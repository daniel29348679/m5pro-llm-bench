# oMLX Speed Report — `mlx-community/Qwen3.8-27B-4bit`

- Started: `2026-08-17T16:24:56-07:00`
- Finished: `2026-08-17T16:28:21-07:00`
- Runtime: `oMLX 0.6.0`
- Architecture / parameters: `qwen3_5` / `27.8B`
- Quantization: `4-bit affine`
- Target model size: `16.68 GB`
- Model context length: `262144`
- First cold-start load time: `2.23 s`
- MTP drafter: `mlx-community/Qwen3.8-27B-MTP-4bit` (`250.9 MB`, block size `3`)

## Methodology

- This run reuses the repository's canonical short, long, and xlong prompts without modification.
- Measurements use oMLX's streaming OpenAI-compatible `/v1/chat/completions` endpoint with `stream_options.include_usage=true`.
- Decode and prefill throughput use oMLX's server-reported `generation_tokens_per_second` and `prompt_tokens_per_second` fields; TTFT is also retained from the client clock.
- Every sample uses `temperature=0` and `seed=42`, with a cold load and warmup before the measured samples.
- The protocol matches the existing suite: short 5 x 256-token limits, long 4 x 512-token limits, and xlong 3 x 256-token limits. The xlong phase temporarily sets the model context cap to 16384 and restores it afterward.
- Repeated xlong prompts can hit oMLX's block prefix cache. Cached-token counts are preserved per sample; use the first uncached sample for cold-prefill analysis.
- The target checkpoint does not contain embedded `mtp.*` tensors. Speculative decoding uses the separately installed Qwen3.8 MTP drafter shown above.

## Summary

| Metric | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| Decode tokens/s (mean ± stdev) | 26.28 ± 0.07 | 22.81 ± 0.10 | 19.88 ± 0.64 |
| Decode tokens/s (median / max) | 26.31 / 26.35 | 22.80 / 22.96 | 20.32 / 20.35 |
| Prompt evaluation tokens/s (mean) | 97.50 | 211.47 | 2702.83 |
| End-to-end tokens/s (mean) | 23.35 | 21.93 | 12.99 |
| Client TTFT seconds (mean) | 0.699 | 0.906 | 11.992 |
| Samples (n) | 5 | 4 | 3 |
| Mean prompt tokens | - | - | 11106 tokens |

## MTP Results

- Formal samples with MTP logs: `12 / 12`
- Draft tokens accepted: `1836 / 3416` (`53.7%`)
- Total decode rounds: `1708`; emitted tokens: `3551`

## Per-Sample Results

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | client TTFT | prompt_n | cached_n | eval_n | MTP accepted | finish | wall |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | short | PASS | 26.35 | 97.41 | 23.40 | 0.700s | 68 | 0 | 146 | 82/128 (64.1%) | stop | 6.24s |
| 2 | short | PASS | 26.31 | 98.26 | 23.40 | 0.694s | 68 | 0 | 146 | 82/128 (64.1%) | stop | 6.24s |
| 3 | short | PASS | 26.31 | 97.10 | 23.36 | 0.702s | 68 | 0 | 146 | 82/128 (64.1%) | stop | 6.25s |
| 4 | short | PASS | 26.26 | 97.22 | 23.32 | 0.701s | 68 | 0 | 146 | 82/128 (64.1%) | stop | 6.26s |
| 5 | short | PASS | 26.16 | 97.50 | 23.25 | 0.699s | 68 | 0 | 146 | 82/128 (64.1%) | stop | 6.28s |
| 6 | long | PASS | 22.96 | 218.93 | 22.09 | 0.875s | 191 | 0 | 512 | 261/502 (52.0%) | length | 23.18s |
| 7 | long | PASS | 22.85 | 214.79 | 21.97 | 0.892s | 191 | 0 | 512 | 261/502 (52.0%) | length | 23.30s |
| 8 | long | PASS | 22.74 | 207.67 | 21.84 | 0.922s | 191 | 0 | 512 | 261/502 (52.0%) | length | 23.44s |
| 9 | long | PASS | 22.69 | 204.51 | 21.80 | 0.936s | 191 | 0 | 512 | 261/502 (52.0%) | length | 23.50s |
| 10 | xlong | PASS | 18.97 | 368.32 | 5.86 | 30.177s | 11106 | 0 | 256 | 122/268 (45.5%) | length | 43.67s |
| 11 | xlong | PASS | 20.35 | 3717.99 | 16.44 | 3.013s | 11106 | 10240 | 256 | 130/250 (52.0%) | length | 15.59s |
| 12 | xlong | PASS | 20.32 | 4022.17 | 16.67 | 2.784s | 11106 | 10240 | 256 | 130/250 (52.0%) | length | 15.38s |
