# M5 Pro LLM 벤치마크 — Ollama, MLX 및 양자화의 영향

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · **한국어** · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

이 레포는 **Apple M5 Pro / 64 GB** 에서 [Ollama](https://ollama.com) 로 10개의 로컬 LLM 속도를 측정합니다. 중점 비교 항목:

- **MoE 와 dense** 의 디코딩 속도 차이 (Qwen3.6 35b-a3b vs 35b dense)
- **양자화 형식** 이 prefill 과 디코딩에 미치는 다른 영향 (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX 태그 BF16 vs 일반 BF16** 의 prefill 성능 차이
- **macOS High Power 모드** 가 처리량에 미치는 결정적 영향

> **TL;DR**: M5 Pro 에서는 **모델 크기 > 양자화 > 아키텍처 최적화**. 디코딩은 메모리 대역폭 병목, prefill 은 양자화 커널 병목 — 완전히 다른 규칙. 자세한 데이터는 [REPORT.md](./REPORT.md) 참고.

## 측정 대상 모델 (10개)

| 시리즈 | 모델 | 파라미터 | 양자화 | 모델 크기 |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B active) | mxfp8 | 37 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B active) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## 주요 결과

### Short prompt 디코딩 속도 순위 (5회 샘플 평균)

| 순위 | 모델 | tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | `qwen3.6:27b-coding-mxfp8` | 9.89 |

### xlong (~11k 토큰) 콜드 prefill 속도

| 순위 | 모델 | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | 🍎 `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## 핵심 발견

### 1. 디코딩과 Prefill 의 병목이 다름

- **디코딩은 메모리 대역폭 병목**: 토큰 1개 생성마다 모델 weights 가 메모리를 한 번 통과해야 함. Gemma4 e4b 의 4-bit (e4b, e4b-nvfp4) 는 모두 ~68 tok/s, BF16 (it-bf16, mlx-bf16) 은 모두 ~28 tok/s. **2.4배 느린 것은 weight 크기 2배에 정확히 대응**.
- **Prefill 은 연산과 양자화 커널 병목**: 같은 4-bit, 같은 9.6 GB 인 e4b 와 e4b-nvfp4 의 디코딩은 거의 같지만, nvfp4 의 콜드 xlong prefill 은 **5.7배 빠름** (4206 vs 736 tok/s).

### 2. nvfp4 가 이 M5 Pro 에서 만능 승자

- 같은 아키텍처에서 nvfp4 디코딩 +33%~+65%, 모델 파일 -39%~-43%.
- Gemma4 에서는 nvfp4 가 디코딩에는 거의 도움이 안 되지만, prefill 은 ~5배 빨라짐.
- 결론: **nvfp4 버전이 있으면 무조건 nvfp4**.

### 3. mxfp8 은 Apple Silicon 의 함정

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) 은 **원본 Q4_K_M (11.82 tok/s) 보다 느리고**, 파일은 1.8배 큼 — mxfp8 은 Metal backend 의 네이티브 가속이 없음.

### 4. MLX 태그는 디코딩에 도움 안 되지만 prefill 은 ~5배 빠름

🍎 `gemma4:e4b-mlx-bf16` 과 `gemma4:e4b-it-bf16` 의 디코딩은 모두 ~28 tok/s 이지만, 콜드 xlong prefill 은 **3721 vs 782 tok/s (4.8배)**. 긴 prompt 시나리오일 때만 MLX 버전 선택.

### 5. MoE 는 M5 Pro 에서 매우 유용

`qwen3.6:35b-a3b` (3B active) 는 디코딩 **~80 tok/s**, 같은 35B 급 dense (`qwen3.6:35b` 41.68) 의 2배. MoE 추론 시 weights 는 3B 만 메모리를 통과 — 메모리 대역폭 병목 규칙에 정확히 부합.

### 6. macOS 전원 모드는 dense 모델에 큰 영향

| 모델 | Automatic (run1) | High Power (run2) | 증가율 |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**재현 가능한 벤치마크는 High Power 를 잠가야 함**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k 긴 컨텍스트 페널티는 작음

10개 모델 모두 short → 11k 토큰 xlong 디코딩 속도 저하는 **4–10%** 에 불과. Apple M5 Pro / 64 GB 는 16k 컨텍스트에도 여유가 충분.

## 테스트 환경

- **하드웨어**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB 통합 메모리
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **전원**: AC, `pmset powermode=2` (High Power)
- **수면 방지**: `caffeinate -dimsu` 측정 내내 활성
- **Python**: 3.14

## 측정 방법

전체 스크립트는 [`bench.py`](./bench.py) 참고. 핵심 설계:

- 각 모델: `keep_alive=0` 언로드 → cold-start → warmup → 측정
- 모두 `temperature=0` `seed=42` `keep_alive=10m` 으로 재현성 보장
- 3가지 prompt 길이:
  - **short** × 5: 26~32 토큰 → `num_predict=256`
  - **long** × 4: 149~156 토큰 → `num_predict=512`
  - **xlong** × 3: ~11k 토큰 → `num_predict=256`, `num_ctx=16384` 강제
- 디코딩 tok/s = 서버가 보고하는 `eval_count / eval_duration`, **KV cache hit 영향 없음**
- Prefill tok/s 는 각 모델 long/xlong 의 **첫 회**(콜드 prefill)만 사용 — Ollama 가 동일 prompt 에 대해 KV cache 를 재사용하여 2번째부터의 prefill 수치가 비정상적으로 큼 (100k+ tok/s).

## 재현 단계

```bash
# 1. High Power 잠금
sudo pmset -a powermode 2

# 2. ollama 서비스 확인
curl -s http://localhost:11434/api/version

# 3. 모델 풀
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. 수면 방지 + 벤치마크 실행
caffeinate -dimsu -t 18000 &
python3 bench.py \
  --models qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
           qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
           qwen3.6:35b-a3b-coding-nvfp4 \
           gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4 \
  --output-dir results \
  --short-runs 5 --long-runs 4 --xlong-runs 3 \
  --short-predict 256 --long-predict 512 --xlong-predict 256 \
  --xlong-num-ctx 16384

# 5. 보고서 생성
python3 render_report.py
```

## 파일 구조

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # 12개 언어 버전
├── REPORT.md                        # 전체 비교 보고서
├── bench.py                         # 측정 스크립트
├── render_report.py                 # 후처리 (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6개 Qwen3.6 모델 — 원본 + 요약
    └── gemma4_*.json / .md          # 4개 Gemma4 모델 — 원본 + 요약
```

## 알려진 측정 제한

- **Gemma4 시리즈의 short prompt TTFT 가 높음 (1.6–5.7s)**: prefill 시간 (32 / ~1400 ≈ 0.02s) 과 비례 안 됨. Ollama 측의 gemma3-style chat template 처리일 가능성.
- **Gemma4 xlong TTFT 가 0.00s 로 표시되는 것은 클라이언트 측 스트리밍 감지 버그**: gemma4 의 첫 청크는 `response`/`thinking` 문자열을 포함하지 않아 클라이언트의 first-token 감지기가 트리거되지 않음. 실제 TTFT 는 `xlong wall - eval_count / xlong_gen` 로 역산.
- **Ollama 의 KV cache 재사용**: 동일 prompt 의 2번째부터는 prefill 이 거의 무료. 본 프로젝트의 prefill 값은 각 그룹의 첫 회만 사용.

## 라이선스

CC BY-SA 4.0. 인용, 수정, 재배포 자유 (출처 표기).

## 기여

다른 M5 Pro 사용자가 추가 모델 (Llama 3.3, DeepSeek, Phi 4 등) 을 시도하고 싶다면 PR 또는 issue 환영. 하드웨어가 다르다면 (M4 / M3 Max / Studio) 같은 설정의 데이터를 측정해 주시면 매우 가치 있음.
