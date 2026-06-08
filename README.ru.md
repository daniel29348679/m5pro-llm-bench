# M5 Pro LLM Benchmark — выбор моделей Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · **Русский** · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Этот репозиторий измеряет пропускную способность локальных LLM на **Apple M5 Pro / 64 GB** через [Ollama](https://ollama.com). Текущие результаты используют **Ollama 0.30.6** и модели, установленные на этой машине. Старая полная серия из 10 моделей сохранена как историческая база в [REPORT.md](./REPORT.md).

## Быстрый выбор

| Ситуация | Выбор | Причина |
|---|---|---|
| Самый быстрый текущий локальный Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M` с `draft_num_predict=4` | Лучшая измеренная скорость decode: до **87.97 tokens/s** |
| Нужна модель Gemma | `gemma4:26b-nvfp4` | Самая быстрая Gemma в текущем запуске установленных моделей |
| Нужен меньший Qwen MTP | `qwen3.6:27b-mtp-q4_K_M` с `draft_num_predict=4` | Файл 17 GB, но намного медленнее 35B-a3B MTP |
| Вы настраиваете MTP | Оставить стандарт `draft_num_predict=4` | Принудительное `8` замедлило обе MTP-модели |
| Нужна только старая полная сравнительная таблица | Читать [REPORT.md](./REPORT.md) | Там исходное сравнение 10 моделей по quantization и MLX |

## Текущие результаты

| Модель | Лучшее применение | Размер файла модели (GB) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | Источник |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Самый быстрый текущий Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP retest, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Qwen fallback без MTP | 21 | 64.57 | 64.58 | 59.15 | Запуск установленных моделей |
| `gemma4:26b-nvfp4` | Самая быстрая текущая Gemma | 16 | 59.16 | 58.33 | 49.07 | Запуск установленных моделей |
| `qwen3.6:27b-mtp-q4_K_M` | Меньший Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP retest, draft 4 |
| `gemma4:31b-nvfp4` | Не выбор для скорости | 20 | 10.41 | 10.27 | 9.14 | Запуск установленных моделей |

## MTP draft tokens

| Модель | MTP draft tokens (`draft_num_predict`) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | Изменение относительно draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**Вывод по MTP:** не форсируйте `draft_num_predict=8` на этой машине. Используйте стандарт модели `4`.

## Модели, протестированные в текущем обновлении

| Семейство | Модель | Параметры | Quantization | Размер файла модели (GB) | Заметки |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Текущий победитель |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Меньший MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Исторический победитель, сейчас медленнее |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Лучший текущий результат Gemma |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | Медленно в этом запуске |

## Форма benchmark

| Сценарий | Длина prompt (tokens) | Лимит генерации (`num_predict`, tokens) | Количество запусков |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | около 11,000 с `num_ctx=16384` | 256 | 3 |

Скорость decode — это `eval_count / eval_duration`, как сообщает сервер Ollama. High Power был зафиксирован через `pmset powermode=2`, во время запусков использовался `caffeinate -dimsu`.

## Исторические заметки

Исходная полная серия протестировала 10 моделей на Ollama 0.21/run2. Используйте ее для исторического сравнения архитектуры, quantization и MLX:

| Историческое наблюдение | Результат |
|---|---|
| Лучший старый short decode | `qwen3.6:35b-a3b-coding-nvfp4` — **80.61 tokens/s** |
| Лучший старый 11k cold prefill | `gemma4:e4b-nvfp4` — **4205.55 tokens/s** |
| Предупреждение для Apple Silicon | `mxfp8` был медленнее Q4_K_M, несмотря на больший размер файлов |
| Предупреждение по MLX | В чистой паре Gemma BF16 MLX помогал prefill, но не decode |

## Сырые результаты

- [Сравнение установленных моделей Ollama 0.30.6](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 retest](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 retest](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Исторический отчет по 10 моделям](./REPORT.md)

## Итоговое решение

Используйте `qwen3.6:35b-a3b-mtp-q4_K_M` со стандартным `draft_num_predict=4`, если нет конкретной причины выбрать другое. Выбирайте `gemma4:26b-nvfp4` только если нужен именно Gemma. Выбирайте `qwen3.6:27b-mtp-q4_K_M` только если файл 17 GB важнее скорости. Не форсируйте MTP draft tokens на `8`.
