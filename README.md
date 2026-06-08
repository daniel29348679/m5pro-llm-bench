# M5 Pro LLM Benchmark — Ollama 0.30.6 Model Picks

**Languages**: **English** · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

This repo benchmarks local LLM throughput on **Apple M5 Pro / 64 GB** with [Ollama](https://ollama.com). The current results use **Ollama 0.30.6** and the models installed on this machine; the older 10-model suite is kept as historical evidence in [REPORT.md](./REPORT.md).

## Quick Pick

| Situation | Pick | Reason |
|---|---|---|
| Fastest current local Qwen model | `qwen3.6:35b-a3b-mtp-q4_K_M` with `draft_num_predict=4` | Best measured decode speed: up to **87.97 tokens/s** |
| You want a Gemma model | `gemma4:26b-nvfp4` | Best current Gemma speed in the installed-model run |
| You need the smaller Qwen MTP model | `qwen3.6:27b-mtp-q4_K_M` with `draft_num_predict=4` | Smaller 17 GB file, but much slower than the 35B-a3B MTP model |
| You are tuning MTP | Keep the model default `draft_num_predict=4` | Forcing `8` was slower on both MTP models |
| You only care about old full-suite comparisons | Read [REPORT.md](./REPORT.md) | Best source for the original 10-model quantization and MLX comparisons |

## Current Results

| Model | Best use | Model file size (GB) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | Data source |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Fastest current Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP retest, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Non-MTP Qwen fallback | 21 | 64.57 | 64.58 | 59.15 | Installed-model run |
| `gemma4:26b-nvfp4` | Fastest current Gemma | 16 | 59.16 | 58.33 | 49.07 | Installed-model run |
| `qwen3.6:27b-mtp-q4_K_M` | Smaller Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP retest, draft 4 |
| `gemma4:31b-nvfp4` | Not a speed pick | 20 | 10.41 | 10.27 | 9.14 | Installed-model run |

## MTP Draft Tokens

| Model | MTP draft tokens (`draft_num_predict`) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | Change vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP conclusion:** do not force `draft_num_predict=8` on this machine. Use the model default `4`.

## Models Tested In The Current Update

| Family | Model | Parameters | Quantization | Model file size (GB) | Notes |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Current winner |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Smaller MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Historical winner, slower in current run |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Best current Gemma result |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | Slow in this run |

## Benchmark Shape

| Case | Prompt length (tokens) | Generation limit (`num_predict`, tokens) | Samples |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | about 11,000 with `num_ctx=16384` | 256 | 3 |

Decode speed is Ollama's server-reported `eval_count / eval_duration`. High Power mode was locked with `pmset powermode=2`, and `caffeinate -dimsu` was used during the runs.

## Historical Notes

The original full suite tested 10 models on Ollama 0.21/run2. Keep using it for architecture, quantization, and MLX comparisons:

| Historical finding | Result |
|---|---|
| Best old short-decode result | `qwen3.6:35b-a3b-coding-nvfp4` at **80.61 tokens/s** |
| Best old 11k cold-prefill result | `gemma4:e4b-nvfp4` at **4205.55 tokens/s** |
| Apple Silicon warning | `mxfp8` was slower than Q4_K_M despite larger files |
| MLX warning | MLX helped prefill, not decode, in the clean Gemma BF16 pair |

## Raw Results

- [Ollama 0.30.6 installed-model comparison](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Retested MTP draft-4 comparison](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Retested MTP draft-8 comparison](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Historical 10-model report](./REPORT.md)

## Final Decision

Use `qwen3.6:35b-a3b-mtp-q4_K_M` with the default `draft_num_predict=4` unless you have a specific reason not to. Choose `gemma4:26b-nvfp4` only when you specifically want Gemma. Choose `qwen3.6:27b-mtp-q4_K_M` only when the smaller 17 GB Qwen file matters more than speed. Do not force MTP draft tokens to `8`.
