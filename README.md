# M5 Pro LLM Benchmark — Ollama Leaderboard

**Languages**: **English** · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

This repository benchmarks local LLM throughput with [Ollama](https://ollama.com) on an **Apple M5 Pro with 64 GB of unified memory**. The leaderboard below is the primary project summary and is updated whenever a new model benchmark is added.

## Current Leaderboard

**Last updated:** August 10, 2026, with `muse-glimmer:30b-mlx` on Ollama 0.32.7.

Overall rank is determined by the arithmetic mean of short, long, and 11k-context decode throughput. Only the latest retained successful run for each model is included.

| Rank | Model | Ollama | Short | Long | 11k context | Overall average | Evidence |
|---:|---|---:|---:|---:|---:|---:|---|
| **1** | `qwen3.6:35b-a3b-mtp-q4_K_M` | 0.30.6 | **86.79** | **87.97** | **79.94** | **84.90** | [draft-4 report](./results/ollama_0.30.6_update/mtp_draft4/qwen3.6_35b-a3b-mtp-q4_K_M.md) |
| **2** | `qwen3.6:35b-a3b-coding-nvfp4` | 0.30.6 | 64.57 | 64.58 | 59.15 | 62.77 | [installed-model report](./results/ollama_0.30.6_update/installed/qwen3.6_35b-a3b-coding-nvfp4.md) |
| **3** | `gemma4:26b-nvfp4` | 0.30.6 | 59.16 | 58.33 | 49.07 | 55.52 | [installed-model report](./results/ollama_0.30.6_update/installed/gemma4_26b-nvfp4.md) |
| **4** | `muse-glimmer:30b-mlx` | 0.32.7 | 24.05 | 26.30 | 24.74 | 25.03 | [latest report](./results/ollama_0.32.7_update/installed/muse-glimmer_30b-mlx.md) |
| **5** | `qwen3.6:27b-mtp-q4_K_M` | 0.30.6 | 17.41 | 20.62 | 15.77 | 17.93 | [draft-4 report](./results/ollama_0.30.6_update/mtp_draft4/qwen3.6_27b-mtp-q4_K_M.md) |
| **6** | `gemma4:31b-nvfp4` | 0.30.6 | 10.41 | 10.27 | 9.14 | 9.94 | [installed-model report](./results/ollama_0.30.6_update/installed/gemma4_31b-nvfp4.md) |

All throughput values are decode tokens/s from Ollama's server-reported `eval_count / eval_duration`; higher is better.

> **Comparability note:** `muse-glimmer:30b-mlx` was measured on Ollama 0.32.7, while the other current leaderboard entries were measured on 0.30.6. The table provides a practical latest-results ranking, but strict apples-to-apples conclusions should only compare rows measured on the same Ollama version.

The leaderboard measures throughput, not response quality, reasoning accuracy, feature support, or memory efficiency. The older Ollama 0.21 suite remains available in [REPORT.md](./REPORT.md) but is not mixed into the current ranking.

## Current Takeaways

- **Fastest overall:** `qwen3.6:35b-a3b-mtp-q4_K_M` with the model-default `draft_num_predict=4`.
- **Fastest non-MTP Qwen:** `qwen3.6:35b-a3b-coding-nvfp4`.
- **Fastest Gemma:** `gemma4:26b-nvfp4`.
- **Latest model tested:** `muse-glimmer:30b-mlx`, currently ranked fourth for decode throughput.
- **MTP setting:** keep `draft_num_predict=4`; forcing `8` was slower for both tested MTP models.

## Latest Benchmark — `muse-glimmer:30b-mlx`

| Property | Result |
|---|---|
| Ollama | 0.32.7 |
| Architecture / parameters | `muse_glimmer` / 32.3B |
| Quantization / file size | nvfp4 / 21 GB |
| Model-default `draft_num_predict` | 15, not overridden |
| Cold-start load time | 2.95 s |
| Successful measured samples | 12 / 12 |
| First uncached 11k prefill | 363.43 tokens/s |
| First uncached 11k TTFT | 30.32 s |

Later identical-prompt samples hit Ollama's KV cache, so cached prompt-evaluation values are preserved as raw evidence but are not treated as cold-prefill measurements. See the [full result](./results/ollama_0.32.7_update/installed/00_comparison.md) and [raw JSON](./results/ollama_0.32.7_update/installed/muse-glimmer_30b-mlx.json).

## Benchmark Protocol

| Case | Prompt size | Generation limit (`num_predict`) | Samples |
|---|---|---:|---:|
| Short | Fixed short prompt; 26–72 tokens depending on tokenizer | 256 | 5 |
| Long | Fixed design prompt; 149–194 tokens depending on tokenizer | 512 | 4 |
| 11k context | Approximately 10.8k–11.1k tokens with `num_ctx=16384` | 256 | 3 |

- Test options: `temperature=0`, `seed=42`, and `keep_alive=10m`.
- Power mode: `pmset powermode=2` on AC power.
- Sleep prevention: `caffeinate -dimsu` for the full run.
- Decode throughput: server-reported `eval_count / eval_duration`.
- Prefill throughput: server-reported `prompt_eval_count / prompt_eval_duration`.
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

- [Ollama 0.32.7 `muse-glimmer:30b-mlx` result](./results/ollama_0.32.7_update/installed/00_comparison.md)
- [Ollama 0.30.6 installed-model comparison](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Ollama 0.30.6 MTP draft-4 comparison](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Ollama 0.30.6 MTP draft-8 comparison](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Historical Ollama 0.21 report](./REPORT.md)

## Leaderboard Maintenance

Whenever a new benchmark is added:

1. Add or replace that model's row in **Current Leaderboard** using its latest successful run.
2. Recalculate `Overall average`, sort the table, and update the rank numbers.
3. Update the `Last updated` line and preserve the Ollama version for every row.
4. Link each leaderboard row to its supporting report.
5. Keep benchmark reports and the main README in English unless another language is explicitly requested.
