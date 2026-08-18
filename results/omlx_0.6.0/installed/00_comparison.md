# oMLX 0.6.0 Qwen3.8 Benchmark

- Report generated: `2026-08-17T16:28:21-07:00`
- Host: Darwin 27.0.0 / Apple M5 Pro / 64 GB
- Runtime / API: `oMLX 0.6.0` / `http://127.0.0.1:8000`
- Power mode: `2` (2 = High Power on AC)
- Sleep prevention: `caffeinate -dimsu` enabled for the full formal run
- Protocol: canonical 5/4/3 samples with 256/512/256 output-token limits

## Primary Result

| Model | MTP | Short | Long | 11k context | Overall average |
|---|---|---:|---:|---:|---:|
| `mlx-community/Qwen3.8-27B-4bit` | external drafter, block 3 | 26.28 | 22.81 | 19.88 | 22.99 |

> Decode throughput uses oMLX's server-reported streaming usage metrics. The prompts, output limits, sample counts, power mode, and xlong context cap match the repository's established suite; runtime instrumentation and quantization still differ from Ollama rows.

## Evidence

- Successful samples: `12 / 12`
- MTP acceptance: `1836 / 3416` (`53.7%`)
- Cold load: `2.23 s`
- [Full per-sample report](./qwen3.8_27b-4bit_mtp.md)
