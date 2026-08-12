# Ollama Speed Report — `nemotron-3.5-lightning:30b-mlx`

- Started: `2026-08-11T22:57:06-07:00`
- Finished: `2026-08-11T22:58:22-07:00`
- Architecture: `nemotron_h`
- Parameters: `32.9B`
- Publisher-stated active parameters: approximately [`3B`](https://ollama.com/library/nemotron-3.5-lightning:30b-mlx)
- Expert routing: `128` routed experts, `6` selected per token, plus `1` shared expert
- Quantization: `nvfp4`
- Model file size: `22.00 GB`
- Ollama: `0.32.9`
- Speculative decoding: built-in one-layer MTP, managed automatically by Ollama
- First cold-start load time: `6.93 s`

## Methodology

- Measurements use Ollama's streaming `/api/generate` endpoint. Decode throughput is calculated from the server-reported `eval_count / eval_duration`.
- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`, which measures prefill throughput.
- `e2e tokens/s` = `eval_count / total_duration`, including prompt prefill.
- TTFT is the wall-clock time until the client receives the first streamed token.
- Every test uses `temperature=0`, `seed=42`, and `keep_alive=10m`, with a warmup before sampling.
- The xlong test forces `num_ctx=16384` and uses an approximately 11k-token prompt to measure long-context prefill and decode throughput.
- Later samples of an identical prompt can hit Ollama's KV cache. Prompt-evaluation means can therefore include cached samples; use each prompt group's first uncached sample for cold-prefill analysis.
- All 12 measured samples exhausted their generation limit while emitting reasoning only (`thinking_chars > 0`, `response_chars = 0`). The report therefore ranks raw decode throughput, not time to a completed visible answer.
- During the formal run, Ollama's adaptive MTP path drafted 425 tokens and accepted 310 (72.9%); the controller frequently selected depth 0 when drafting was not beneficial.

## Summary

| Metric | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| Decode tokens/s (mean ± stdev) | 68.36 ± 2.75 | 70.01 ± 0.78 | 64.69 ± 2.42 |
| Decode tokens/s (median / max) | 68.81 / 70.87 | 70.44 / 70.51 | 66.23 / 66.56 |
| Prompt evaluation tokens/s (mean, including cached samples) | 2279030.13 | 7297488.35 | 324703498.78 |
| End-to-end tokens/s (mean) | 68.00 | 69.20 | 51.96 |
| TTFT seconds (mean) | 0.048 | 0.116 | 2.143 |
| Samples (n) | 5 | 4 | 3 |
| Mean prompt_eval_count | - | - | 11321 tokens |

## Per-Sample Results

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | PASS | 63.34 | 1006.66 | 62.66 | 0.071 | 32 | 256 | 1182 | 0 | 4.09 |
| 2 | short | PASS | 68.01 | 2363018.76 | 67.73 | 0.044 | 32 | 256 | 1235 | 0 | 3.78 |
| 3 | short | PASS | 68.81 | 2685239.57 | 68.53 | 0.041 | 32 | 256 | 1141 | 0 | 3.74 |
| 4 | short | PASS | 70.87 | 3490782.15 | 70.62 | 0.041 | 32 | 256 | 1227 | 0 | 3.63 |
| 5 | short | PASS | 70.78 | 2855103.50 | 70.47 | 0.043 | 32 | 256 | 1169 | 0 | 3.63 |
| 6 | long | PASS | 70.43 | 618.31 | 67.89 | 0.307 | 160 | 512 | 2207 | 0 | 7.54 |
| 7 | long | PASS | 68.65 | 4814.63 | 68.23 | 0.073 | 160 | 512 | 2165 | 0 | 7.51 |
| 8 | long | PASS | 70.45 | 14065934.07 | 70.32 | 0.043 | 160 | 512 | 2175 | 0 | 7.28 |
| 9 | long | PASS | 70.51 | 15118586.41 | 70.38 | 0.040 | 160 | 512 | 2231 | 0 | 7.28 |
| 10 | xlong | PASS | 61.27 | 1822.65 | 24.59 | 6.285 | 11321 | 256 | 1158 | 0 | 10.42 |
| 11 | xlong | PASS | 66.23 | 259211.31 | 65.09 | 0.096 | 11321 | 256 | 1160 | 0 | 3.94 |
| 12 | xlong | PASS | 66.56 | 973849462.37 | 66.22 | 0.049 | 11321 | 256 | 1130 | 0 | 3.88 |
