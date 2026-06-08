# M5 Pro LLM Benchmark — Elección de modelos en Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · **Español** · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Este repo mide el rendimiento de LLM locales en **Apple M5 Pro / 64 GB** con [Ollama](https://ollama.com). Los resultados actuales usan **Ollama 0.30.6** y los modelos instalados en esta máquina. La suite antigua de 10 modelos queda como evidencia histórica en [REPORT.md](./REPORT.md).

## Elección rápida

| Situación | Elige | Motivo |
|---|---|---|
| Qwen local más rápido hoy | `qwen3.6:35b-a3b-mtp-q4_K_M` con `draft_num_predict=4` | Mejor velocidad medida: hasta **87.97 tokens/s** |
| Quieres un modelo Gemma | `gemma4:26b-nvfp4` | Mejor Gemma en la corrida actual de modelos instalados |
| Necesitas el Qwen MTP más pequeño | `qwen3.6:27b-mtp-q4_K_M` con `draft_num_predict=4` | Archivo de 17 GB, pero mucho más lento que el 35B-a3B MTP |
| Estás ajustando MTP | Mantén el valor por defecto `draft_num_predict=4` | Forzar `8` fue más lento en ambos modelos MTP |
| Solo quieres la comparación histórica completa | Lee [REPORT.md](./REPORT.md) | Ahí está la comparación original de cuantización y MLX de 10 modelos |

## Resultados actuales

| Modelo | Mejor uso | Tamaño del archivo (GB) | Decodificación short (tokens/s) | Decodificación long (tokens/s) | Decodificación contexto 11k (tokens/s) | Fuente |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Qwen más rápido actual | 22 | **86.79** | **87.97** | **79.94** | Retest MTP, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Alternativa Qwen sin MTP | 21 | 64.57 | 64.58 | 59.15 | Modelos instalados |
| `gemma4:26b-nvfp4` | Gemma más rápido actual | 16 | 59.16 | 58.33 | 49.07 | Modelos instalados |
| `qwen3.6:27b-mtp-q4_K_M` | Qwen MTP más pequeño | 17 | 17.41 | 20.62 | 15.77 | Retest MTP, draft 4 |
| `gemma4:31b-nvfp4` | No es opción de velocidad | 20 | 10.41 | 10.27 | 9.14 | Modelos instalados |

## Tokens de borrador MTP

| Modelo | Tokens MTP de borrador (`draft_num_predict`) | Decodificación short (tokens/s) | Decodificación long (tokens/s) | Decodificación contexto 11k (tokens/s) | Cambio vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**Conclusión MTP:** no fuerces `draft_num_predict=8` en esta máquina. Usa el valor por defecto `4`.

## Modelos probados en la actualización actual

| Familia | Modelo | Parámetros | Cuantización | Tamaño del archivo (GB) | Notas |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Ganador actual |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Baseline MTP más pequeño |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Ganador histórico, más lento ahora |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Mejor Gemma actual |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | Lento en esta corrida |

## Forma del benchmark

| Caso | Longitud del prompt (tokens) | Límite de generación (`num_predict`, tokens) | Muestras |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| Contexto 11k | cerca de 11,000 con `num_ctx=16384` | 256 | 3 |

La velocidad de decodificación usa `eval_count / eval_duration` reportado por el servidor Ollama. High Power se fijó con `pmset powermode=2`, y se usó `caffeinate -dimsu` durante las pruebas.

## Notas históricas

La suite completa original probó 10 modelos en Ollama 0.21/run2. Sigue siendo útil para comparar arquitectura, cuantización y MLX:

| Hallazgo histórico | Resultado |
|---|---|
| Mejor resultado antiguo en short decode | `qwen3.6:35b-a3b-coding-nvfp4` con **80.61 tokens/s** |
| Mejor resultado antiguo en 11k cold prefill | `gemma4:e4b-nvfp4` con **4205.55 tokens/s** |
| Advertencia en Apple Silicon | `mxfp8` fue más lento que Q4_K_M aunque los archivos eran más grandes |
| Advertencia sobre MLX | En el par limpio Gemma BF16, MLX ayudó a prefill, no a decode |

## Resultados crudos

- [Comparación de modelos instalados en Ollama 0.30.6](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Retest MTP draft-4](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Retest MTP draft-8](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Reporte histórico de 10 modelos](./REPORT.md)

## Decisión final

Usa `qwen3.6:35b-a3b-mtp-q4_K_M` con el valor por defecto `draft_num_predict=4`, salvo que tengas una razón concreta para no hacerlo. Elige `gemma4:26b-nvfp4` solo si necesitas Gemma. Elige `qwen3.6:27b-mtp-q4_K_M` solo si el archivo de 17 GB importa más que la velocidad. No fuerces los tokens MTP de borrador a `8`.
