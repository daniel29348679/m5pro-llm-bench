#!/usr/bin/env python3
"""Run the canonical M5 Pro benchmark suite against an oMLX server."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from bench import LONG_PROMPT, SHORT_PROMPT, detect_host, make_xlong_prompt, stat


@dataclass
class Sample:
    prompt_label: str
    ok: bool
    error: str | None = None
    finish_reason: str | None = None
    wall_total_s: float = 0.0
    ttft_s: float = 0.0
    server_ttft_s: float = 0.0
    load_duration_s: float = 0.0
    prompt_eval_count: int = 0
    cached_prompt_tokens: int = 0
    prompt_eval_duration_s: float = 0.0
    eval_count: int = 0
    eval_duration_s: float = 0.0
    total_duration_s: float = 0.0
    server_prompt_tps: float = 0.0
    server_gen_tps: float = 0.0
    thinking_chars: int = 0
    response_chars: int = 0
    mtp: dict[str, Any] | None = None

    @property
    def gen_tps(self) -> float:
        if self.server_gen_tps > 0:
            return self.server_gen_tps
        return self.eval_count / self.eval_duration_s if self.eval_duration_s > 0 else 0.0

    @property
    def prompt_tps(self) -> float:
        if self.server_prompt_tps > 0:
            return self.server_prompt_tps
        return (
            self.prompt_eval_count / self.prompt_eval_duration_s
            if self.prompt_eval_duration_s > 0
            else 0.0
        )

    @property
    def e2e_tps(self) -> float:
        return self.eval_count / self.total_duration_s if self.total_duration_s > 0 else 0.0


@dataclass
class Report:
    runtime: str
    runtime_version: str
    api_url: str
    model: str
    display_name: str
    model_path: str
    size_bytes: int
    parameter_count: str
    quantization: str
    architecture: str
    model_context_length: int
    started_at: str
    finished_at: str
    load_first_request_s: float
    host: str
    power_mode: str
    settings: dict[str, Any]
    protocol: dict[str, Any]
    mtp: dict[str, Any]
    samples: list[dict[str, Any]] = field(default_factory=list)


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def stream_generate(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
) -> Sample:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "seed": 42,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    sample = Sample(prompt_label="?", ok=False)
    started = time.perf_counter()
    first_token_at: float | None = None
    usage: dict[str, Any] = {}

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                chunk = json.loads(body)
                if chunk.get("error"):
                    raise RuntimeError(str(chunk["error"]))
                if chunk.get("usage"):
                    usage = chunk["usage"]
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                choice = choices[0]
                if choice.get("finish_reason") is not None:
                    sample.finish_reason = str(choice["finish_reason"])
                delta = choice.get("delta") or {}
                reasoning = delta.get("reasoning_content") or ""
                content = delta.get("content") or ""
                if first_token_at is None and (reasoning or content):
                    first_token_at = time.perf_counter()
                sample.thinking_chars += len(reasoning)
                sample.response_chars += len(content)
    except Exception as exc:  # noqa: BLE001 - preserve benchmark failures.
        sample.error = f"{type(exc).__name__}: {exc}"
        sample.wall_total_s = time.perf_counter() - started
        return sample

    sample.wall_total_s = time.perf_counter() - started
    sample.ttft_s = (
        first_token_at - started if first_token_at is not None else sample.wall_total_s
    )
    if not usage:
        sample.error = "stream ended without usage metrics"
        return sample

    details = usage.get("prompt_tokens_details") or {}
    sample.ok = True
    sample.server_ttft_s = float(usage.get("time_to_first_token") or 0.0)
    sample.load_duration_s = float(usage.get("model_load_duration") or 0.0)
    sample.prompt_eval_count = int(usage.get("prompt_tokens") or 0)
    sample.cached_prompt_tokens = int(details.get("cached_tokens") or 0)
    sample.prompt_eval_duration_s = float(usage.get("prompt_eval_duration") or 0.0)
    sample.eval_count = int(usage.get("completion_tokens") or 0)
    sample.eval_duration_s = float(usage.get("generation_duration") or 0.0)
    sample.total_duration_s = float(usage.get("total_time") or sample.wall_total_s)
    sample.server_prompt_tps = float(usage.get("prompt_tokens_per_second") or 0.0)
    sample.server_gen_tps = float(usage.get("generation_tokens_per_second") or 0.0)
    return sample


def get_runtime_version() -> str:
    result = subprocess.run(
        ["omlx", "--version"], capture_output=True, text=True, check=False
    )
    match = re.search(r"(\d+\.\d+\.\d+)", result.stdout + result.stderr)
    return match.group(1) if match else "unknown"


def get_power_mode() -> str:
    result = subprocess.run(
        ["pmset", "-g", "custom"], capture_output=True, text=True, check=False
    )
    section = ""
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.endswith("Power:"):
            section = line[:-1]
        elif section == "AC Power" and line.startswith("powermode"):
            return line.split()[-1]
    return "unknown"


def get_model_info(base_url: str, model: str) -> dict[str, Any]:
    models = request_json(base_url, "/admin/api/models").get("models", [])
    entry = next((item for item in models if item.get("id") == model), None)
    if entry is None:
        raise RuntimeError(f"oMLX model not found: {model}")
    return entry


def get_safe_settings(base_url: str, model_info: dict[str, Any]) -> dict[str, Any]:
    global_settings = request_json(base_url, "/admin/api/global-settings")
    model_settings = model_info.get("settings") or {}
    return {
        "listen_host": global_settings.get("server", {}).get("host"),
        "listen_port": global_settings.get("server", {}).get("port"),
        "default_context_window": global_settings.get("sampling", {}).get(
            "max_context_window"
        ),
        "max_concurrent_requests": global_settings.get("scheduler", {}).get(
            "max_concurrent_requests"
        ),
        "memory_guard_tier": global_settings.get("memory", {}).get(
            "memory_guard_tier"
        ),
        "cache_enabled": global_settings.get("cache", {}).get("enabled"),
        "decode_fairness": global_settings.get("scheduler", {}).get(
            "decode_fairness"
        ),
        "model_max_context_window": model_settings.get("max_context_window"),
        "vlm_mtp_enabled": model_settings.get("vlm_mtp_enabled"),
        "vlm_mtp_draft_model": model_settings.get("vlm_mtp_draft_model"),
        "vlm_mtp_draft_block_size": model_settings.get("vlm_mtp_draft_block_size"),
    }


def update_model_context(base_url: str, model: str, value: int | None) -> None:
    model_path = urllib.parse.quote(model, safe="")
    request_json(
        base_url,
        f"/admin/api/models/{model_path}/settings",
        method="PUT",
        payload={"max_context_window": value},
    )


def unload_model(base_url: str, model: str) -> None:
    model_path = urllib.parse.quote(model, safe="")
    request_json(
        base_url,
        f"/admin/api/models/{model_path}/unload",
        method="POST",
        payload={},
    )


MTP_PATTERN = re.compile(
    r"vlm_mtp stats: request=(?P<request>\S+) finish=(?P<finish>\S+) "
    r"rounds=(?P<rounds>\d+) accepted=(?P<accepted>\d+)/(?P<drafted>\d+) "
    r"\((?P<acceptance>[\d.]+)%\) tokens_per_round=(?P<tokens_per_round>[\d.]+) "
    r"emitted=(?P<emitted>\d+) block_size=(?P<block_size>\d+)"
)


def read_mtp_stats(log_path: Path, offset: int) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    if log_path.stat().st_size < offset:
        offset = 0
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        text = handle.read()
    stats: list[dict[str, Any]] = []
    for match in MTP_PATTERN.finditer(text):
        values = match.groupdict()
        stats.append(
            {
                "request_id": values["request"],
                "finish": values["finish"],
                "rounds": int(values["rounds"]),
                "accepted_tokens": int(values["accepted"]),
                "drafted_tokens": int(values["drafted"]),
                "acceptance_percent": float(values["acceptance"]),
                "tokens_per_round": float(values["tokens_per_round"]),
                "emitted_tokens": int(values["emitted"]),
                "block_size": int(values["block_size"]),
            }
        )
    return stats


def samples_of(report: Report, label: str) -> list[Sample]:
    return [
        Sample(**sample)
        for sample in report.samples
        if sample.get("ok") and sample.get("prompt_label") == label
    ]


def render_model_report(report: Report, output_path: Path) -> None:
    groups = {name: samples_of(report, name) for name in ("short", "long", "xlong")}

    def group_stats(name: str, attr: str) -> dict[str, float]:
        return stat([getattr(sample, attr) for sample in groups[name]])

    gen = {name: group_stats(name, "gen_tps") for name in groups}
    prompt = {name: group_stats(name, "prompt_tps") for name in groups}
    e2e = {name: group_stats(name, "e2e_tps") for name in groups}
    ttft = {name: group_stats(name, "ttft_s") for name in groups}
    xlong_prompt_mean = statistics.mean(
        [sample.prompt_eval_count for sample in groups["xlong"]]
    )

    mtp = report.mtp
    lines = [
        f"# oMLX Speed Report — `{report.display_name}`",
        "",
        f"- Started: `{report.started_at}`",
        f"- Finished: `{report.finished_at}`",
        f"- Runtime: `oMLX {report.runtime_version}`",
        f"- Architecture / parameters: `{report.architecture}` / `{report.parameter_count}`",
        f"- Quantization: `{report.quantization}`",
        f"- Target model size: `{report.size_bytes / 1e9:.2f} GB`",
        f"- Model context length: `{report.model_context_length}`",
        f"- First cold-start load time: `{report.load_first_request_s:.2f} s`",
        f"- MTP drafter: `{mtp.get('draft_model')}` (`{mtp.get('draft_size_bytes', 0) / 1e6:.1f} MB`, block size `{mtp.get('block_size')}`)",
        "",
        "## Methodology",
        "",
        "- This run reuses the repository's canonical short, long, and xlong prompts without modification.",
        "- Measurements use oMLX's streaming OpenAI-compatible `/v1/chat/completions` endpoint with `stream_options.include_usage=true`.",
        "- Decode and prefill throughput use oMLX's server-reported `generation_tokens_per_second` and `prompt_tokens_per_second` fields; TTFT is also retained from the client clock.",
        "- Every sample uses `temperature=0` and `seed=42`, with a cold load and warmup before the measured samples.",
        "- The protocol matches the existing suite: short 5 x 256-token limits, long 4 x 512-token limits, and xlong 3 x 256-token limits. The xlong phase temporarily sets the model context cap to 16384 and restores it afterward.",
        "- Repeated xlong prompts can hit oMLX's block prefix cache. Cached-token counts are preserved per sample; use the first uncached sample for cold-prefill analysis.",
        "- The target checkpoint does not contain embedded `mtp.*` tensors. Speculative decoding uses the separately installed Qwen3.8 MTP drafter shown above.",
        "",
        "## Summary",
        "",
        "| Metric | short prompt | long prompt | xlong prompt (16k) |",
        "|---|---:|---:|---:|",
        f"| Decode tokens/s (mean ± stdev) | {gen['short']['mean']:.2f} ± {gen['short']['stdev']:.2f} | {gen['long']['mean']:.2f} ± {gen['long']['stdev']:.2f} | {gen['xlong']['mean']:.2f} ± {gen['xlong']['stdev']:.2f} |",
        f"| Decode tokens/s (median / max) | {gen['short']['median']:.2f} / {gen['short']['max']:.2f} | {gen['long']['median']:.2f} / {gen['long']['max']:.2f} | {gen['xlong']['median']:.2f} / {gen['xlong']['max']:.2f} |",
        f"| Prompt evaluation tokens/s (mean) | {prompt['short']['mean']:.2f} | {prompt['long']['mean']:.2f} | {prompt['xlong']['mean']:.2f} |",
        f"| End-to-end tokens/s (mean) | {e2e['short']['mean']:.2f} | {e2e['long']['mean']:.2f} | {e2e['xlong']['mean']:.2f} |",
        f"| Client TTFT seconds (mean) | {ttft['short']['mean']:.3f} | {ttft['long']['mean']:.3f} | {ttft['xlong']['mean']:.3f} |",
        f"| Samples (n) | {gen['short']['n']} | {gen['long']['n']} | {gen['xlong']['n']} |",
        f"| Mean prompt tokens | - | - | {xlong_prompt_mean:.0f} tokens |",
        "",
        "## MTP Results",
        "",
        f"- Formal samples with MTP logs: `{mtp.get('sample_count', 0)} / {len(report.samples)}`",
        f"- Draft tokens accepted: `{mtp.get('accepted_tokens', 0)} / {mtp.get('drafted_tokens', 0)}` (`{mtp.get('acceptance_percent', 0):.1f}%`)",
        f"- Total decode rounds: `{mtp.get('rounds', 0)}`; emitted tokens: `{mtp.get('emitted_tokens', 0)}`",
        "",
        "## Per-Sample Results",
        "",
        "| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | client TTFT | prompt_n | cached_n | eval_n | MTP accepted | finish | wall |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for index, raw in enumerate(report.samples, 1):
        sample = Sample(**raw)
        if not sample.ok:
            lines.append(
                f"| {index} | {sample.prompt_label} | FAIL | - | - | - | - | - | - | - | - | `{sample.error}` | {sample.wall_total_s:.2f}s |"
            )
            continue
        mtp_cell = "-"
        if sample.mtp:
            mtp_cell = (
                f"{sample.mtp['accepted_tokens']}/{sample.mtp['drafted_tokens']} "
                f"({sample.mtp['acceptance_percent']:.1f}%)"
            )
        lines.append(
            f"| {index} | {sample.prompt_label} | PASS | {sample.gen_tps:.2f} | "
            f"{sample.prompt_tps:.2f} | {sample.e2e_tps:.2f} | {sample.ttft_s:.3f}s | "
            f"{sample.prompt_eval_count} | {sample.cached_prompt_tokens} | "
            f"{sample.eval_count} | {mtp_cell} | {sample.finish_reason} | "
            f"{sample.wall_total_s:.2f}s |"
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def render_comparison(report: Report, output_path: Path) -> None:
    short = stat([sample.gen_tps for sample in samples_of(report, "short")])
    long_ = stat([sample.gen_tps for sample in samples_of(report, "long")])
    xlong = stat([sample.gen_tps for sample in samples_of(report, "xlong")])
    overall = statistics.mean([short["mean"], long_["mean"], xlong["mean"]])
    lines = [
        "# oMLX 0.6.0 Qwen3.8 Benchmark",
        "",
        f"- Report generated: `{report.finished_at}`",
        f"- Host: {report.host}",
        f"- Runtime / API: `oMLX {report.runtime_version}` / `{report.api_url}`",
        f"- Power mode: `{report.power_mode}` (2 = High Power on AC)",
        "- Sleep prevention: `caffeinate -dimsu` enabled for the full formal run",
        "- Protocol: canonical 5/4/3 samples with 256/512/256 output-token limits",
        "",
        "## Primary Result",
        "",
        "| Model | MTP | Short | Long | 11k context | Overall average |",
        "|---|---|---:|---:|---:|---:|",
        f"| `{report.display_name}` | external drafter, block {report.mtp.get('block_size')} | {short['mean']:.2f} | {long_['mean']:.2f} | {xlong['mean']:.2f} | {overall:.2f} |",
        "",
        "> Decode throughput uses oMLX's server-reported streaming usage metrics. The prompts, output limits, sample counts, power mode, and xlong context cap match the repository's established suite; runtime instrumentation and quantization still differ from Ollama rows.",
        "",
        "## Evidence",
        "",
        f"- Successful samples: `{sum(1 for sample in report.samples if sample.get('ok'))} / {len(report.samples)}`",
        f"- MTP acceptance: `{report.mtp.get('accepted_tokens', 0)} / {report.mtp.get('drafted_tokens', 0)}` (`{report.mtp.get('acceptance_percent', 0):.1f}%`)",
        f"- Cold load: `{report.load_first_request_s:.2f} s`",
        "- [Full per-sample report](./qwen3.8_27b-4bit_mtp.md)",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen3.8-27B-4bit")
    parser.add_argument("--parameters", default="27.8B")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-prefix", default="qwen3.8_27b-4bit_mtp")
    parser.add_argument("--short-runs", type=int, default=5)
    parser.add_argument("--long-runs", type=int, default=4)
    parser.add_argument("--xlong-runs", type=int, default=3)
    parser.add_argument("--short-predict", type=int, default=256)
    parser.add_argument("--long-predict", type=int, default=512)
    parser.add_argument("--xlong-predict", type=int, default=256)
    parser.add_argument("--xlong-repeats", type=int, default=28)
    parser.add_argument("--xlong-num-ctx", type=int, default=16384)
    parser.add_argument("--timeout", type=float, default=2400.0)
    args = parser.parse_args()

    health = request_json(args.api_url, "/health")
    if health.get("status") != "healthy":
        raise RuntimeError(f"oMLX is not healthy: {health}")

    model_info = get_model_info(args.api_url, args.model)
    settings = get_safe_settings(args.api_url, model_info)
    original_context = (model_info.get("settings") or {}).get("max_context_window")
    model_path = Path(model_info["model_path"])
    config = json.loads((model_path / "config.json").read_text(encoding="utf-8"))
    quant = config.get("quantization_config") or config.get("quantization") or {}
    quant_name = f"{quant.get('bits', '?')}-bit {quant.get('mode', '?')}"

    draft_id = settings.get("vlm_mtp_draft_model")
    draft_info = get_model_info(args.api_url, draft_id) if draft_id else {}
    log_path = Path.home() / ".omlx" / "logs" / "server.log"

    print(f"Host: {detect_host()}", flush=True)
    print(f"Runtime: oMLX {get_runtime_version()} at {args.api_url}", flush=True)
    print(f"Model: {model_info['display_name']}", flush=True)
    print(
        f"Protocol: short {args.short_runs}x{args.short_predict}, "
        f"long {args.long_runs}x{args.long_predict}, "
        f"xlong {args.xlong_runs}x{args.xlong_predict}",
        flush=True,
    )

    unload_model(args.api_url, args.model)
    time.sleep(2.0)
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    cold = stream_generate(args.api_url, args.model, "Hello.", 8, args.timeout)
    if not cold.ok:
        raise RuntimeError(f"cold-load request failed: {cold.error}")
    load_first_s = cold.load_duration_s or cold.wall_total_s
    print(f"Cold load: {load_first_s:.2f}s", flush=True)

    warmup = stream_generate(args.api_url, args.model, SHORT_PROMPT, 64, args.timeout)
    if not warmup.ok:
        raise RuntimeError(f"warmup failed: {warmup.error}")
    log_offset = log_path.stat().st_size if log_path.exists() else 0

    samples: list[Sample] = []
    cases = (
        ("short", SHORT_PROMPT, args.short_runs, args.short_predict),
        ("long", LONG_PROMPT, args.long_runs, args.long_predict),
    )
    for label, prompt, runs, max_tokens in cases:
        print(f"{label}: {runs} samples x {max_tokens} tokens", flush=True)
        for index in range(runs):
            sample = stream_generate(
                args.api_url, args.model, prompt, max_tokens, args.timeout
            )
            sample.prompt_label = label
            samples.append(sample)
            print(
                f"  {index + 1}/{runs}: ok={sample.ok} gen={sample.gen_tps:.2f} "
                f"prefill={sample.prompt_tps:.2f} ttft={sample.ttft_s:.3f}s "
                f"cached={sample.cached_prompt_tokens}",
                flush=True,
            )

    xlong_prompt = make_xlong_prompt(args.xlong_repeats)
    try:
        update_model_context(args.api_url, args.model, args.xlong_num_ctx)
        print(
            f"xlong: {args.xlong_runs} samples x {args.xlong_predict} tokens "
            f"(context cap {args.xlong_num_ctx})",
            flush=True,
        )
        for index in range(args.xlong_runs):
            sample = stream_generate(
                args.api_url,
                args.model,
                xlong_prompt,
                args.xlong_predict,
                args.timeout,
            )
            sample.prompt_label = "xlong"
            samples.append(sample)
            print(
                f"  {index + 1}/{args.xlong_runs}: ok={sample.ok} "
                f"gen={sample.gen_tps:.2f} prefill={sample.prompt_tps:.2f} "
                f"ttft={sample.ttft_s:.3f}s cached={sample.cached_prompt_tokens}",
                flush=True,
            )
    finally:
        update_model_context(args.api_url, args.model, original_context)

    mtp_samples = read_mtp_stats(log_path, log_offset)
    for sample, mtp_sample in zip(samples, mtp_samples):
        sample.mtp = mtp_sample
    accepted = sum(item["accepted_tokens"] for item in mtp_samples)
    drafted = sum(item["drafted_tokens"] for item in mtp_samples)
    mtp_summary = {
        "enabled": bool(settings.get("vlm_mtp_enabled")),
        "draft_model": draft_info.get("display_name") or draft_id,
        "draft_size_bytes": int(draft_info.get("estimated_size") or 0),
        "block_size": settings.get("vlm_mtp_draft_block_size"),
        "sample_count": len(mtp_samples),
        "accepted_tokens": accepted,
        "drafted_tokens": drafted,
        "acceptance_percent": accepted / drafted * 100 if drafted else 0.0,
        "rounds": sum(item["rounds"] for item in mtp_samples),
        "emitted_tokens": sum(item["emitted_tokens"] for item in mtp_samples),
    }

    finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report = Report(
        runtime="oMLX",
        runtime_version=get_runtime_version(),
        api_url=args.api_url,
        model=args.model,
        display_name=model_info["display_name"],
        model_path=str(model_path),
        size_bytes=int(model_info.get("actual_size") or model_info.get("estimated_size") or 0),
        parameter_count=args.parameters,
        quantization=quant_name,
        architecture=str(config.get("model_type") or model_info.get("config_model_type")),
        model_context_length=int(model_info.get("model_context_length") or 0),
        started_at=started_at,
        finished_at=finished_at,
        load_first_request_s=load_first_s,
        host=detect_host(),
        power_mode=get_power_mode(),
        settings=settings,
        protocol={
            "short_runs": args.short_runs,
            "long_runs": args.long_runs,
            "xlong_runs": args.xlong_runs,
            "short_predict": args.short_predict,
            "long_predict": args.long_predict,
            "xlong_predict": args.xlong_predict,
            "xlong_repeats": args.xlong_repeats,
            "xlong_num_ctx": args.xlong_num_ctx,
            "temperature": 0.0,
            "seed": 42,
        },
        mtp=mtp_summary,
        samples=[asdict(sample) for sample in samples],
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{args.output_prefix}.json"
    md_path = output_dir / f"{args.output_prefix}.md"
    json_path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    render_model_report(report, md_path)
    render_comparison(report, output_dir / "00_comparison.md")
    print(f"Wrote {json_path}, {md_path}, and 00_comparison.md", flush=True)

    unload_model(args.api_url, args.model)
    return 0 if all(sample.ok for sample in samples) else 1


if __name__ == "__main__":
    raise SystemExit(main())
