# Benchmark de LLM no M5 Pro — Ollama, MLX e o Impacto da Quantização

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · **Português** · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Este repositório mede a velocidade de **10 LLMs locais no Apple M5 Pro / 64 GB** via [Ollama](https://ollama.com), comparando:

- **MoE vs dense** em velocidade de decodificação (Qwen3.6 35b-a3b vs 35b dense)
- **Formatos de quantização** e seu impacto distinto em prefill vs decodificação (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **BF16 com tag MLX vs BF16 comum** em desempenho de prefill
- Impacto do **modo High Power do macOS** sobre o throughput

> **TL;DR**: No M5 Pro, **tamanho do modelo > quantização > otimização de arquitetura**. Decodificação está limitada pela largura de banda da memória; prefill pelo kernel de quantização — regras completamente diferentes. Dados completos em [REPORT.md](./REPORT.md).

## Modelos testados (10)

| Família | Modelo | Parâmetros | Quant. | Tamanho |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B ativo) | mxfp8 | 37 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B ativo) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## Resultados principais

### Velocidade de decodificação short prompt (média de 5 amostras)

| Rank | Modelo | tok/s |
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

### Velocidade de prefill cold xlong (~11k tokens)

| Rank | Modelo | prefill tok/s |
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

## Conclusões principais

### 1. Decodificação e prefill têm gargalos diferentes

- **Decodificação = limitada pela largura de banda da memória**: pesos atravessam a memória uma vez por token. As variantes 4-bit do Gemma4 (e4b, e4b-nvfp4) decodificam todas a ~68 tok/s; BF16 (it-bf16, mlx-bf16) a ~28 tok/s. **2.4× mais lento corresponde exatamente a 2× tamanho dos pesos.**
- **Prefill = limitado por compute e kernel de quantização**: mesmo 4-bit, mesmo 9.6 GB, e4b vs e4b-nvfp4 decodificam identicamente — mas o cold xlong prefill do nvfp4 é **5.7× mais rápido** (4206 vs 736 tok/s).

### 2. nvfp4 é o vencedor abrangente neste M5 Pro

- Na mesma arquitetura, nvfp4 decodifica 33–65% mais rápido, com arquivos 39–43% menores.
- No Gemma4, nvfp4 não ajuda a decodificação, mas acelera prefill ~5×.
- Conclusão: **sempre escolher nvfp4 quando disponível**.

### 3. mxfp8 é uma armadilha no Apple Silicon

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) é **mais lento que o Q4_K_M original (11.82 tok/s)** apesar de ser 1.8× maior — mxfp8 não tem aceleração nativa no backend Metal.

### 4. A tag MLX não ajuda a decodificação mas acelera prefill ~5×

🍎 `gemma4:e4b-mlx-bf16` e `gemma4:e4b-it-bf16` decodificam identicamente a ~28 tok/s, mas o cold xlong prefill é **3721 vs 782 tok/s (4.8×)**. Escolher variantes MLX apenas quando prompts longos dominam.

### 5. MoE compensa no M5 Pro

`qwen3.6:35b-a3b` (3B ativo) decodifica a **~80 tok/s**, duas vezes mais rápido que o dense equivalente `qwen3.6:35b` (41.68). MoE atravessa apenas 3B de pesos pela memória por token — perfeitamente alinhado ao gargalo de banda.

### 6. O modo de energia do macOS é decisivo para modelos dense

| Modelo | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Benchmarks reproduzíveis devem travar High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. Penalidade de contexto longo de 16k é pequena

Todos os 10 modelos perdem apenas **4–10%** de velocidade de decodificação ao passar de short → 11k tokens xlong. M5 Pro / 64 GB tem bastante margem para contexto de 16k.

## Ambiente de teste

- **Hardware**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB de memória unificada
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **Energia**: AC, `pmset powermode=2` (High Power)
- **Anti-suspensão**: `caffeinate -dimsu` ativo o tempo todo
- **Python**: 3.14

## Metodologia

Ver [`bench.py`](./bench.py). Design chave:

- Por modelo: `keep_alive=0` para descarregar → cold-start → warmup → medir
- Todos com `temperature=0` `seed=42` `keep_alive=10m` para reprodutibilidade
- Três comprimentos de prompt:
  - **short** × 5: 26~32 tokens → `num_predict=256`
  - **long** × 4: 149~156 tokens → `num_predict=512`
  - **xlong** × 3: ~11k tokens → `num_predict=256`, `num_ctx=16384` forçado
- Decodificação tok/s = `eval_count / eval_duration` reportado pelo servidor. **Não afetado por hits de KV cache.**
- Prefill tok/s pega apenas a **primeira execução** de long/xlong (cold prefill) — Ollama reutiliza KV cache para prompts repetidos e infla absurdamente os números (100k+ tok/s).

## Reproduzir

```bash
# 1. Travar High Power
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

# 4. Anti-suspensão + medir
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

# 5. Gerar relatório
python3 render_report.py
```

## Estrutura do repo

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # Este arquivo em 12 idiomas
├── REPORT.md                        # Relatório de comparação completo
├── bench.py                         # Script de medição
├── render_report.py                 # Pós-processamento (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 modelos Qwen3.6 — dados brutos + resumo
    └── gemma4_*.json / .md          # 4 modelos Gemma4 — dados brutos + resumo
```

## Limitações de medição conhecidas

- **TTFT alto em short prompt para Gemma4 (1.6–5.7 s)**: desproporcional ao tempo de prefill (32 / ~1400 ≈ 0.02 s). Provavelmente processamento de chat-template gemma3-style no lado Ollama.
- **TTFT xlong do Gemma4 mostra 0.00 s — bug de detecção de streaming no cliente**: o primeiro chunk do gemma4 não contém strings `response`/`thinking`, então o detector de first-token do cliente não dispara. Calcular TTFT real com `xlong wall - eval_count / xlong_gen`.
- **Reuso de KV cache do Ollama**: prompts idênticos na 2ª execução inflam absurdamente os números de prefill. O relatório só pega cold prefill (run 1).

## Licença

CC BY-SA 4.0. Citar, modificar, redistribuir livremente com atribuição.

## Contribuir

Outros donos de M5 Pro testando modelos adicionais (Llama 3.3, DeepSeek, Phi 4, …) bem-vindos a abrir PR ou issue. Com hardware diferente (M4 / M3 Max / Studio), um dataset equivalente seria muito valioso.
