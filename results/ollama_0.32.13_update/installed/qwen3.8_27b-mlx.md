# Ollama Speed Report — `qwen3.8:27b-mlx`

- Started: `2026-08-15T20:54:58-07:00`
- Finished: `2026-08-15T20:57:34-07:00`
- Architecture: `qwen3_5`
- Parameters: `27.8B`
- Quantization: `nvfp4`
- Model file size: `18.00 GB`
- Ollama: `0.32.13`
- Model context length: `262144`
- Native MTP checkpoint: [one hidden layer](https://ollama.com/library/qwen3.8:27b-mlx/blobs/af908e4b42c0) (`mtp_num_hidden_layers=1`) with 15 `mtp.*` tensors
- Speculative decoding: inline MTP, managed automatically by Ollama
- First cold-start load time: `1.86 s`

## Methodology

- Measurements use Ollama's streaming `/api/generate` endpoint. Decode throughput is calculated from the server-reported `eval_count / eval_duration`.
- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`, which measures prefill throughput.
- `e2e tokens/s` = `eval_count / total_duration`, including prompt prefill.
- TTFT is the wall-clock time until the client receives the first streamed token.
- Every test uses `temperature=0`, `seed=42`, and `keep_alive=10m`, with a warmup before sampling.
- The short and long tests used the server-default `num_ctx=131072`; the xlong test forces `num_ctx=16384` and uses an approximately 11k-token prompt to measure long-context prefill and decode throughput.
- Later samples of an identical prompt can hit Ollama's KV cache. Prompt-evaluation means can therefore include cached samples; use each prompt group's first uncached sample for cold-prefill analysis.
- All 12 measured samples exhausted their generation limit. Six emitted reasoning only (`response_chars = 0`), while six emitted both reasoning and a visible response, so the report ranks raw decode throughput rather than time to a completed answer.
- Across the 12 formal samples, Ollama's adaptive MTP path drafted 4,303 tokens and accepted 2,608 (60.6%), with a maximum draft depth of 5.

## Summary

| Metric | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| Decode tokens/s (mean ± stdev) | 34.25 ± 0.25 | 32.79 ± 1.29 | 34.38 ± 1.21 |
| Decode tokens/s (median / max) | 34.38 / 34.52 | 33.24 / 34.04 | 34.45 / 35.83 |
| Prompt evaluation tokens/s (mean, including cached samples) | 1598209.99 | 5607337.54 | 278391179.61 |
| End-to-end tokens/s (mean) | 34.06 | 32.46 | 25.13 |
| TTFT seconds (mean) | 0.147 | 0.263 | 9.270 |
| Samples (n) | 5 | 4 | 3 |
| Mean prompt_eval_count | - | - | 11064 tokens |

## Per-Sample Results

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | PASS | 34.17 | 396.17 | 33.75 | 0.175 | 26 | 256 | 444 | 762 | 7.59 |
| 2 | short | PASS | 34.40 | 2026026.65 | 34.26 | 0.142 | 26 | 256 | 444 | 761 | 7.47 |
| 3 | short | PASS | 34.52 | 2087012.36 | 34.38 | 0.140 | 26 | 256 | 444 | 761 | 7.45 |
| 4 | short | PASS | 34.38 | 2026026.65 | 34.25 | 0.141 | 26 | 256 | 444 | 761 | 7.48 |
| 5 | short | PASS | 33.80 | 1851588.09 | 33.67 | 0.139 | 26 | 256 | 444 | 761 | 7.60 |
| 6 | long | PASS | 33.44 | 322.53 | 32.41 | 0.596 | 149 | 512 | 2313 | 0 | 15.80 |
| 7 | long | PASS | 30.65 | 2240.97 | 30.47 | 0.172 | 149 | 512 | 1868 | 279 | 16.80 |
| 8 | long | PASS | 34.04 | 10426142.33 | 33.97 | 0.144 | 149 | 512 | 2352 | 0 | 15.08 |
| 9 | long | PASS | 33.04 | 12000644.33 | 32.98 | 0.142 | 149 | 512 | 2352 | 0 | 15.53 |
| 10 | xlong | PASS | 34.45 | 405.56 | 7.37 | 27.452 | 11064 | 256 | 1157 | 0 | 34.76 |
| 11 | xlong | PASS | 35.83 | 154265.34 | 35.30 | 0.211 | 11064 | 256 | 1211 | 0 | 7.26 |
| 12 | xlong | PASS | 32.87 | 835018867.92 | 32.73 | 0.148 | 11064 | 256 | 1233 | 0 | 7.83 |
