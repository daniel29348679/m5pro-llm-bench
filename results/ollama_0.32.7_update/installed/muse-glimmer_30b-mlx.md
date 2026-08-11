# Ollama Speed Report — `muse-glimmer:30b-mlx`

- Started: `2026-08-10T18:57:59-07:00`
- Finished: `2026-08-10T19:01:21-07:00`
- Architecture: `muse_glimmer`
- Parameters: `32.3B`
- Quantization: `nvfp4`
- Model file size: `21.00 GB`
- Ollama: `0.32.7`
- Model-default `draft_num_predict`: `15` (not overridden)
- First cold-start load time: `2.95 s`

## Methodology

- Measurements use Ollama's streaming `/api/generate` endpoint. Decode throughput is calculated from the server-reported `eval_count / eval_duration`.
- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`, which measures prefill throughput.
- `e2e tokens/s` = `eval_count / total_duration`, including prompt prefill.
- TTFT is the wall-clock time until the client receives the first streamed token.
- Every test uses `temperature=0`, `seed=42`, and `keep_alive=10m`, with a warmup before sampling.
- The xlong test forces `num_ctx=16384` and uses an approximately 14k-token prompt to measure long-context prefill and decode throughput.
- Later samples of an identical prompt can hit Ollama's KV cache. Prompt-evaluation means therefore include cached samples; use each prompt group's first uncached sample for cold-prefill analysis.

## Summary

| Metric | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| Decode tokens/s (mean ± stdev) | 24.05 ± 0.29 | 26.30 ± 0.25 | 24.74 ± 0.24 |
| Decode tokens/s (median / max) | 23.98 / 24.50 | 26.20 / 26.71 | 24.69 / 25.05 |
| Prompt evaluation tokens/s (mean, including cached samples) | 8002053.77 | 15205501.65 | 378607105.81 |
| End-to-end tokens/s (mean) | 23.97 | 26.06 | 18.48 |
| TTFT seconds (mean) | 0.126 | 0.307 | 10.264 |
| Samples (n) | 5 | 4 | 3 |
| Mean prompt_eval_count | - | - | 10837 tokens |

## Per-Sample Results

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | PASS | 23.65 | 10799460.03 | 23.56 | 0.133 | 72 | 256 | 934 | 301 | 10.87 |
| 2 | short | PASS | 24.50 | 9142857.14 | 24.43 | 0.126 | 72 | 256 | 934 | 301 | 10.48 |
| 3 | short | PASS | 23.98 | 6995724.83 | 23.91 | 0.124 | 72 | 256 | 934 | 301 | 10.71 |
| 4 | short | PASS | 24.21 | 6400000.00 | 24.13 | 0.125 | 72 | 256 | 934 | 301 | 10.61 |
| 5 | short | PASS | 23.90 | 6672226.86 | 23.82 | 0.123 | 72 | 256 | 934 | 301 | 10.75 |
| 6 | long | PASS | 26.10 | 317.35 | 25.27 | 0.833 | 194 | 512 | 2391 | 0 | 20.26 |
| 7 | long | PASS | 26.09 | 24767011.36 | 26.05 | 0.140 | 194 | 512 | 2391 | 0 | 19.66 |
| 8 | long | PASS | 26.30 | 17504285.84 | 26.25 | 0.129 | 194 | 512 | 2391 | 0 | 19.51 |
| 9 | long | PASS | 26.71 | 18550392.04 | 26.67 | 0.126 | 194 | 512 | 2391 | 0 | 19.20 |
| 10 | xlong | PASS | 24.69 | 363.43 | 6.36 | 30.323 | 10837 | 256 | 1409 | 0 | 40.25 |
| 11 | xlong | PASS | 24.47 | 105171.13 | 24.13 | 0.289 | 10837 | 256 | 1420 | 0 | 10.62 |
| 12 | xlong | PASS | 25.05 | 1135715782.85 | 24.95 | 0.180 | 10837 | 256 | 1420 | 0 | 10.28 |
