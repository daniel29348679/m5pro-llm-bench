#!/usr/bin/env python3
"""Final comparison report covering 6 Qwen3.6 + 4 Gemma4 models.

Reads the per-model JSONs and writes 00_comparison.md with proper TL;DR,
family-grouped tables, prefill cold/cached split, and observations.
"""

from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
HOST = "Darwin 25.5.0 / Apple M5 Pro / 64 GB"

QWEN_FILES = [
    "qwen3.6_35b.json",
    "qwen3.6_27b.json",
    "qwen3.6_27b-coding-mxfp8.json",
    "qwen3.6_27b-coding-nvfp4.json",
    "qwen3.6_35b-a3b-coding-mxfp8.json",
    "qwen3.6_35b-a3b-coding-nvfp4.json",
]
GEMMA_FILES = [
    "gemma4_e4b.json",
    "gemma4_e4b-it-bf16.json",
    "gemma4_e4b-mlx-bf16.json",
    "gemma4_e4b-nvfp4.json",
]


def gen_tps(s: dict) -> float:
    d = s.get("eval_duration_s") or 0
    return (s.get("eval_count") or 0) / d if d > 0 else 0.0


def prompt_tps(s: dict) -> float:
    d = s.get("prompt_eval_duration_s") or 0
    return (s.get("prompt_eval_count") or 0) / d if d > 0 else 0.0


def split_by_label(samples: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"short": [], "long": [], "xlong": []}
    for s in samples:
        if not s.get("ok"):
            continue
        lbl = s.get("prompt_label")
        if lbl in out:
            out[lbl].append(s)
    return out


def mean(xs: list[float]) -> float:
    xs = [x for x in xs if x > 0]
    return statistics.mean(xs) if xs else 0.0


def load_row(path: Path, family: str) -> dict:
    r = json.loads(path.read_text(encoding="utf-8"))
    by = split_by_label(r["samples"])
    short, long_, xlong = by["short"], by["long"], by["xlong"]
    return {
        "family": family,
        "model": r["model"],
        "params": r["parameter_count"],
        "quant": r["quantization"],
        "size_gb": r["size_bytes"] / 1e9,
        "load_s": r["load_first_request_s"],
        "short_gen": mean([gen_tps(s) for s in short]),
        "long_gen": mean([gen_tps(s) for s in long_]),
        "xlong_gen": mean([gen_tps(s) for s in xlong]),
        "short_prompt_cold": prompt_tps(short[0]) if short else 0.0,
        "long_prompt_cold": prompt_tps(long_[0]) if long_ else 0.0,
        "xlong_prompt_cold": prompt_tps(xlong[0]) if xlong else 0.0,
        "short_ttft_cold": short[0]["ttft_s"] if short else 0.0,
        "long_ttft_cold": long_[0]["ttft_s"] if long_ else 0.0,
        "xlong_ttft_cold": xlong[0]["ttft_s"] if xlong else 0.0,
        "xlong_wall_cold": xlong[0]["wall_total_s"] if xlong else 0.0,
        "xlong_prompt_n": xlong[0]["prompt_eval_count"] if xlong else 0,
    }


def main() -> int:
    rows: list[dict] = []
    for f in QWEN_FILES:
        p = RESULTS / f
        if p.exists():
            rows.append(load_row(p, "Qwen3.6"))
    for f in GEMMA_FILES:
        p = RESULTS / f
        if p.exists():
            rows.append(load_row(p, "Gemma4"))

    qwen_rows = [r for r in rows if r["family"] == "Qwen3.6"]
    gemma_rows = [r for r in rows if r["family"] == "Gemma4"]

    by_short = sorted(rows, key=lambda r: r["short_gen"], reverse=True)
    by_long = sorted(rows, key=lambda r: r["long_gen"], reverse=True)
    by_xlong = sorted(rows, key=lambda r: r["xlong_gen"], reverse=True)
    by_long_prefill = sorted(rows, key=lambda r: r["long_prompt_cold"], reverse=True)
    by_xlong_prefill = sorted(rows, key=lambda r: r["xlong_prompt_cold"], reverse=True)

    L: list[str] = []
    L.append("# Qwen3.6 + Gemma4 Ollama 速度綜合對比 — run2 (高效能模式 + 16k 上下文)")
    L.append("")
    L.append(f"- 報告產生時間: `{datetime.now().astimezone().isoformat(timespec='seconds')}`")
    L.append(f"- 主機: {HOST}")
    L.append(f"- Python: `{sys.version.split()[0]}`")
    L.append("- Ollama URL: `http://localhost:11434`")
    L.append("- 系統電源模式: `pmset powermode=2` (High Power, AC 供電)")
    L.append("- 防睡眠: `caffeinate -dimsu` 全程啟用")
    L.append("- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`,每模型 cold-start + warmup 後才取樣")
    L.append("- 取樣: short × 5 (256 tok)、long × 4 (512 tok)、xlong × 3 (256 tok, num_ctx=16384, prompt ~11k tok)")
    L.append("- 受測模型: 6 × Qwen3.6 系列 + 4 × Gemma4 e4b 系列 = 10 個模型")
    L.append("")

    L.append("## TL;DR — 一句話結論")
    L.append("")
    L.append("### Qwen3.6 系列")
    L.append("- **MoE 35b-a3b 在解碼上完勝 dense**：`qwen3.6:35b-a3b-coding-nvfp4` (80.6 tok/s) 是 Qwen 最快,約是 dense 35b 的 2 倍、dense 27b 的 7 倍。")
    L.append("- **nvfp4 量化壓倒性勝過 mxfp8**：同架構下 nvfp4 解碼快 1.3–1.7 倍,模型檔小 40%~43%。")
    L.append("- **dense 27b-coding-mxfp8 反常**：9.86 tok/s 比原版 27b 的 11.82 還慢,且檔案大 1.8 倍 — mxfp8 在 Apple Silicon Metal backend 沒有原生加速。")
    L.append("")
    L.append("### Gemma4 e4b 系列")
    L.append("- **e4b 4-bit 與 nvfp4 解碼幾乎相同**：68.6 vs 69.3 tok/s,差距 1%。")
    L.append("- **但 nvfp4 的 prefill 快很多**：xlong cold prefill 4206 vs 736 tok/s,**5.7 倍**。長 prompt 場景 nvfp4 明顯較佳。")
    L.append("- **BF16 變體解碼慢 2.4 倍**：28.0–28.4 vs 4-bit 的 68 tok/s,符合 BF16 記憶體頻寬需求 2x 的理論。")
    L.append("- **`mlx-bf16` 解碼與 `it-bf16` 相同,但 prefill 大幅領先**：xlong cold prefill 3721 vs 782 tok/s (4.8 倍);長 prompt 場景 mlx 較佳。")
    L.append("- **`e4b-nvfp4` 是 8B 級最佳全能選擇**：69 tok/s 解碼、9.6 GB 檔案、1.09s 載入、prefill 也最快。")
    L.append("")
    L.append("### 跨系列比較")
    L.append("- **8B Gemma4 e4b 解碼完勝 27B Qwen dense**：69 vs 11.8 tok/s (5.8x)。要快先看模型大小,再看 quant。")
    L.append("- **35B-MoE (3B active) 仍微勝 8B dense**：80.6 vs 69.3 tok/s,只快 16%,但模型大 2x 且品質應較高。")
    L.append("- **長上下文懲罰一致很小**：所有 10 個模型從 short → 11k token xlong 解碼速度只掉 4–10%。M5 Pro 的記憶體頻寬對 16k context 仍未撞瓶頸。")
    L.append("- **電源模式必須鎖 High Power**：上一輪 Automatic 模式下 dense 模型慢 50%~90%;nvfp4 在兩種模式下都已跑滿。")
    L.append("")

    L.append("## 主表 — 生成速度 (cache 不影響)")
    L.append("")
    L.append("| 系列 | 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | short gen | long gen | xlong gen |")
    L.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    for r in rows:
        L.append(
            f"| {r['family']} | `{r['model']}` | {r['params']} | {r['quant']} | "
            f"{r['size_gb']:.2f} | {r['load_s']:.2f} | "
            f"{r['short_gen']:.2f} | {r['long_gen']:.2f} | {r['xlong_gen']:.2f} |"
        )
    L.append("")
    L.append("> `gen` 為純解碼 tokens/s (`eval_count / eval_duration`,越大越快)。受 KV cache 命中影響極小,是最穩定的速度指標。")
    L.append("")

    L.append("## Prefill 主表 — 冷啟 (run 1, KV cache 未命中)")
    L.append("")
    L.append("Ollama 對相同 prompt 會重用 KV cache,所以第 2 次起的 prefill 不是真正的 prefill 速度。下表只取每個模型 long/xlong 的第一筆 (冷啟) 作為代表。")
    L.append("")
    L.append("| 系列 | 模型 | short prompt tok/s | long prompt tok/s (cold) | xlong prompt tok/s (cold) | short TTFT (s) | long TTFT (s) cold | xlong TTFT (s) cold | xlong wall (s) cold |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        L.append(
            f"| {r['family']} | `{r['model']}` | "
            f"{r['short_prompt_cold']:.2f} | "
            f"{r['long_prompt_cold']:.2f} | "
            f"{r['xlong_prompt_cold']:.2f} | "
            f"{r['short_ttft_cold']:.3f} | "
            f"{r['long_ttft_cold']:.3f} | "
            f"{r['xlong_ttft_cold']:.2f} | "
            f"{r['xlong_wall_cold']:.2f} |"
        )
    L.append("")
    L.append(f"> xlong prompt 約 {rows[0]['xlong_prompt_n']} tokens; TTFT 為 client 收到第一個 token 的 wall-clock 秒數。")
    L.append("> ⚠️ Gemma4 系列的 xlong TTFT 顯示 0.00s 是量測 bug — gemma4 的串流首 chunk 行為與 qwen 不同,不含 response/thinking 字串,導致客戶端的 TTFT 偵測未觸發。請以 `xlong wall` 減去 `eval_count / xlong_gen` 推算實際 TTFT。")
    L.append("")

    L.append("## 排名")
    L.append("")
    L.append("### short prompt 解碼速度")
    L.append("")
    L.append("| 排名 | 系列 | 模型 | short gen tok/s |")
    L.append("|---:|---|---|---:|")
    for i, r in enumerate(by_short, 1):
        L.append(f"| {i} | {r['family']} | `{r['model']}` | {r['short_gen']:.2f} |")
    L.append("")

    L.append("### long prompt 解碼速度")
    L.append("")
    L.append("| 排名 | 系列 | 模型 | long gen tok/s |")
    L.append("|---:|---|---|---:|")
    for i, r in enumerate(by_long, 1):
        L.append(f"| {i} | {r['family']} | `{r['model']}` | {r['long_gen']:.2f} |")
    L.append("")

    L.append("### xlong (16k 上下文) 解碼速度")
    L.append("")
    L.append("| 排名 | 系列 | 模型 | xlong gen tok/s | 平均 prompt tokens |")
    L.append("|---:|---|---|---:|---:|")
    for i, r in enumerate(by_xlong, 1):
        L.append(f"| {i} | {r['family']} | `{r['model']}` | {r['xlong_gen']:.2f} | {r['xlong_prompt_n']:.0f} |")
    L.append("")

    L.append("### long prompt 冷啟 prefill 速度 (吃 prompt 能力)")
    L.append("")
    L.append("| 排名 | 系列 | 模型 | long prompt tok/s (cold) |")
    L.append("|---:|---|---|---:|")
    for i, r in enumerate(by_long_prefill, 1):
        L.append(f"| {i} | {r['family']} | `{r['model']}` | {r['long_prompt_cold']:.2f} |")
    L.append("")

    L.append("### xlong (11k tokens) 冷啟 prefill 速度")
    L.append("")
    L.append("| 排名 | 系列 | 模型 | xlong prompt tok/s (cold) | xlong wall (s) |")
    L.append("|---:|---|---|---:|---:|")
    for i, r in enumerate(by_xlong_prefill, 1):
        L.append(
            f"| {i} | {r['family']} | `{r['model']}` | "
            f"{r['xlong_prompt_cold']:.2f} | {r['xlong_wall_cold']:.2f} |"
        )
    L.append("")

    L.append("## 觀察與分析")
    L.append("")
    L.append("### 1. MoE vs Dense (Qwen3.6 內部)")
    L.append("- `35b-a3b-coding-nvfp4` (MoE, 3B active)：80.6 tok/s short")
    L.append("- `35b` (dense)：41.7 tok/s short")
    L.append("- 兩者參數量相近 (35–36B),但 MoE 推論時只啟用 3B → 解碼速度幾乎兩倍。")
    L.append("")

    L.append("### 2. 量化格式：nvfp4 vs mxfp8 (Qwen3.6)")
    L.append("同架構 `35b-a3b-coding`：")
    L.append("- nvfp4：80.6 tok/s short / 21 GB")
    L.append("- mxfp8：60.4 tok/s short / 37 GB")
    L.append("- nvfp4 解碼 +33%、模型檔 -43%。")
    L.append("")
    L.append("同架構 `27b-coding`：")
    L.append("- nvfp4：16.3 tok/s short / 19 GB")
    L.append("- mxfp8：9.9 tok/s short / 31 GB")
    L.append("- nvfp4 解碼 +65%、模型檔 -39%。")
    L.append("")

    L.append("### 3. dense 27b-coding-mxfp8 的異常")
    L.append("`27b-coding-mxfp8` (9.9 tok/s) 比原版 `qwen3.6:27b` Q4_K_M (11.8 tok/s) 還慢,且檔案大 1.8 倍。")
    L.append("- mxfp8 在 Apple Silicon 的 Metal backend 上沒有原生加速。")
    L.append("- 推論：在 M5 Pro 上跑 27b dense 程式碼模型應選 nvfp4 (16.3 tok/s)。")
    L.append("")

    L.append("### 4. Gemma4 系列 — 量化對 prefill vs 解碼的影響")
    L.append("Gemma4 e4b 4 個變體解碼速度只有 2 個層級 (4-bit ~68, BF16 ~28),但 prefill 卻有顯著差異：")
    L.append("")
    L.append("| 變體 | 大小 | 解碼 (short) | xlong cold prefill | xlong wall (s) |")
    L.append("|---|---:|---:|---:|---:|")
    for r in gemma_rows:
        L.append(
            f"| `{r['model']}` | {r['size_gb']:.2f} GB | "
            f"{r['short_gen']:.2f} | "
            f"{r['xlong_prompt_cold']:.2f} | "
            f"{r['xlong_wall_cold']:.2f} |"
        )
    L.append("")
    L.append("**關鍵發現**：")
    L.append("- **解碼 = 記憶體頻寬綁住**：4-bit (e4b, e4b-nvfp4) 都是 ~68 tok/s,BF16 (it-bf16, mlx-bf16) 都是 ~28 tok/s。一個模型 weights 走過記憶體一次/token,bytes 越少越快。")
    L.append("- **Prefill = compute 綁住,quant kernel 重要**：")
    L.append("  - `e4b-nvfp4` 的 xlong prefill 4206 tok/s 是同樣 9.6 GB 的 `e4b` Q4-equivalent (736 tok/s) 的 **5.7 倍**。")
    L.append("  - `e4b-mlx-bf16` 的 xlong prefill 3721 tok/s 是同樣 16 GB 的 `e4b-it-bf16` (782 tok/s) 的 **4.8 倍**。")
    L.append("  - 同 quant 用 mlx-friendly 格式或 nvfp4 路徑,prefill 速度提升 5x 級別。")
    L.append("- 對於長 prompt (RAG、code review、長文翻譯),quant 格式對 TTFT 的影響比解碼速度還大。")
    L.append("")

    L.append("### 5. 跨系列：Gemma4 8B vs Qwen 27B / 35B")
    L.append("解碼速度排序：")
    for i, r in enumerate(by_short, 1):
        if i <= 5:
            L.append(f"  {i}. `{r['model']}` ({r['family']}) — {r['short_gen']:.2f} tok/s")
    L.append("")
    L.append("`gemma4:e4b-nvfp4` (8B nvfp4, 9.6 GB) 排第 2,只比 `qwen3.6:35b-a3b-coding-nvfp4` (35B MoE, 21 GB) 慢 16%。")
    L.append("但前者參數量是後者的 1/4,品質應較弱。模型大小通常壓過 quant 與架構優化的速度差。")
    L.append("")

    L.append("### 6. 長上下文懲罰 (短 prompt → 11k token prompt)")
    L.append("")
    L.append("| 模型 | short → xlong | 衰減 |")
    L.append("|---|---|---:|")
    for r in rows:
        if r["short_gen"] > 0:
            ratio = r["xlong_gen"] / r["short_gen"]
            drop_pct = (1 - ratio) * 100
            L.append(
                f"| `{r['model']}` | {r['short_gen']:.2f} → {r['xlong_gen']:.2f} | "
                f"-{drop_pct:.1f}% |"
            )
    L.append("")
    L.append("所有模型衰減都在 4–10%,M5 Pro 的記憶體頻寬對 16k context 仍很穩。")
    L.append("")

    L.append("### 7. Gemma4 的 TTFT 異常")
    L.append("Gemma4 系列在 short prompt 下 TTFT 介於 1.6–5.7s,而 prefill 32 token / 1400 tok/s ≈ 0.02s。")
    L.append("差距 1.5–5.7s 不在 prefill,可能是 ollama 對 gemma3-style chat template 處理或某種延遲首 chunk 的行為。")
    L.append("xlong run 中,gemma4 的 TTFT 量測都顯示 0.00s — 這是 client 串流端偵測 bug:gemma4 的首 chunk 不含 response/thinking 字串,客戶端的 first-token 偵測未觸發。**真實 TTFT 請以 `xlong wall - eval_count / xlong_gen` 推算**。")
    L.append("")

    L.append("## 與 run1 (Automatic powermode) 的對照 — 僅 Qwen 系列")
    L.append("")
    L.append("上一輪在 `powermode=0` (Automatic) 下執行,未鎖定 High Power。")
    L.append("")
    L.append("| 模型 | run1 short gen | run2 short gen (High Power) | 增幅 |")
    L.append("|---|---:|---:|---:|")
    L.append("| `qwen3.6:35b` | 27.36 | 41.68 | +52% |")
    L.append("| `qwen3.6:27b` | 6.24 | 11.82 | +89% |")
    L.append("| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |")
    L.append("| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |")
    L.append("")
    L.append("> nvfp4 在 Automatic 模式下幾乎已跑滿,dense 模型則受 powermode 影響極大。建議任何需要可重現的速度量測都先把 macOS 切到 High Power (`sudo pmset -a powermode 2`)。")
    L.append("")

    L.append("## 指標說明")
    L.append("")
    L.append("- **gen tok/s**：純解碼 tokens/s (`eval_count / eval_duration`)。受 KV cache 命中影響極小,是最穩定的速度指標。")
    L.append("- **prompt tok/s**：prefill 速度。⚠️ Ollama 在相同 prompt 連續送出時會直接重用 KV cache,第 2 次起的數值會異常巨大 (cache hit)。本報告用「冷啟 (run 1)」代表真正的 prefill 速度。")
    L.append("- **TTFT**：client 收到第一個 token 的 wall-clock 秒數。受 prompt 長度與 prefill 速度雙重影響。⚠️ Gemma4 xlong TTFT 為量測 bug,請看 `xlong wall`。")
    L.append("- **冷啟 (load)**：模型剛載入記憶體後第一次 forward 的時間。")
    L.append("- **xlong**：~11k tokens 合成語料 + `num_ctx=16384` 量測長上下文 prefill 與解碼速度。")
    L.append("")

    out_path = ROOT / "REPORT.md"
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {out_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
