# M5 Pro LLM Benchmark — Ollama + oMLX Leaderboard

**Languages**: **English** · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

This repository benchmarks local LLM throughput with [Ollama](https://ollama.com) and [oMLX](https://github.com/jundot/omlx) on an **Apple M5 Pro with 64 GB of unified memory**. The leaderboard below is the primary project summary and is updated whenever a new model benchmark is added.

## Current Leaderboard

**Last updated:** August 17, 2026, with `mlx-community/Qwen3.8-27B-4bit` on oMLX 0.6.0.

Overall rank is determined by the arithmetic mean of short, long, and 11k-context decode throughput. Only the latest retained successful run for each model is included.

| Rank | Model | Runtime | Short | Long | 11k context | Overall average | Evidence |
|---:|---|---:|---:|---:|---:|---:|---|
| **1** | `qwen3.6:35b-a3b-mtp-q4_K_M` | Ollama 0.30.6 | **86.79** | **87.97** | **79.94** | **84.90** | [draft-4 report](./results/ollama_0.30.6_update/mtp_draft4/qwen3.6_35b-a3b-mtp-q4_K_M.md) |
| **2** | `nemotron-3.5-lightning:30b-mlx` | Ollama 0.32.9 | 68.36 | 70.01 | 64.69 | 67.69 | [Ollama 0.32.9 report](./results/ollama_0.32.9_update/installed/nemotron-3.5-lightning_30b-mlx.md) |
| **3** | `qwen3.6:35b-a3b-coding-nvfp4` | Ollama 0.30.6 | 64.57 | 64.58 | 59.15 | 62.77 | [installed-model report](./results/ollama_0.30.6_update/installed/qwen3.6_35b-a3b-coding-nvfp4.md) |
| **4** | `gemma4:26b-nvfp4` | Ollama 0.30.6 | 59.16 | 58.33 | 49.07 | 55.52 | [installed-model report](./results/ollama_0.30.6_update/installed/gemma4_26b-nvfp4.md) |
| **5** | `qwen3.8:27b-mlx` | Ollama 0.32.13 | 34.25 | 32.79 | 34.38 | 33.81 | [Ollama report](./results/ollama_0.32.13_update/installed/qwen3.8_27b-mlx.md) |
| **6** | `muse-glimmer:30b-mlx` | Ollama 0.32.7 | 24.05 | 26.30 | 24.74 | 25.03 | [Ollama 0.32.7 report](./results/ollama_0.32.7_update/installed/muse-glimmer_30b-mlx.md) |
| **7** | `mlx-community/Qwen3.8-27B-4bit` | oMLX 0.6.0 | 26.28 | 22.81 | 19.88 | 22.99 | [oMLX report](./results/omlx_0.6.0/installed/qwen3.8_27b-4bit_mtp.md) |
| **8** | `qwen3.6:27b-mtp-q4_K_M` | Ollama 0.30.6 | 17.41 | 20.62 | 15.77 | 17.93 | [draft-4 report](./results/ollama_0.30.6_update/mtp_draft4/qwen3.6_27b-mtp-q4_K_M.md) |
| **9** | `gemma4:31b-nvfp4` | Ollama 0.30.6 | 10.41 | 10.27 | 9.14 | 9.94 | [installed-model report](./results/ollama_0.30.6_update/installed/gemma4_31b-nvfp4.md) |

All throughput values are server-reported decode tokens/s; Ollama rows use `eval_count / eval_duration`, while the oMLX row uses `generation_tokens_per_second` from streaming usage. Higher is better.

> **Comparability note:** current rows span multiple Ollama versions plus oMLX 0.6.0. The prompts, output limits, sample counts, power mode, and xlong context cap match, but runtime instrumentation, model packaging, quantization, and MTP implementation differ. Treat the table as a practical ranking rather than a strict runtime shootout.

The leaderboard measures throughput, not response quality, reasoning accuracy, feature support, or memory efficiency. The older Ollama 0.21 suite remains available in [REPORT.md](./REPORT.md) but is not mixed into the current ranking.

## Current Takeaways

- **Fastest overall:** `qwen3.6:35b-a3b-mtp-q4_K_M` with the model-default `draft_num_predict=4`.
- **Fastest model tested on Ollama 0.32.9:** `nemotron-3.5-lightning:30b-mlx`, ranked second overall.
- **Fastest non-MTP Qwen:** `qwen3.6:35b-a3b-coding-nvfp4`.
- **Fastest Gemma:** `gemma4:26b-nvfp4`.
- **Latest run:** `mlx-community/Qwen3.8-27B-4bit` on oMLX 0.6.0, ranked seventh with a 22.99 tokens/s three-scenario average.
- **Qwen3.8 runtime result:** the tested Ollama package averaged 33.81 tokens/s; the tested oMLX target-plus-drafter pair averaged 22.99 tokens/s. They use different quantization and MTP packaging, so this is not a clean runtime-only comparison.
- **Qwen MTP modes:** keep `draft_num_predict=4` for the older Qwen3.6 GGUF tags; Ollama's Qwen3.8 package uses an inline MTP head, while this oMLX setup uses a separate 250.9 MB MTP drafter with block size 3.

## Latest Benchmark — oMLX `mlx-community/Qwen3.8-27B-4bit`

| Property | Result |
|---|---|
| Runtime | oMLX 0.6.0 |
| Architecture / parameters | `qwen3_5` dense hybrid-attention model / 27.8B |
| Quantization / target size | 4-bit affine / 16.68 GB |
| Model context / measured xlong context | 262144 / 16384 tokens |
| Speculative decoding | External `Qwen3.8-27B-MTP-4bit` drafter / 250.9 MB / block size 3 |
| Cold-start load time | 2.23 s |
| Successful measured samples | 12 / 12 |
| First uncached 11k prefill | 368.32 tokens/s |
| First uncached 11k TTFT | 30.18 s |

The three-scenario decode average was **22.99 tokens/s** (26.28 short, 22.81 long, 19.88 at 11k context). All five short samples stopped naturally after 146 completion tokens; the long and xlong samples reached their generation limits. During the 12 formal samples, MTP accepted 1,836 of 3,416 drafted tokens (53.7%). The first xlong sample was uncached; the next two restored 10,240 prompt tokens from oMLX's block prefix cache. The target checkpoint itself contains no embedded `mtp.*` tensors, so acceleration comes from the external drafter. See the [full result](./results/omlx_0.6.0/installed/00_comparison.md) and [raw JSON](./results/omlx_0.6.0/installed/qwen3.8_27b-4bit_mtp.json).

## Benchmark Protocol

| Case | Prompt size | Generation limit | Samples |
|---|---|---:|---:|
| Short | Fixed short prompt; 26–72 tokens depending on tokenizer | 256 | 5 |
| Long | Fixed design prompt; 149–194 tokens depending on tokenizer | 512 | 4 |
| 11k context | Approximately 10.8k–11.3k tokens with `num_ctx=16384` | 256 | 3 |

- Test options: `temperature=0` and `seed=42`; Ollama runs also use `keep_alive=10m`.
- Power mode: `pmset powermode=2` on AC power.
- Sleep prevention: `caffeinate -dimsu` for the full run.
- Decode throughput: Ollama `eval_count / eval_duration`; oMLX streaming `generation_tokens_per_second`.
- Prefill throughput: Ollama `prompt_eval_count / prompt_eval_duration`; oMLX streaming `prompt_tokens_per_second`.
- TTFT: client-observed wall-clock time until the first streamed token.

## MTP Draft-Token Retest

| Model | `draft_num_predict` | Short | Long | 11k context | Change vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**Conclusion:** do not force `draft_num_predict=8` on this machine. Use the model default of `4` for these Qwen MTP models.

## Historical Suite

The original Ollama 0.21 suite tested 10 models and remains the reference for older architecture, quantization, and MLX comparisons:

| Historical finding | Result |
|---|---|
| Best short decode | `qwen3.6:35b-a3b-coding-nvfp4` at 80.61 tokens/s |
| Best 11k cold prefill | `gemma4:e4b-nvfp4` at 4205.55 tokens/s |
| Apple Silicon quantization finding | `mxfp8` was slower than Q4_K_M despite larger files |
| MLX finding | MLX helped prefill, not decode, in the clean Gemma BF16 pair |

See [REPORT.md](./REPORT.md) for the full historical comparison.

## Raw Results

- [oMLX 0.6.0 `Qwen3.8-27B-4bit` result](./results/omlx_0.6.0/installed/00_comparison.md)
- [Ollama 0.32.13 `qwen3.8:27b-mlx` result](./results/ollama_0.32.13_update/installed/00_comparison.md)
- [Ollama 0.32.9 `nemotron-3.5-lightning:30b-mlx` result](./results/ollama_0.32.9_update/installed/00_comparison.md)
- [Ollama 0.32.7 `muse-glimmer:30b-mlx` result](./results/ollama_0.32.7_update/installed/00_comparison.md)
- [Ollama 0.30.6 installed-model comparison](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Ollama 0.30.6 MTP draft-4 comparison](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Ollama 0.30.6 MTP draft-8 comparison](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Historical Ollama 0.21 report](./REPORT.md)

## Leaderboard Maintenance

Whenever a new benchmark is added:

1. Add or replace that model's row in **Current Leaderboard** using its latest successful run.
2. Recalculate `Overall average`, sort the table, and update the rank numbers.
3. Update the `Last updated` line and preserve the runtime and version for every row.
4. Link each leaderboard row to its supporting report.
5. Keep benchmark reports and the main README in English unless another language is explicitly requested.
