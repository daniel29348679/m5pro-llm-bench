#!/usr/bin/env python3
"""Precise per-model token-speed benchmark for Ollama (v2 — adds 16k long-context).

Measures, for each model:
  - load time (cold start of first request after a fresh /api/generate keep_alive=0)
  - prompt eval tokens/s (prompt_eval_count / prompt_eval_duration)
  - generation tokens/s (eval_count / eval_duration)
  - end-to-end tokens/s (eval_count / total_duration)
  - time-to-first-token (TTFT) measured via streaming
  - peak / mean / stdev across N samples for short / long / xlong (16k) prompts

Outputs JSON + Markdown for each model and a comparison Markdown.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any

OLLAMA_URL = "http://localhost:11434"
GENERATE_URL = f"{OLLAMA_URL}/api/generate"

SHORT_PROMPT = (
    "In one paragraph, explain what an HTTP server is and how it handles requests."
)

LONG_PROMPT = (
    "You are a senior staff engineer. Write a detailed technical design document for a "
    "high-throughput, low-latency HTTP request router. Cover: request lifecycle, "
    "connection handling (keep-alive, HTTP/2, HTTP/3), TLS termination strategies, "
    "load-balancing algorithms (round robin, least-connections, EWMA, P2C), health "
    "checking, retry/timeout/budget policies, circuit breaking, observability "
    "(structured logs, metrics, traces), graceful shutdown, zero-downtime deploys, "
    "rolling configuration reloads, backpressure, queue management, and resource "
    "isolation. Provide concrete pseudocode for the main hot path and discuss the "
    "performance trade-offs of each design decision in detail."
)

# A single ~500-token paragraph repeated to build a long-context prompt.
XLONG_PARAGRAPH = (
    "Distributed systems pose a unique combination of correctness, latency, and "
    "operability challenges. Consider a service-mesh sidecar that must terminate TLS, "
    "route requests by header, weight, and locality, perform retries with hedging, "
    "enforce circuit breakers per upstream endpoint, emit OpenTelemetry traces with "
    "B3 propagation, and report Prometheus histograms with exemplars. Each hop adds "
    "queuing latency, head-of-line blocking risk, and a chance for partial failure. "
    "On the data plane the hot path must avoid allocations, prefer zero-copy IO, "
    "use lock-free queues for cross-thread handoffs, and amortize syscalls via "
    "io_uring or kqueue. On the control plane, a robust xDS implementation must "
    "deliver eventual consistency under partition while remaining strongly ordered "
    "for resource updates within a single resource type. Discovery uses incremental "
    "delta xDS to bound bandwidth. Health checking integrates active probes with "
    "passive outlier detection so that endpoints with elevated error rates are "
    "ejected and slowly readmitted. The retry policy must respect budgets, RTO, "
    "and idempotency markers; replays are dangerous on POST without strict "
    "idempotency keys. Observability dashboards should expose RED metrics, USE "
    "metrics, queue depths, GC pauses, file descriptor utilization, and TLS "
    "handshake latency. For deployment, blue/green and canary with progressive "
    "delivery shrink blast radius. Configuration changes ride through atomic "
    "version bumps to prevent torn reads. Memory budgets must account for KV cache "
    "growth in adjacent inference workloads. Security posture demands mTLS by "
    "default, SPIFFE identities, RBAC at L7, signed configuration, and continuous "
    "supply-chain attestation. The entire system must be testable: deterministic "
    "simulators for the control plane, fault injection for the data plane, and "
    "end-to-end soak tests with shaped traffic. The trade-offs between per-request "
    "overhead and feature richness, between strong consistency and availability, "
    "between operability and complexity, are the substance of staff-level design."
)


@dataclass
class Sample:
    prompt_label: str
    ok: bool
    error: str | None = None
    # Wall-clock timings measured by the client
    wall_total_s: float = 0.0
    ttft_s: float = 0.0  # streaming: time to first token from server
    # Server-reported counters (nanoseconds in the API; converted to seconds)
    load_duration_s: float = 0.0
    prompt_eval_count: int = 0
    prompt_eval_duration_s: float = 0.0
    eval_count: int = 0
    eval_duration_s: float = 0.0
    total_duration_s: float = 0.0
    thinking_chars: int = 0
    response_chars: int = 0

    @property
    def gen_tps(self) -> float:
        return self.eval_count / self.eval_duration_s if self.eval_duration_s > 0 else 0.0

    @property
    def prompt_tps(self) -> float:
        return (
            self.prompt_eval_count / self.prompt_eval_duration_s
            if self.prompt_eval_duration_s > 0
            else 0.0
        )

    @property
    def e2e_tps(self) -> float:
        return self.eval_count / self.total_duration_s if self.total_duration_s > 0 else 0.0


@dataclass
class ModelReport:
    model: str
    size_bytes: int
    parameter_count: str
    quantization: str
    architecture: str
    started_at: str
    finished_at: str
    load_first_request_s: float
    samples: list[dict[str, Any]] = field(default_factory=list)


def run(cmd: list[str], timeout: float = 60.0) -> str:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, check=False
    ).stdout


def get_model_info(model: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "size_bytes": 0,
        "parameter_count": "?",
        "quantization": "?",
        "architecture": "?",
    }
    try:
        out = run(["ollama", "show", model], timeout=20)
        for raw in out.splitlines():
            line = raw.strip()
            if line.startswith("architecture"):
                info["architecture"] = line.split(None, 1)[1]
            elif line.startswith("parameters"):
                info["parameter_count"] = line.split(None, 1)[1]
            elif line.startswith("quantization"):
                info["quantization"] = line.split(None, 1)[1]
    except Exception:
        pass
    try:
        out = run(["ollama", "list"], timeout=10)
        for line in out.splitlines():
            if line.startswith(model + " ") or line.startswith(model + "\t"):
                parts = line.split()
                if len(parts) >= 4:
                    size_str = parts[2] + " " + parts[3]
                    info["size_bytes"] = parse_size(size_str)
                break
    except Exception:
        pass
    return info


def parse_size(value: str) -> int:
    parts = value.strip().split()
    if not parts:
        return 0
    try:
        num = float(parts[0])
    except ValueError:
        return 0
    unit = parts[1].upper() if len(parts) > 1 else "B"
    factors = {
        "B": 1,
        "KB": 1_000,
        "MB": 1_000_000,
        "GB": 1_000_000_000,
        "TB": 1_000_000_000_000,
    }
    return int(num * factors.get(unit, 1))


def unload_model(model: str) -> None:
    payload = {"model": model, "prompt": "", "keep_alive": 0, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GENERATE_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
    except Exception:
        pass


def stream_generate(
    model: str,
    prompt: str,
    num_predict: int,
    timeout_s: float,
    num_ctx: int | None = None,
) -> Sample:
    options: dict[str, Any] = {
        "num_predict": num_predict,
        "temperature": 0.0,
        "seed": 42,
    }
    if num_ctx is not None:
        options["num_ctx"] = num_ctx

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": "10m",
        "options": options,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GENERATE_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    sample = Sample(prompt_label="?", ok=False)
    started = time.perf_counter()
    first_token_at: float | None = None
    thinking_chars = 0
    response_chars = 0
    final: dict[str, Any] = {}

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            for raw_line in resp:
                if not raw_line.strip():
                    continue
                try:
                    chunk = json.loads(raw_line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                if first_token_at is None and (
                    chunk.get("response") or chunk.get("thinking")
                ):
                    first_token_at = time.perf_counter()
                thinking_chars += len(chunk.get("thinking") or "")
                response_chars += len(chunk.get("response") or "")
                if chunk.get("done"):
                    final = chunk
                    break
    except Exception as exc:  # noqa: BLE001
        sample.error = f"{type(exc).__name__}: {exc}"
        sample.wall_total_s = time.perf_counter() - started
        return sample

    sample.wall_total_s = time.perf_counter() - started
    sample.ttft_s = (first_token_at - started) if first_token_at else 0.0
    sample.ok = True
    sample.load_duration_s = float(final.get("load_duration") or 0) / 1e9
    sample.prompt_eval_count = int(final.get("prompt_eval_count") or 0)
    sample.prompt_eval_duration_s = float(final.get("prompt_eval_duration") or 0) / 1e9
    sample.eval_count = int(final.get("eval_count") or 0)
    sample.eval_duration_s = float(final.get("eval_duration") or 0) / 1e9
    sample.total_duration_s = float(final.get("total_duration") or 0) / 1e9
    sample.thinking_chars = thinking_chars
    sample.response_chars = response_chars
    return sample


def stat(values: list[float]) -> dict[str, float]:
    values = [v for v in values if v > 0]
    if not values:
        return {"mean": 0, "median": 0, "stdev": 0, "min": 0, "max": 0, "n": 0}
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "n": len(values),
    }


def make_xlong_prompt(repeats: int) -> str:
    lead = (
        "You are a senior distributed-systems architect. Read the following extensive "
        "context (a corpus of design notes) carefully, then produce a detailed "
        "synthesis at the end. Context corpus follows.\n\n"
    )
    body = "\n\n---\n\n".join(
        f"Section {i + 1}.\n{XLONG_PARAGRAPH}" for i in range(repeats)
    )
    tail = (
        "\n\n---\n\nEnd of corpus. Now write a deep synthesis covering the major "
        "themes, conflicts between approaches, and concrete recommendations."
    )
    return lead + body + tail


def benchmark_model(
    model: str,
    short_runs: int,
    long_runs: int,
    xlong_runs: int,
    short_predict: int,
    long_predict: int,
    xlong_predict: int,
    xlong_repeats: int,
    xlong_num_ctx: int,
    timeout_s: float,
) -> ModelReport:
    info = get_model_info(model)
    print(f"\n=== {model} ===", flush=True)
    print(
        f"  arch={info['architecture']} params={info['parameter_count']} "
        f"quant={info['quantization']} size={info['size_bytes'] / 1e9:.2f} GB",
        flush=True,
    )

    print("  unloading any previous model...", flush=True)
    unload_model(model)
    time.sleep(2.0)

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print("  cold-start request (loading model into memory)...", flush=True)
    cold = stream_generate(model, "Hello.", num_predict=8, timeout_s=timeout_s)
    if not cold.ok:
        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        return ModelReport(
            model=model,
            size_bytes=info["size_bytes"],
            parameter_count=info["parameter_count"],
            quantization=info["quantization"],
            architecture=info["architecture"],
            started_at=started_at,
            finished_at=finished_at,
            load_first_request_s=cold.wall_total_s,
            samples=[asdict(cold) | {"_kind": "cold"}],
        )
    load_first_s = cold.load_duration_s if cold.load_duration_s > 0 else cold.wall_total_s
    print(
        f"    load_duration={cold.load_duration_s:.2f}s wall={cold.wall_total_s:.2f}s",
        flush=True,
    )

    print("  warmup...", flush=True)
    stream_generate(model, SHORT_PROMPT, num_predict=64, timeout_s=timeout_s)

    samples: list[Sample] = []

    print(f"  short prompt × {short_runs} (num_predict={short_predict})...", flush=True)
    for i in range(short_runs):
        s = stream_generate(
            model, SHORT_PROMPT, num_predict=short_predict, timeout_s=timeout_s
        )
        s.prompt_label = "short"
        samples.append(s)
        if s.ok:
            print(
                f"    [short {i + 1}/{short_runs}] gen={s.gen_tps:6.2f} tok/s "
                f"prompt_eval={s.prompt_tps:7.2f} tok/s ttft={s.ttft_s * 1000:6.0f}ms "
                f"eval_n={s.eval_count} prompt_n={s.prompt_eval_count} "
                f"think={s.thinking_chars} resp={s.response_chars}",
                flush=True,
            )
        else:
            print(f"    [short {i + 1}/{short_runs}] ERROR {s.error}", flush=True)

    print(f"  long prompt × {long_runs} (num_predict={long_predict})...", flush=True)
    for i in range(long_runs):
        s = stream_generate(
            model, LONG_PROMPT, num_predict=long_predict, timeout_s=timeout_s
        )
        s.prompt_label = "long"
        samples.append(s)
        if s.ok:
            print(
                f"    [long {i + 1}/{long_runs}] gen={s.gen_tps:6.2f} tok/s "
                f"prompt_eval={s.prompt_tps:7.2f} tok/s ttft={s.ttft_s * 1000:6.0f}ms "
                f"eval_n={s.eval_count} prompt_n={s.prompt_eval_count} "
                f"think={s.thinking_chars} resp={s.response_chars}",
                flush=True,
            )
        else:
            print(f"    [long {i + 1}/{long_runs}] ERROR {s.error}", flush=True)

    if xlong_runs > 0:
        xlong_prompt = make_xlong_prompt(xlong_repeats)
        approx_words = len(xlong_prompt.split())
        print(
            f"  xlong prompt × {xlong_runs} (num_ctx={xlong_num_ctx} "
            f"num_predict={xlong_predict} ~{approx_words} words)...",
            flush=True,
        )
        for i in range(xlong_runs):
            s = stream_generate(
                model,
                xlong_prompt,
                num_predict=xlong_predict,
                timeout_s=timeout_s,
                num_ctx=xlong_num_ctx,
            )
            s.prompt_label = "xlong"
            samples.append(s)
            if s.ok:
                print(
                    f"    [xlong {i + 1}/{xlong_runs}] gen={s.gen_tps:6.2f} tok/s "
                    f"prompt_eval={s.prompt_tps:7.2f} tok/s ttft={s.ttft_s:6.2f}s "
                    f"eval_n={s.eval_count} prompt_n={s.prompt_eval_count} "
                    f"wall={s.wall_total_s:6.1f}s",
                    flush=True,
                )
            else:
                print(f"    [xlong {i + 1}/{xlong_runs}] ERROR {s.error}", flush=True)

    finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    return ModelReport(
        model=model,
        size_bytes=info["size_bytes"],
        parameter_count=info["parameter_count"],
        quantization=info["quantization"],
        architecture=info["architecture"],
        started_at=started_at,
        finished_at=finished_at,
        load_first_request_s=load_first_s,
        samples=[asdict(s) for s in samples],
    )


def _samples_of(report: ModelReport, label: str) -> list[Sample]:
    out: list[Sample] = []
    for s in report.samples:
        if s.get("prompt_label") != label or not s.get("ok"):
            continue
        out.append(Sample(**{k: v for k, v in s.items() if k != "_kind"}))
    return out


def render_model_md(report: ModelReport, output_path: Path) -> None:
    short = _samples_of(report, "short")
    long_ = _samples_of(report, "long")
    xlong = _samples_of(report, "xlong")

    short_gen = stat([s.gen_tps for s in short])
    long_gen = stat([s.gen_tps for s in long_])
    xlong_gen = stat([s.gen_tps for s in xlong])
    short_prompt = stat([s.prompt_tps for s in short])
    long_prompt = stat([s.prompt_tps for s in long_])
    xlong_prompt = stat([s.prompt_tps for s in xlong])
    short_e2e = stat([s.e2e_tps for s in short])
    long_e2e = stat([s.e2e_tps for s in long_])
    xlong_e2e = stat([s.e2e_tps for s in xlong])
    short_ttft = stat([s.ttft_s for s in short])
    long_ttft = stat([s.ttft_s for s in long_])
    xlong_ttft = stat([s.ttft_s for s in xlong])

    xlong_prompt_n_avg = (
        statistics.mean([s.prompt_eval_count for s in xlong]) if xlong else 0
    )

    lines: list[str] = []
    lines.append(f"# Ollama 速度報告 — `{report.model}`")
    lines.append("")
    lines.append(f"- 開始: `{report.started_at}`")
    lines.append(f"- 結束: `{report.finished_at}`")
    lines.append(f"- 架構: `{report.architecture}`")
    lines.append(f"- 參數量: `{report.parameter_count}`")
    lines.append(f"- 量化格式: `{report.quantization}`")
    lines.append(f"- 模型檔大小: `{report.size_bytes / 1e9:.2f} GB`")
    lines.append(f"- 第一次冷啟動載入時間: `{report.load_first_request_s:.2f} s`")
    lines.append("")
    lines.append("## 量測說明")
    lines.append("")
    lines.append("- 透過 Ollama `/api/generate` 串流 API 量測；以伺服器回報的 `eval_count / eval_duration` 計算純生成 tokens/s。")
    lines.append("- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`，反映 prefill 速度。")
    lines.append("- `e2e tokens/s` = `eval_count / total_duration`，含 prompt prefill。")
    lines.append("- TTFT 為串流首個 token 抵達 client 的 wall-clock 時間。")
    lines.append("- 全部測試使用 `temperature=0`、`seed=42`，`keep_alive=10m`，先 warmup 再取樣。")
    lines.append("- xlong 測試強制 `num_ctx=16384`，使用約 14k tokens 的 prompt 量測長上下文 prefill 與生成速度。")
    lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append("| 指標 | short prompt | long prompt | xlong prompt (16k) |")
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| 生成 tokens/s（mean ± stdev） | "
        f"{short_gen['mean']:.2f} ± {short_gen['stdev']:.2f} | "
        f"{long_gen['mean']:.2f} ± {long_gen['stdev']:.2f} | "
        f"{xlong_gen['mean']:.2f} ± {xlong_gen['stdev']:.2f} |"
    )
    lines.append(
        f"| 生成 tokens/s（median / max） | "
        f"{short_gen['median']:.2f} / {short_gen['max']:.2f} | "
        f"{long_gen['median']:.2f} / {long_gen['max']:.2f} | "
        f"{xlong_gen['median']:.2f} / {xlong_gen['max']:.2f} |"
    )
    lines.append(
        f"| prompt eval tokens/s（mean） | "
        f"{short_prompt['mean']:.2f} | "
        f"{long_prompt['mean']:.2f} | "
        f"{xlong_prompt['mean']:.2f} |"
    )
    lines.append(
        f"| e2e tokens/s（mean） | "
        f"{short_e2e['mean']:.2f} | "
        f"{long_e2e['mean']:.2f} | "
        f"{xlong_e2e['mean']:.2f} |"
    )
    lines.append(
        f"| TTFT 秒（mean） | "
        f"{short_ttft['mean']:.3f} | "
        f"{long_ttft['mean']:.3f} | "
        f"{xlong_ttft['mean']:.3f} |"
    )
    lines.append(
        f"| 樣本數 (n) | {short_gen['n']} | {long_gen['n']} | {xlong_gen['n']} |"
    )
    if xlong:
        lines.append(
            f"| 平均 prompt_eval_count | - | - | {xlong_prompt_n_avg:.0f} tokens |"
        )
    lines.append("")

    lines.append("## 每次取樣明細")
    lines.append("")
    lines.append(
        "| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | "
        "prompt_n | eval_n | think chars | resp chars | wall (s) |"
    )
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i, s in enumerate(report.samples, 1):
        if not s.get("ok"):
            lines.append(
                f"| {i} | {s.get('prompt_label')} | ❌ {s.get('error')} | - | - | - | - | - | - | - | - | "
                f"{s.get('wall_total_s', 0):.2f} |"
            )
            continue
        sm = Sample(**{k: v for k, v in s.items() if k != "_kind"})
        lines.append(
            f"| {i} | {sm.prompt_label} | ✅ | {sm.gen_tps:.2f} | {sm.prompt_tps:.2f} | "
            f"{sm.e2e_tps:.2f} | {sm.ttft_s:.3f} | {sm.prompt_eval_count} | "
            f"{sm.eval_count} | {sm.thinking_chars} | {sm.response_chars} | "
            f"{sm.wall_total_s:.2f} |"
        )
    lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_comparison_md(reports: list[ModelReport], output_path: Path, host: str) -> None:
    rows: list[dict[str, Any]] = []
    for r in reports:
        short = _samples_of(r, "short")
        long_ = _samples_of(r, "long")
        xlong = _samples_of(r, "xlong")

        def _mean(xs: list[float]) -> float:
            return statistics.mean(xs) if xs else 0.0

        rows.append(
            {
                "model": r.model,
                "params": r.parameter_count,
                "quant": r.quantization,
                "size_gb": r.size_bytes / 1e9,
                "load_s": r.load_first_request_s,
                "short_gen": _mean([s.gen_tps for s in short]),
                "long_gen": _mean([s.gen_tps for s in long_]),
                "xlong_gen": _mean([s.gen_tps for s in xlong]),
                "short_prompt": _mean([s.prompt_tps for s in short]),
                "long_prompt": _mean([s.prompt_tps for s in long_]),
                "xlong_prompt": _mean([s.prompt_tps for s in xlong]),
                "short_ttft": _mean([s.ttft_s for s in short]),
                "long_ttft": _mean([s.ttft_s for s in long_]),
                "xlong_ttft": _mean([s.ttft_s for s in xlong]),
                "xlong_prompt_n": _mean([s.prompt_eval_count for s in xlong]),
            }
        )

    rows_by_short_gen = sorted(rows, key=lambda r: r["short_gen"], reverse=True)
    rows_by_long_gen = sorted(rows, key=lambda r: r["long_gen"], reverse=True)
    rows_by_xlong_gen = sorted(rows, key=lambda r: r["xlong_gen"], reverse=True)

    lines: list[str] = []
    lines.append("# Qwen3.6 系列 Ollama 速度綜合對比 (run2 — 高效能模式 + 16k 上下文)")
    lines.append("")
    lines.append(
        f"- 報告產生時間: `{datetime.now().astimezone().isoformat(timespec='seconds')}`"
    )
    lines.append(f"- 主機: {host}")
    lines.append(f"- Python: `{sys.version.split()[0]}`")
    lines.append(f"- Ollama URL: `{OLLAMA_URL}`")
    lines.append("- 系統電源模式: `pmset powermode=2`（High Power, AC 供電）")
    lines.append("- 防睡眠: `caffeinate -dimsu` 全程啟用")
    lines.append("- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`")
    lines.append("- short/long 採用預設 num_ctx；xlong 強制 `num_ctx=16384`")
    lines.append("")
    lines.append("## 主表 — 三段 prompt 的生成 / prompt eval / TTFT")
    lines.append("")
    lines.append(
        "| 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | "
        "short gen | long gen | xlong gen | "
        "short prompt | long prompt | xlong prompt | "
        "short TTFT | long TTFT | xlong TTFT |"
    )
    lines.append(
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in rows:
        lines.append(
            f"| `{r['model']}` | {r['params']} | {r['quant']} | "
            f"{r['size_gb']:.2f} | {r['load_s']:.2f} | "
            f"{r['short_gen']:.2f} | {r['long_gen']:.2f} | {r['xlong_gen']:.2f} | "
            f"{r['short_prompt']:.2f} | {r['long_prompt']:.2f} | {r['xlong_prompt']:.2f} | "
            f"{r['short_ttft']:.3f} | {r['long_ttft']:.3f} | {r['xlong_ttft']:.2f} |"
        )
    lines.append("")
    lines.append("> 所有數值單位：`gen` / `prompt` 為 tokens/s（越大越快）；`TTFT` 為秒（越小越好）。")
    lines.append("")

    lines.append("## 排名")
    lines.append("")
    lines.append("### short prompt 生成速度")
    lines.append("")
    lines.append("| 排名 | 模型 | short gen tok/s |")
    lines.append("|---:|---|---:|")
    for i, r in enumerate(rows_by_short_gen, 1):
        lines.append(f"| {i} | `{r['model']}` | {r['short_gen']:.2f} |")
    lines.append("")

    lines.append("### long prompt 生成速度")
    lines.append("")
    lines.append("| 排名 | 模型 | long gen tok/s |")
    lines.append("|---:|---|---:|")
    for i, r in enumerate(rows_by_long_gen, 1):
        lines.append(f"| {i} | `{r['model']}` | {r['long_gen']:.2f} |")
    lines.append("")

    lines.append("### xlong (16k) 生成速度")
    lines.append("")
    lines.append("| 排名 | 模型 | xlong gen tok/s | 平均 prompt tokens |")
    lines.append("|---:|---|---:|---:|")
    for i, r in enumerate(rows_by_xlong_gen, 1):
        lines.append(
            f"| {i} | `{r['model']}` | {r['xlong_gen']:.2f} | "
            f"{r['xlong_prompt_n']:.0f} |"
        )
    lines.append("")

    lines.append("## 指標說明")
    lines.append("")
    lines.append("- **gen tok/s**：純生成 tokens/s（伺服器回報的 `eval_count / eval_duration`）。")
    lines.append("- **prompt tok/s**：prefill 速度，反映模型一次吞下整段 prompt 的能力。")
    lines.append("- **TTFT**：client 收到第一個 token 的 wall-clock 秒數，可視為使用者「按下送出後等多久」。")
    lines.append("- **冷啟**：模型剛載入記憶體後第一次 forward 的時間（伺服器 `load_duration` 或 wall）。")
    lines.append("- **xlong**：以一段 ~14k tokens 的合成語料 + `num_ctx=16384` 量測長上下文 prefill 與生成速度。")
    lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def detect_host() -> str:
    chip = "?"
    mem = "?"
    try:
        out = run(["system_profiler", "SPHardwareDataType"], timeout=10)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Chip:"):
                chip = line.split(":", 1)[1].strip()
            elif line.startswith("Memory:"):
                mem = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return f"{platform.system()} {platform.release()} / {chip} / {mem}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--short-runs", type=int, default=5)
    parser.add_argument("--long-runs", type=int, default=4)
    parser.add_argument("--xlong-runs", type=int, default=3)
    parser.add_argument("--short-predict", type=int, default=256)
    parser.add_argument("--long-predict", type=int, default=512)
    parser.add_argument("--xlong-predict", type=int, default=256)
    parser.add_argument("--xlong-repeats", type=int, default=28,
                        help="number of times the ~500-token paragraph is repeated to build the xlong prompt")
    parser.add_argument("--xlong-num-ctx", type=int, default=16384)
    parser.add_argument("--timeout", type=float, default=2400.0)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    host = detect_host()
    print(f"Output dir: {out_dir}")
    print(f"Host: {host}")
    print(f"Models: {args.models}")
    print(
        f"short_runs={args.short_runs} long_runs={args.long_runs} "
        f"xlong_runs={args.xlong_runs} "
        f"short_predict={args.short_predict} long_predict={args.long_predict} "
        f"xlong_predict={args.xlong_predict} xlong_num_ctx={args.xlong_num_ctx}"
    )

    reports: list[ModelReport] = []
    for model in args.models:
        try:
            report = benchmark_model(
                model,
                args.short_runs,
                args.long_runs,
                args.xlong_runs,
                args.short_predict,
                args.long_predict,
                args.xlong_predict,
                args.xlong_repeats,
                args.xlong_num_ctx,
                args.timeout,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  FATAL benchmarking {model}: {exc}", flush=True)
            continue
        reports.append(report)
        safe = model.replace("/", "_").replace(":", "_")
        json_path = out_dir / f"{safe}.json"
        md_path = out_dir / f"{safe}.md"
        json_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        render_model_md(report, md_path)
        print(f"  → wrote {md_path.name} & {json_path.name}", flush=True)
        # Free memory before loading the next model.
        unload_model(model)

    if reports:
        render_comparison_md(reports, out_dir / "00_comparison.md", host)
        print(f"\nWrote comparison: {out_dir / '00_comparison.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
