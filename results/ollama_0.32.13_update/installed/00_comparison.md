# Ollama Speed Comparison (High Power Mode + 16k Context)

- Report generated: `2026-08-15T20:57:34-07:00`
- Host: Darwin 27.0.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama: `0.32.13`
- Ollama URL: `http://localhost:11434`
- System power mode: `pmset powermode=2` (High Power, AC power)
- Sleep prevention: `caffeinate -dimsu` enabled for the full run
- Test settings: `temperature=0` `seed=42` `keep_alive=10m`
- short/long use the server-default `num_ctx=131072`; xlong forces `num_ctx=16384`
- The checkpoint includes a native one-layer MTP head; Ollama selected the draft depth automatically during the run.
- All 12 measured samples exhausted their generation limit, so these values rank raw decode throughput rather than time to a completed answer.

## Primary Results — Decode, Prompt Evaluation, and TTFT

| Model | Parameters | Quantization | Size (GB) | Cold load (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.8:27b-mlx` | 27.8B | nvfp4 | 18.00 | 1.86 | 34.25 | 32.79 | 34.38 | 1598209.99 | 5607337.54 | 278391179.61 | 0.147 | 0.263 | 9.27 |

> `gen` and `prompt` values are tokens/s (higher is better); `TTFT` is seconds (lower is better).

> Later samples of an identical prompt hit Ollama's KV cache, so the prompt means include cached results. The first uncached long and xlong prefill rates were `322.53` and `405.56` tokens/s, respectively, and the first xlong TTFT was `27.45 s`.

## Rankings

### Short-Prompt Decode Throughput

| Rank | Model | short gen tok/s |
|---:|---|---:|
| 1 | `qwen3.8:27b-mlx` | 34.25 |

### Long-Prompt Decode Throughput

| Rank | Model | long gen tok/s |
|---:|---|---:|
| 1 | `qwen3.8:27b-mlx` | 32.79 |

### Xlong (16k) Decode Throughput

| Rank | Model | xlong gen tok/s | Mean prompt tokens |
|---:|---|---:|---:|
| 1 | `qwen3.8:27b-mlx` | 34.38 | 11064 |

## Metric Definitions

- **gen tok/s**: Decode throughput from the server-reported `eval_count / eval_duration`.
- **prompt tok/s**: Prefill throughput, measuring how quickly the model processes the input prompt.
- **TTFT**: Client-observed wall-clock time until the first streamed token arrives.
- **Cold load**: Time for the first forward pass after loading the model, using server `load_duration` or wall time.
- **xlong**: Long-context prefill and decode using an approximately 11k-token synthetic corpus with `num_ctx=16384`.
