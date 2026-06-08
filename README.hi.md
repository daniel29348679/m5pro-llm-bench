# M5 Pro LLM Benchmark — Ollama 0.30.6 मॉडल चयन

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · **हिन्दी**

यह repo **Apple M5 Pro / 64 GB** पर [Ollama](https://ollama.com) के साथ local LLM throughput मापता है। मौजूदा नतीजे **Ollama 0.30.6** और इस मशीन पर installed models से लिए गए हैं। पुराना 10-model full suite ऐतिहासिक reference के रूप में [REPORT.md](./REPORT.md) में रखा गया है।

## जल्दी चुनाव

| स्थिति | चुनें | कारण |
|---|---|---|
| अभी सबसे तेज local Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M` with `draft_num_predict=4` | सबसे अच्छा measured decode speed: **87.97 tokens/s** तक |
| आपको Gemma model चाहिए | `gemma4:26b-nvfp4` | current installed-model run में सबसे तेज Gemma |
| आपको छोटा Qwen MTP चाहिए | `qwen3.6:27b-mtp-q4_K_M` with `draft_num_predict=4` | 17 GB file, लेकिन 35B-a3B MTP से काफी धीमा |
| आप MTP tune कर रहे हैं | model default `draft_num_predict=4` रखें | `8` force करने से दोनों MTP models धीमे हुए |
| आपको सिर्फ पुराना full comparison चाहिए | [REPORT.md](./REPORT.md) पढ़ें | original 10-model quantization और MLX comparison वहीं है |

## मौजूदा नतीजे

| Model | Best use | Model file size (GB) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | Data source |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | अभी सबसे तेज Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP retest, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | non-MTP Qwen fallback | 21 | 64.57 | 64.58 | 59.15 | Installed-model run |
| `gemma4:26b-nvfp4` | अभी सबसे तेज Gemma | 16 | 59.16 | 58.33 | 49.07 | Installed-model run |
| `qwen3.6:27b-mtp-q4_K_M` | छोटा Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP retest, draft 4 |
| `gemma4:31b-nvfp4` | speed pick नहीं | 20 | 10.41 | 10.27 | 9.14 | Installed-model run |

## MTP draft tokens

| Model | MTP draft tokens (`draft_num_predict`) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | draft 4 से बदलाव |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP निष्कर्ष:** इस machine पर `draft_num_predict=8` force न करें। model default `4` इस्तेमाल करें।

## Current update में test किए गए models

| Family | Model | Parameters | Quantization | Model file size (GB) | Notes |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | current winner |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | छोटा MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | historical winner, current run में slower |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | best current Gemma result |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | इस run में धीमा |

## Benchmark shape

| Case | Prompt length (tokens) | Generation limit (`num_predict`, tokens) | Samples |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | करीब 11,000 with `num_ctx=16384` | 256 | 3 |

Decode speed Ollama server-reported `eval_count / eval_duration` है। High Power को `pmset powermode=2` से lock किया गया, और runs के दौरान `caffeinate -dimsu` इस्तेमाल हुआ।

## Historical notes

Original full suite ने Ollama 0.21/run2 पर 10 models test किए थे। Architecture, quantization, और MLX comparison के लिए उसे historical reference की तरह इस्तेमाल करें:

| Historical finding | Result |
|---|---|
| पुराना best short decode | `qwen3.6:35b-a3b-coding-nvfp4` at **80.61 tokens/s** |
| पुराना best 11k cold prefill | `gemma4:e4b-nvfp4` at **4205.55 tokens/s** |
| Apple Silicon warning | `mxfp8` बड़े files के बावजूद Q4_K_M से धीमा था |
| MLX warning | clean Gemma BF16 pair में MLX ने prefill में मदद की, decode में नहीं |

## Raw results

- [Ollama 0.30.6 installed-model comparison](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 retest](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 retest](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Historical 10-model report](./REPORT.md)

## अंतिम निष्कर्ष

जब तक कोई खास constraint न हो, `qwen3.6:35b-a3b-mtp-q4_K_M` इस्तेमाल करें और default `draft_num_predict=4` रखें। `gemma4:26b-nvfp4` सिर्फ तब चुनें जब Gemma चाहिए। `qwen3.6:27b-mtp-q4_K_M` सिर्फ तब चुनें जब 17 GB file size speed से ज्यादा महत्वपूर्ण हो। MTP draft tokens को `8` पर force न करें।
