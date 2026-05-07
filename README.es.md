# Benchmark de LLM en M5 Pro — Ollama, MLX y el Impacto de la Cuantización

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · **Español** · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Este repositorio mide la velocidad de **10 LLMs locales en Apple M5 Pro / 64 GB** mediante [Ollama](https://ollama.com), comparando:

- **MoE vs dense** en velocidad de decodificación (Qwen3.6 35b-a3b vs 35b dense)
- **Formatos de cuantización** y su impacto distinto en prefill vs decodificación (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **BF16 etiquetado MLX vs BF16 ordinario** en rendimiento de prefill
- Impacto del **modo High Power de macOS** sobre el throughput

> **TL;DR**: En M5 Pro, **tamaño del modelo > cuantización > optimización de arquitectura**. La decodificación está limitada por ancho de banda de memoria; el prefill por kernel de cuantización — siguen reglas completamente distintas. Datos completos en [REPORT.md](./REPORT.md).

## Modelos probados (10)

| Familia | Modelo | Parámetros | Cuant. | Tamaño |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B active) | mxfp8 | 37 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B active) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## Resultados principales

### Velocidad de decodificación short prompt (media de 5 muestras)

| Rank | Modelo | tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | `qwen3.6:27b-coding-mxfp8` | 9.89 |

### Velocidad de prefill cold xlong (~11k tokens)

| Rank | Modelo | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## Hallazgos clave

### 1. Decodificación y prefill tienen cuellos de botella distintos

- **Decodificación = limitada por ancho de banda de memoria**: los pesos atraviesan la memoria una vez por token. Las variantes 4-bit de Gemma4 (e4b, e4b-nvfp4) decodifican a ~68 tok/s; BF16 (it-bf16, mlx-bf16) a ~28 tok/s. **2.4× más lento corresponde exactamente a 2× tamaño de pesos.**
- **Prefill = limitado por compute y kernel de cuantización**: mismo 4-bit, mismo 9.6 GB, e4b vs e4b-nvfp4 decodifican casi idénticamente — pero el cold xlong prefill de nvfp4 es **5.7× más rápido** (4206 vs 736 tok/s).

### 2. nvfp4 es el ganador integral en este M5 Pro

- En la misma arquitectura, nvfp4 decodifica 33–65% más rápido, con archivos 39–43% más pequeños.
- En Gemma4, nvfp4 no ayuda a decodificar pero acelera prefill ~5×.
- Conclusión: **siempre elegir nvfp4 si está disponible**.

### 3. mxfp8 es una trampa en Apple Silicon

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) es **más lento que el Q4_K_M original (11.82 tok/s)** a pesar de ser 1.8× más grande — mxfp8 no tiene aceleración nativa en el backend Metal.

### 4. La etiqueta MLX no ayuda a decodificar pero acelera prefill ~5×

`gemma4:e4b-mlx-bf16` y `gemma4:e4b-it-bf16` decodifican idénticamente a ~28 tok/s, pero el cold xlong prefill es **3721 vs 782 tok/s (4.8×)**. Elegir variantes MLX solo cuando dominan los prompts largos.

### 5. MoE rinde bien en M5 Pro

`qwen3.6:35b-a3b` (3B activo) decodifica a **~80 tok/s**, dos veces más rápido que el equivalente dense `qwen3.6:35b` (41.68). MoE solo recorre 3B de pesos por token — perfectamente alineado con el cuello de botella de ancho de banda.

### 6. El modo de energía de macOS es decisivo para modelos dense

| Modelo | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Los benchmarks reproducibles deben fijar High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. La penalización por contexto largo de 16k es pequeña

Los 10 modelos pierden solo **4–10%** de velocidad de decodificación al pasar de short → 11k token xlong. M5 Pro / 64 GB tiene margen de sobra para 16k de contexto.

## Entorno de prueba

- **Hardware**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB de memoria unificada
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **Energía**: AC, `pmset powermode=2` (High Power)
- **Antisuspensión**: `caffeinate -dimsu` activo durante toda la prueba
- **Python**: 3.14

## Metodología

Ver [`bench.py`](./bench.py). Diseño clave:

- Para cada modelo: `keep_alive=0` para descargar → cold-start → warmup → medir
- Todos con `temperature=0` `seed=42` `keep_alive=10m` para reproducibilidad
- Tres longitudes de prompt:
  - **short** × 5: 26~32 tokens → `num_predict=256`
  - **long** × 4: 149~156 tokens → `num_predict=512`
  - **xlong** × 3: ~11k tokens → `num_predict=256`, `num_ctx=16384` forzado
- Tok/s de decodificación = `eval_count / eval_duration` reportado por servidor. **No afectado por hits de KV cache.**
- Tok/s de prefill toma solo la **primera ejecución** de long/xlong (cold prefill) — Ollama reutiliza KV cache para prompts repetidos e infla absurdamente los números (100k+ tok/s).

## Reproducir

```bash
# 1. Bloquear High Power
sudo pmset -a powermode 2

# 2. Verificar ollama
curl -s http://localhost:11434/api/version

# 3. Pull modelos
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. Antisuspensión + medir
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

# 5. Generar reporte
python3 render_report.py
```

## Estructura del repositorio

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # Este archivo en 12 idiomas
├── REPORT.md                        # Reporte de comparación completo
├── bench.py                         # Script de medición
├── render_report.py                 # Postprocesamiento (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 modelos Qwen3.6 — datos brutos + resumen
    └── gemma4_*.json / .md          # 4 modelos Gemma4 — datos brutos + resumen
```

## Limitaciones de medición conocidas

- **TTFT alto en short prompt de Gemma4 (1.6–5.7 s)**: desproporcionado con el tiempo de prefill (32 / ~1400 ≈ 0.02 s). Probablemente procesamiento del chat-template gemma3-style en Ollama.
- **TTFT xlong de Gemma4 muestra 0.00 s — bug de detección de streaming en cliente**: el primer chunk de gemma4 no contiene cadenas `response`/`thinking`, así que el detector de first-token del cliente no se dispara. Calcular TTFT real con `xlong wall - eval_count / xlong_gen`.
- **Reutilización de KV cache de Ollama**: prompts idénticos en la 2ª ejecución inflan los números de prefill ridículamente. El reporte solo toma cold prefill (run 1).

## Licencia

CC BY-SA 4.0. Citar, modificar, redistribuir libremente con atribución.

## Contribuir

Otros propietarios de M5 Pro probando modelos adicionales (Llama 3.3, DeepSeek, Phi 4, …) bienvenidos a abrir PR o issue. Si tienes hardware diferente (M4 / M3 Max / Studio), un dataset igual sería muy valioso.
