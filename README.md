# M5 Pro LLM Benchmark — Ollama 0.30.6, MTP, MLX, and Quantization

**Languages**: **English** · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

This repo benchmarks local LLM throughput on **Apple M5 Pro / 64 GB** via [Ollama](https://ollama.com). It contains two data sets:

- **Current update**: Ollama **0.30.6** installed-model run, including Qwen3.6 MTP models and draft-depth checks.
- **Historical full suite**: the original 10-model Ollama run covering Qwen3.6, Gemma4, MLX-tagged models, and quantization formats.

The benchmark compares:

- **MoE vs dense** decode speed (Qwen3.6 35b-a3b vs 35b dense)
- **MTP draft settings** (`draft_num_predict=4` default vs `8`)
- **Quantization formats** for prefill vs decode (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX-tagged BF16 vs ordinary BF16** prefill performance
- **macOS High Power mode** impact on throughput

> **TL;DR**: On the current Ollama 0.30.6 setup, `qwen3.6:35b-a3b-mtp-q4_K_M` is the fastest installed Qwen model tested here: **83.65 / 84.74 / 76.68 tok/s** on short / long / xlong decode. MTP should stay at the model default `draft_num_predict=4`; forcing `8` was slower.

## Current Results — Ollama 0.30.6

After updating Ollama to **0.30.6**, the installed-model ranking changed. The current speed pick is the MTP MoE model:

| Model | Size | short gen | long gen | xlong gen | Change vs comparable baseline |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 22 GB | **83.65** | **84.74** | **76.68** | **+19-20%** vs prior MTP run |
| `qwen3.6:35b-a3b-coding-nvfp4` | 21 GB | 64.57 | 64.58 | 59.15 | **-20%** vs original run2 |
| `gemma4:26b-nvfp4` | 16 GB | 59.16 | 58.33 | 49.07 | New same-method baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 17 GB | 19.43 | 20.60 | 15.95 | Mostly flat; short +9.6% |
| `gemma4:31b-nvfp4` | 20 GB | 10.41 | 10.27 | 9.14 | New same-method baseline; not a speed pick |

**Current recommendation:** use `qwen3.6:35b-a3b-mtp-q4_K_M` for Qwen throughput on this machine. It now beats the previous fastest `qwen3.6:35b-a3b-coding-nvfp4` in the local Ollama 0.30.6 setup.

Keep MTP `draft_num_predict` at the model default `4`. Forcing `draft_num_predict=8` was slower across both MTP models:

| Model | draft | short gen | long gen | xlong gen |
|---|---:|---:|---:|---:|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 69.75 | 70.57 | 64.29 |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 36.67 | 46.66 | 40.72 |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.72 | 20.37 | 15.93 |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.44 | 12.61 | 8.97 |

Raw update results:

- [Ollama 0.30.6 installed-model comparison](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP default draft-4 baseline](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 comparison](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)

## What Changed

- The **current fastest local model** in this repo is now `qwen3.6:35b-a3b-mtp-q4_K_M` on Ollama 0.30.6.
- The older `qwen3.6:35b-a3b-coding-nvfp4` result remains useful as a historical baseline, but it regressed by about **20%** under the current 0.30.6 installed-model run.
- `qwen3.6:27b-mtp-q4_K_M` improved mostly on short prompts; long and xlong were effectively flat.
- `gemma4:26b-nvfp4` and `gemma4:31b-nvfp4` are new same-method baselines in this update. The 31B nvfp4 model is not a throughput pick.

## Historical Full Suite — Ollama 0.21/run2

The original full-suite report tested 10 models and remains the best apples-to-apples comparison for quantization, MLX tagging, and dense-vs-MoE behavior. See [REPORT.md](./REPORT.md) for the detailed historical report.

### Models tested (10)

| Family | Model | Params | Quant | File size |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B active) | mxfp8 | 37 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B active) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

### Historical Top Results

#### Short-prompt decode speed (mean of 5 samples)

| Rank | Model | tok/s |
|---:|---|---:|
| 1 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.89 |

#### xlong (~11k token) cold-prefill speed

| Rank | Model | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | 🍎 `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | 🍎 `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## Key Findings

### 1. Current Ollama 0.30.6 winner: Qwen3.6 35B-a3B MTP

`qwen3.6:35b-a3b-mtp-q4_K_M` is the best current throughput result: **83.65 tok/s short**, **84.74 tok/s long**, and **76.68 tok/s xlong**. That is about **20% faster** than the earlier MTP baseline and faster than the older coding nvfp4 winner in this local setup.

### 2. MTP draft depth matters

The MTP model default `draft_num_predict=4` is the right setting for these tests. `draft_num_predict=8` made both MTP models slower, by roughly **34-47%** depending on prompt length and model.

### 3. Decode and prefill have different bottlenecks

- **Decode is usually memory-bandwidth bound**: weights traverse memory once per token. In the historical Gemma4 suite, 4-bit variants decode at ~68 tok/s while BF16 variants decode at ~28 tok/s.
- **Prefill is compute and quant-kernel bound**: in the historical suite, `gemma4:e4b-nvfp4` has similar decode speed to `gemma4:e4b`, but cold xlong prefill is **5.7x faster** (4206 vs 736 tok/s).

### 4. nvfp4 is strong, but not universally best across Ollama versions

In the historical full suite, nvfp4 was the best all-round format within matching architecture families. Under the current Ollama 0.30.6 installed-model run, however, `qwen3.6:35b-a3b-coding-nvfp4` regressed by about **20%**, while the new MTP Q4_K_M MoE model became the top Qwen throughput choice.

Practical rule: prefer nvfp4 when it is the best same-architecture option, but verify against current Ollama/runtime versions before treating it as universal.

### 5. mxfp8 is a trap on Apple Silicon

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) is **slower than the original Q4_K_M (11.82 tok/s)** despite being 1.8× larger — mxfp8 has no native Metal backend acceleration.

### 6. The "MLX" tag doesn't help decode but accelerates prefill ~5x

🍎 `gemma4:e4b-mlx-bf16` and `gemma4:e4b-it-bf16` decode identically at ~28 tok/s, but cold xlong prefill is **3721 vs 782 tok/s (4.8×)**. Pick MLX variants only when long prompts dominate.

### 7. MoE pays off on M5 Pro

MoE only walks the active experts through memory per token. That is why both historical and current Qwen3.6 MoE models dominate dense 27B/35B decode speed on this machine.

### 8. macOS power mode is decisive for dense models

| Model | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Reproducible benchmarks must lock High Power**:

```bash
sudo pmset -a powermode 2
```

### 9. 16k long-context penalty is small

All 10 models lose only **4–10%** decode speed going from short → 11k-token xlong. M5 Pro / 64 GB has plenty of headroom for 16k context.

<!-- mlx-caveat:v1 -->
## ⚠️ MLX control-group caveat — read before citing findings 3 & 4

Five of the ten benchmarked models are MLX variants (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

This affects how findings 3 and 4 should be read:

- **Finding 3 (mxfp8 is a trap)**: the comparison is 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs non-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Precise statement: **the MLX mxfp8 path on Ollama's Metal backend is slower than the base-GGUF Q4_K_M path**, despite being 1.8× larger.
- **Finding 4 (MLX tag doesn't help decode but boosts prefill)**: only the gemma4 pair has a clean MLX vs non-MLX BF16 comparison (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). The qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` pairs are *both* MLX, so the nvfp4-vs-mxfp8 contrast there is **a quantization comparison within MLX**, not an isolation of the MLX path itself.

In short: 🍎 marks MLX variants, and the only true "MLX vs non-MLX, all else equal" pair in the suite is the gemma4 BF16 pair.

## Test environment

- **Hardware**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB unified memory
- **Current update OS**: Darwin 25.6.0
- **Current update Ollama**: v0.30.6
- **Historical full-suite OS**: Darwin 25.5.0
- **Historical full-suite Ollama**: v0.21.0
- **Power**: AC, `pmset powermode=2` (High Power)
- **No-sleep**: `caffeinate -dimsu` throughout
- **Python**: 3.14

## Methodology

See [`bench.py`](./bench.py). Key design:

- For each model: `keep_alive=0` unload → cold-start → warmup → measure
- All runs use `temperature=0` `seed=42` `keep_alive=10m` for reproducibility
- Three prompt lengths:
  - **short** × 5: 26~32-token prompt → `num_predict=256`
  - **long** × 4: 149~156-token prompt → `num_predict=512`
  - **xlong** × 3: ~11k-token prompt → `num_predict=256`, forced `num_ctx=16384`
- Decode tok/s = server-reported `eval_count / eval_duration`. **Not affected by KV cache hits.**
- Prefill tok/s only takes the **first run** of long/xlong (cold prefill) — Ollama reuses KV cache for repeated prompts and inflates subsequent prefill numbers absurdly (100k+ tok/s).

## Reproduce

```bash
# 1. Lock High Power
sudo pmset -a powermode 2

# 2. Verify ollama
curl -s http://localhost:11434/api/version

# 3. Pull models
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. Run benchmark (no-sleep + measure)
caffeinate -dimsu -t 18000 &
python3 bench.py \
  --models qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
           qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
           qwen3.6:35b-a3b-coding-nvfp4 \
           gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4 \
  --output-dir results \
  --short-runs 5 --long-runs 4 --xlong-runs 3 \
  --short-predict 256 --long-predict 512 --xlong-predict 256 \
  --xlong-num-ctx 16384

# 5. Render report
python3 render_report.py
```

## Repo layout

```
m5pro-llm-bench/
├── README.md / README.<lang>.md   # This file in 12 languages
├── REPORT.md                       # Full comparison report
├── bench.py                        # Measurement script
├── render_report.py                # Post-processor (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md        # Historical 6 Qwen3.6 models
    ├── gemma4_*.json / .md         # Historical 4 Gemma4 models
    └── ollama_0.30.6_update/       # Current update raw results
```

## Known measurement caveats

- **Gemma4 short-prompt TTFT is high (1.6–5.7 s)**: out of proportion with prefill time (32 / ~1400 ≈ 0.02 s). Likely Ollama-side gemma3-style chat-template processing.
- **Gemma4 xlong TTFT shows 0.00 s — client-side streaming detection bug**: gemma4's first stream chunk lacks `response`/`thinking` strings, so the client's first-token detector never fires. Use `xlong wall - eval_count / xlong_gen` to back out actual TTFT.
- **Ollama KV-cache reuse**: identical prompts on the 2nd run inflate `prompt_eval` numbers ridiculously. The report only takes cold prefill (run 1).

## License

CC BY-SA 4.0. Cite, modify, redistribute freely with attribution.

## Contributing

Other M5 Pro owners running additional models (Llama 3.3, DeepSeek, Phi 4, …) are welcome to open a PR or issue. If you have different hardware (M4 / M3 Max / Studio), a matching dataset would be very valuable.
