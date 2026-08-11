# `muse-glimmer:30b-mlx` Ollama Speed Benchmark (High Power Mode + 16k Context)

- Report generated: `2026-08-10T19:01:21-07:00`
- Host: Darwin 27.0.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama: `0.32.7`
- Ollama URL: `http://localhost:11434`
- System power mode: `pmset powermode=2` (High Power, AC power)
- Sleep prevention: `caffeinate -dimsu` enabled for the full run
- Test settings: `temperature=0` `seed=42` `keep_alive=10m`
- Model-default `draft_num_predict`: `15` (not overridden)
- short/long use the default num_ctx; xlong forces `num_ctx=16384`

## Primary Results — Decode, Prompt Evaluation, and TTFT

| Model | Parameters | Quantization | Size (GB) | Cold load (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `muse-glimmer:30b-mlx` | 32.3B | nvfp4 | 21.00 | 2.95 | 24.05 | 26.30 | 24.74 | 8002053.77 | 15205501.65 | 378607105.81 | 0.126 | 0.307 | 10.26 |

> `gen` and `prompt` values are tokens/s (higher is better); `TTFT` is seconds (lower is better).

> Later samples of an identical prompt can hit Ollama's KV cache, so the prompt means include cached results. The first uncached long and xlong prefill rates were `317.35` and `363.43` tokens/s, respectively, and the first xlong TTFT was `30.32 s`.

## Rankings

### Short-Prompt Decode Throughput

| Rank | Model | short gen tok/s |
|---:|---|---:|
| 1 | `muse-glimmer:30b-mlx` | 24.05 |

### Long-Prompt Decode Throughput

| Rank | Model | long gen tok/s |
|---:|---|---:|
| 1 | `muse-glimmer:30b-mlx` | 26.30 |

### Xlong (16k) Decode Throughput

| Rank | Model | xlong gen tok/s | Mean prompt tokens |
|---:|---|---:|---:|
| 1 | `muse-glimmer:30b-mlx` | 24.74 | 10837 |

## Metric Definitions

- **gen tok/s**: Decode throughput from the server-reported `eval_count / eval_duration`.
- **prompt tok/s**: Prefill throughput, measuring how quickly the model processes the input prompt.
- **TTFT**: Client-observed wall-clock time until the first streamed token arrives.
- **Cold load**: Time for the first forward pass after loading the model, using server `load_duration` or wall time.
- **xlong**: Long-context prefill and decode using an approximately 14k-token synthetic corpus with `num_ctx=16384`.
