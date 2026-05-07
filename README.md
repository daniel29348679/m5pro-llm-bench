# M5 Pro LLM Benchmark — Ollama, MLX, and Quantization

**Languages**: **English** · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

This repo benchmarks **10 local LLMs on Apple M5 Pro / 64 GB** via [Ollama](https://ollama.com), comparing:

- **MoE vs dense** decode speed (Qwen3.6 35b-a3b vs 35b dense)
- **Quantization formats** for prefill vs decode (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX-tagged BF16 vs ordinary BF16** prefill performance
- **macOS High Power mode** impact on throughput

> **TL;DR**: On M5 Pro, **model size > quantization > architecture optimization**. Decode is memory-bandwidth bound; prefill is quant-kernel bound — they follow completely different rules. See [REPORT.md](./REPORT.md) for full data.

## Models tested (10)

| Family | Model | Params | Quant | File size |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B active) | mxfp8 | 37 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B active) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## Top results

### Short-prompt decode speed (mean of 5 samples)

| Rank | Model | tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | `qwen3.6:27b-coding-mxfp8` | 9.89 |

### xlong (~11k token) cold-prefill speed

| Rank | Model | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## Key findings

### 1. Decode and prefill have different bottlenecks

- **Decode is memory-bandwidth bound**: weights traverse memory once per token. Gemma4 4-bit variants (e4b, e4b-nvfp4) all decode at ~68 tok/s; BF16 variants (it-bf16, mlx-bf16) at ~28 tok/s. **2.4× slower matches 2× weight size exactly.**
- **Prefill is compute and quant-kernel bound**: same 4-bit, same 9.6 GB, e4b vs e4b-nvfp4 decode identically — yet nvfp4's cold xlong prefill is **5.7× faster** (4206 vs 736 tok/s).

### 2. nvfp4 is the all-round winner on this M5 Pro

- Within the same architecture, nvfp4 decodes 33–65% faster, with files 39–43% smaller.
- On Gemma4 nvfp4 doesn't help decode but speeds up prefill by ~5×.
- Conclusion: **always pick nvfp4 if available**.

### 3. mxfp8 is a trap on Apple Silicon

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) is **slower than the original Q4_K_M (11.82 tok/s)** despite being 1.8× larger — mxfp8 has no native Metal backend acceleration.

### 4. The "MLX" tag doesn't help decode but accelerates prefill ~5×

`gemma4:e4b-mlx-bf16` and `gemma4:e4b-it-bf16` decode identically at ~28 tok/s, but cold xlong prefill is **3721 vs 782 tok/s (4.8×)**. Pick MLX variants only when long prompts dominate.

### 5. MoE pays off on M5 Pro

`qwen3.6:35b-a3b` (3B active) decodes at **~80 tok/s**, twice as fast as the equivalent dense `qwen3.6:35b` (41.68). MoE only walks 3B of weights through memory per token — perfectly aligned with the bandwidth bound.

### 6. macOS power mode is decisive for dense models

| Model | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Reproducible benchmarks must lock High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k long-context penalty is small

All 10 models lose only **4–10%** decode speed going from short → 11k-token xlong. M5 Pro / 64 GB has plenty of headroom for 16k context.

## Test environment

- **Hardware**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB unified memory
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
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
    ├── qwen3.6_*.json / .md        # 6 Qwen3.6 models — raw + summary
    └── gemma4_*.json / .md         # 4 Gemma4 models — raw + summary
```

## Known measurement caveats

- **Gemma4 short-prompt TTFT is high (1.6–5.7 s)**: out of proportion with prefill time (32 / ~1400 ≈ 0.02 s). Likely Ollama-side gemma3-style chat-template processing.
- **Gemma4 xlong TTFT shows 0.00 s — client-side streaming detection bug**: gemma4's first stream chunk lacks `response`/`thinking` strings, so the client's first-token detector never fires. Use `xlong wall - eval_count / xlong_gen` to back out actual TTFT.
- **Ollama KV-cache reuse**: identical prompts on the 2nd run inflate `prompt_eval` numbers ridiculously. The report only takes cold prefill (run 1).

## License

CC BY-SA 4.0. Cite, modify, redistribute freely with attribution.

## Contributing

Other M5 Pro owners running additional models (Llama 3.3, DeepSeek, Phi 4, …) are welcome to open a PR or issue. If you have different hardware (M4 / M3 Max / Studio), a matching dataset would be very valuable.
