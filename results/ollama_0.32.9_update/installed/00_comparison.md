# Ollama Speed Comparison (High Power Mode + 16k Context)

- Report generated: `2026-08-11T22:58:22-07:00`
- Host: Darwin 27.0.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama: `0.32.9`
- Ollama URL: `http://localhost:11434`
- System power mode: `pmset powermode=2` (High Power, AC power)
- Sleep prevention: `caffeinate -dimsu` enabled for the full run
- Test settings: `temperature=0` `seed=42` `keep_alive=10m`
- short/long use the default num_ctx; xlong forces `num_ctx=16384`
- The model uses a built-in one-layer MTP speculative head; Ollama adaptively selected the draft depth during the run.
- All measured samples exhausted their generation limit in the reasoning channel, so these values rank decode throughput rather than time to a completed visible answer.

## Primary Results — Decode, Prompt Evaluation, and TTFT

| Model | Parameters | Quantization | Size (GB) | Cold load (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `nemotron-3.5-lightning:30b-mlx` | 32.9B | nvfp4 | 22.00 | 6.93 | 68.36 | 70.01 | 64.69 | 2279030.13 | 7297488.35 | 324703498.78 | 0.048 | 0.116 | 2.14 |

> `gen` and `prompt` values are tokens/s (higher is better); `TTFT` is seconds (lower is better).

## Rankings

### Short-Prompt Decode Throughput

| Rank | Model | short gen tok/s |
|---:|---|---:|
| 1 | `nemotron-3.5-lightning:30b-mlx` | 68.36 |

### Long-Prompt Decode Throughput

| Rank | Model | long gen tok/s |
|---:|---|---:|
| 1 | `nemotron-3.5-lightning:30b-mlx` | 70.01 |

### Xlong (16k) Decode Throughput

| Rank | Model | xlong gen tok/s | Mean prompt tokens |
|---:|---|---:|---:|
| 1 | `nemotron-3.5-lightning:30b-mlx` | 64.69 | 11321 |

## Metric Definitions

- **gen tok/s**: Decode throughput from the server-reported `eval_count / eval_duration`.
- **prompt tok/s**: Prefill throughput, measuring how quickly the model processes the input prompt.
- **TTFT**: Client-observed wall-clock time until the first streamed token arrives.
- **Cold load**: Time for the first forward pass after loading the model, using server `load_duration` or wall time.
- **xlong**: Long-context prefill and decode using an approximately 11k-token synthetic corpus with `num_ctx=16384`.
