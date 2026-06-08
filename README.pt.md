# M5 Pro LLM Benchmark — Escolha de modelos no Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · **Português** · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Este repo mede o throughput de LLMs locais em **Apple M5 Pro / 64 GB** com [Ollama](https://ollama.com). Os resultados atuais usam **Ollama 0.30.6** e os modelos instalados nesta máquina. A suíte antiga com 10 modelos fica como referência histórica em [REPORT.md](./REPORT.md).

## Escolha rápida

| Situação | Escolha | Motivo |
|---|---|---|
| Qwen local mais rápido hoje | `qwen3.6:35b-a3b-mtp-q4_K_M` com `draft_num_predict=4` | Melhor velocidade medida: até **87.97 tokens/s** |
| Você quer um modelo Gemma | `gemma4:26b-nvfp4` | Melhor Gemma no run atual dos modelos instalados |
| Você precisa do Qwen MTP menor | `qwen3.6:27b-mtp-q4_K_M` com `draft_num_predict=4` | Arquivo de 17 GB, mas muito mais lento que o 35B-a3B MTP |
| Você está ajustando MTP | Mantenha o padrão `draft_num_predict=4` | Forçar `8` foi mais lento nos dois modelos MTP |
| Você só quer a comparação histórica completa | Leia [REPORT.md](./REPORT.md) | Comparação original de quantização e MLX com 10 modelos |

## Resultados atuais

| Modelo | Melhor uso | Tamanho do arquivo do modelo (GB) | Decodificação short (tokens/s) | Decodificação long (tokens/s) | Decodificação contexto 11k (tokens/s) | Fonte |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Qwen atual mais rápido | 22 | **86.79** | **87.97** | **79.94** | Reteste MTP, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Alternativa Qwen sem MTP | 21 | 64.57 | 64.58 | 59.15 | Run de modelos instalados |
| `gemma4:26b-nvfp4` | Gemma atual mais rápido | 16 | 59.16 | 58.33 | 49.07 | Run de modelos instalados |
| `qwen3.6:27b-mtp-q4_K_M` | Qwen MTP menor | 17 | 17.41 | 20.62 | 15.77 | Reteste MTP, draft 4 |
| `gemma4:31b-nvfp4` | Não é escolha por velocidade | 20 | 10.41 | 10.27 | 9.14 | Run de modelos instalados |

## Tokens de rascunho MTP

| Modelo | Tokens de rascunho MTP (`draft_num_predict`) | Decodificação short (tokens/s) | Decodificação long (tokens/s) | Decodificação contexto 11k (tokens/s) | Mudança vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**Conclusão MTP:** não force `draft_num_predict=8` nesta máquina. Use o padrão do modelo, `4`.

## Modelos testados na atualização atual

| Família | Modelo | Parâmetros | Quantização | Tamanho do arquivo do modelo (GB) | Notas |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Vencedor atual |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Baseline MTP menor |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Vencedor histórico, mais lento agora |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Melhor resultado Gemma atual |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | Lento neste run |

## Forma do benchmark

| Caso | Tamanho do prompt (tokens) | Limite de geração (`num_predict`, tokens) | Amostras |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| Contexto 11k | cerca de 11,000 com `num_ctx=16384` | 256 | 3 |

A velocidade de decodificação usa `eval_count / eval_duration` reportado pelo servidor Ollama. High Power foi fixado com `pmset powermode=2`, e `caffeinate -dimsu` foi usado durante os runs.

## Notas históricas

A suíte completa original testou 10 modelos no Ollama 0.21/run2. Use-a como referência histórica para arquitetura, quantização e MLX:

| Achado histórico | Resultado |
|---|---|
| Melhor short decode antigo | `qwen3.6:35b-a3b-coding-nvfp4` com **80.61 tokens/s** |
| Melhor 11k cold prefill antigo | `gemma4:e4b-nvfp4` com **4205.55 tokens/s** |
| Aviso em Apple Silicon | `mxfp8` foi mais lento que Q4_K_M apesar de arquivos maiores |
| Aviso sobre MLX | No par limpo Gemma BF16, MLX ajudou prefill, não decode |

## Resultados brutos

- [Comparação de modelos instalados no Ollama 0.30.6](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Reteste MTP draft-4](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Reteste MTP draft-8](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Relatório histórico de 10 modelos](./REPORT.md)

## Decisão final

Use `qwen3.6:35b-a3b-mtp-q4_K_M` com o padrão `draft_num_predict=4`, salvo se houver um motivo específico para não usar. Escolha `gemma4:26b-nvfp4` apenas quando quiser Gemma. Escolha `qwen3.6:27b-mtp-q4_K_M` apenas quando o arquivo de 17 GB importar mais que velocidade. Não force os tokens de rascunho MTP para `8`.
