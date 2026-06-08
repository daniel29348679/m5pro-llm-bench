# M5 Pro LLM Benchmark — Ollama 0.30.6 모델 선택

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · **한국어** · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

이 repo는 **Apple M5 Pro / 64 GB**에서 [Ollama](https://ollama.com) 로컬 LLM 처리량을 측정합니다. 현재 결과는 **Ollama 0.30.6**과 이 머신에 설치된 모델을 사용합니다. 이전 10개 모델 전체 비교는 [REPORT.md](./REPORT.md)에 역사 데이터로 남겨 두었습니다.

## 빠른 선택

| 상황 | 선택 | 이유 |
|---|---|---|
| 현재 가장 빠른 로컬 Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M`, `draft_num_predict=4` | 최대 실측 디코드 속도 **87.97 tokens/s** |
| Gemma 모델이 필요함 | `gemma4:26b-nvfp4` | 현재 설치된 Gemma 중 가장 빠름 |
| 더 작은 Qwen MTP가 필요함 | `qwen3.6:27b-mtp-q4_K_M`, `draft_num_predict=4` | 17 GB 파일이지만 35B-a3B MTP보다 훨씬 느림 |
| MTP를 조정 중 | 모델 기본값 `draft_num_predict=4` 유지 | `8`로 강제하면 두 MTP 모델 모두 느려짐 |
| 예전 전체 비교만 필요함 | [REPORT.md](./REPORT.md) | 원래 10개 모델 양자화와 MLX 비교가 있음 |

## 현재 결과

| 모델 | 적합한 용도 | 모델 파일 크기 (GB) | Short 디코드 (tokens/s) | Long 디코드 (tokens/s) | 11k 컨텍스트 디코드 (tokens/s) | 데이터 출처 |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 현재 가장 빠른 Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP 재측정, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | 비 MTP Qwen 대안 | 21 | 64.57 | 64.58 | 59.15 | 설치 모델 측정 |
| `gemma4:26b-nvfp4` | 현재 가장 빠른 Gemma | 16 | 59.16 | 58.33 | 49.07 | 설치 모델 측정 |
| `qwen3.6:27b-mtp-q4_K_M` | 더 작은 Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP 재측정, draft 4 |
| `gemma4:31b-nvfp4` | 속도 우선 선택 아님 | 20 | 10.41 | 10.27 | 9.14 | 설치 모델 측정 |

## MTP 예측 tokens

| 모델 | MTP 예측 tokens (`draft_num_predict`) | Short 디코드 (tokens/s) | Long 디코드 (tokens/s) | 11k 컨텍스트 디코드 (tokens/s) | draft 4 대비 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP 결론:** 이 머신에서는 `draft_num_predict=8`을 강제하지 말고 모델 기본값 `4`를 사용하세요.

## 현재 업데이트에서 측정한 모델

| 패밀리 | 모델 | 파라미터 | 양자화 | 모델 파일 크기 (GB) | 메모 |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | 현재 승자 |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | 더 작은 MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | 역사적 승자, 현재 run에서는 느려짐 |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | 현재 Gemma 최고 결과 |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | 이번 run에서는 느림 |

## 벤치마크 조건

| 케이스 | Prompt 길이 (tokens) | 생성 제한 (`num_predict`, tokens) | 샘플 수 |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | 약 11,000, `num_ctx=16384` | 256 | 3 |

디코드 속도는 Ollama server가 보고한 `eval_count / eval_duration`입니다. High Power는 `pmset powermode=2`로 고정했고, 측정 중에는 `caffeinate -dimsu`를 사용했습니다.

## 역사 데이터 요약

원래 전체 비교는 Ollama 0.21/run2에서 10개 모델을 측정했습니다. 아키텍처, 양자화, MLX 비교에는 역사적 기준으로 사용하세요.

| 역사적 발견 | 결과 |
|---|---|
| 이전 short 디코드 최고 | `qwen3.6:35b-a3b-coding-nvfp4`, **80.61 tokens/s** |
| 이전 11k cold prefill 최고 | `gemma4:e4b-nvfp4`, **4205.55 tokens/s** |
| Apple Silicon 주의점 | `mxfp8`은 파일이 더 큰데도 Q4_K_M보다 느렸음 |
| MLX 주의점 | 깨끗한 Gemma BF16 비교에서 MLX는 prefill에는 도움, decode에는 도움 없음 |

## 원본 결과

- [Ollama 0.30.6 설치 모델 비교](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 재측정](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 재측정](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [역사 10개 모델 리포트](./REPORT.md)

## 최종 결론

특별한 제약이 없다면 `qwen3.6:35b-a3b-mtp-q4_K_M`를 사용하고 기본 `draft_num_predict=4`를 유지하세요. Gemma가 꼭 필요할 때만 `gemma4:26b-nvfp4`를 선택하세요. 22 GB 파일이 부담스럽고 17 GB 파일 크기가 속도보다 중요할 때만 `qwen3.6:27b-mtp-q4_K_M`를 선택하세요. MTP 예측 tokens를 `8`로 강제하지 마세요.
