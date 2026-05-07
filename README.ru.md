# Бенчмарк LLM на M5 Pro — Ollama, MLX и Влияние Квантизации

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · **Русский** · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Этот репозиторий измеряет скорость **10 локальных LLM на Apple M5 Pro / 64 ГБ** через [Ollama](https://ollama.com), сравнивая:

- **MoE и dense** в скорости декодирования (Qwen3.6 35b-a3b vs 35b dense)
- **Форматы квантизации** и их разное влияние на prefill и декодирование (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **BF16 с тегом MLX vs обычный BF16** по производительности prefill
- Влияние **режима macOS High Power** на пропускную способность

> **TL;DR**: На M5 Pro **размер модели > квантизация > оптимизация архитектуры**. Декодирование упирается в пропускную способность памяти; prefill — в quant-ядро. Совершенно разные правила. Полные данные в [REPORT.md](./REPORT.md).

## Тестируемые модели (10)

| Семейство | Модель | Параметры | Квант. | Размер |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 ГБ |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 ГБ |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 ГБ |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 ГБ |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B активных) | mxfp8 | 37 ГБ |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B активных) | nvfp4 | 21 ГБ |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 ГБ |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 ГБ |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 ГБ |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 ГБ |

## Главные результаты

### Скорость декодирования short prompt (среднее из 5 замеров)

| Ранг | Модель | tok/s |
|---:|---|---:|
| 1 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.89 |

### Скорость холодного prefill xlong (~11k токенов)

| Ранг | Модель | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | 🍎 `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | 🍎 `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## Ключевые выводы

### 1. У декодирования и prefill разные узкие места

- **Декодирование = ограничено пропускной способностью памяти**: веса проходят через память один раз на токен. 4-битные варианты Gemma4 (e4b, e4b-nvfp4) декодируют все при ~68 tok/s; BF16 (it-bf16, mlx-bf16) — при ~28 tok/s. **В 2.4 раза медленнее точно соответствует двукратному размеру весов.**
- **Prefill = ограничен compute и quant-ядром**: тот же 4-бит, те же 9.6 ГБ, e4b vs e4b-nvfp4 декодируют идентично — но холодный xlong prefill nvfp4 **в 5.7 раз быстрее** (4206 vs 736 tok/s).

### 2. nvfp4 — универсальный победитель на этом M5 Pro

- В одной архитектуре nvfp4 декодирует на 33–65% быстрее, файлы на 39–43% меньше.
- На Gemma4 nvfp4 не помогает декодированию, но ускоряет prefill ~5×.
- Вывод: **всегда выбирать nvfp4, если доступен**.

### 3. mxfp8 — ловушка на Apple Silicon

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) **медленнее оригинального Q4_K_M (11.82 tok/s)**, хотя в 1.8 раза больше — у mxfp8 нет нативного ускорения на бэкенде Metal.

### 4. Тег MLX не помогает декодированию, но ускоряет prefill ~5×

🍎 `gemma4:e4b-mlx-bf16` и `gemma4:e4b-it-bf16` декодируют идентично при ~28 tok/s, но холодный xlong prefill — **3721 vs 782 tok/s (4.8×)**. Выбирать MLX-варианты только при доминировании длинных промтов.

### 5. MoE окупается на M5 Pro

`qwen3.6:35b-a3b` (3B активных) декодирует при **~80 tok/s**, вдвое быстрее эквивалентного dense `qwen3.6:35b` (41.68). MoE прогоняет через память лишь 3B весов на токен — идеально соответствует ограничению пропускной способности.

### 6. Режим питания macOS критически важен для dense моделей

| Модель | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Воспроизводимые бенчмарки должны фиксировать High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. Штраф за длинный контекст 16k мал

Все 10 моделей теряют лишь **4–10%** скорости декодирования при переходе с short → 11k токенов xlong. У M5 Pro / 64 ГБ много запаса для 16k контекста.

<!-- mlx-caveat:v1 -->
## ⚠️ Уточнение про контрольную группу MLX — прочитать перед цитированием findings 3 и 4

Пять из десяти протестированных моделей — это варианты MLX (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Это влияет на правильное прочтение findings 3 и 4:

- **Finding 3 (mxfp8 — ловушка)**: сравнение это 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs не-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Точная формулировка: **путь MLX-mxfp8 на бэкенде Metal Ollama медленнее, чем базовый путь GGUF Q4_K_M**, несмотря на то, что в 1.8× больше.
- **Finding 4 (тег MLX не помогает decode, но ускоряет prefill)**: только пара gemma4 даёт чистое сравнение «MLX vs не-MLX, тот же BF16» (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Пары qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` *обе* являются MLX, так что контраст nvfp4-vs-mxfp8 там — это **сравнение квантизации внутри MLX**, а не изоляция самого MLX-пути.

Кратко: 🍎 — варианты MLX; единственная по-настоящему чистая пара «MLX vs не-MLX, всё остальное одинаково» в наборе — это пара BF16 у gemma4.

## Окружение тестирования

- **Железо**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 ГБ единая память
- **ОС**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **Питание**: AC, `pmset powermode=2` (High Power)
- **Анти-сон**: `caffeinate -dimsu` активен всё время
- **Python**: 3.14

## Методология

См. [`bench.py`](./bench.py). Ключевой дизайн:

- Для каждой модели: `keep_alive=0` для выгрузки → cold-start → warmup → измерение
- Все с `temperature=0` `seed=42` `keep_alive=10m` для воспроизводимости
- Три длины промта:
  - **short** × 5: 26~32 токенов → `num_predict=256`
  - **long** × 4: 149~156 токенов → `num_predict=512`
  - **xlong** × 3: ~11k токенов → `num_predict=256`, принудительный `num_ctx=16384`
- Декодирование tok/s = `eval_count / eval_duration` от сервера. **Не зависит от хитов KV cache.**
- Prefill tok/s берёт только **первый запуск** long/xlong (холодный prefill) — Ollama переиспользует KV cache для повторных промтов и абсурдно завышает числа (100k+ tok/s).

## Воспроизведение

```bash
# 1. Зафиксировать High Power
sudo pmset -a powermode 2

# 2. Проверить ollama
curl -s http://localhost:11434/api/version

# 3. Скачать модели
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. Анти-сон + измерить
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

# 5. Сгенерировать отчёт
python3 render_report.py
```

## Структура репо

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # Этот файл на 12 языках
├── REPORT.md                        # Полный отчёт сравнения
├── bench.py                         # Скрипт измерения
├── render_report.py                 # Постобработка (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 моделей Qwen3.6 — сырые данные + сводка
    └── gemma4_*.json / .md          # 4 модели Gemma4 — сырые данные + сводка
```

## Известные ограничения измерений

- **Высокий TTFT для short prompt у Gemma4 (1.6–5.7 с)**: непропорционален времени prefill (32 / ~1400 ≈ 0.02 с). Вероятно, обработка чат-шаблона gemma3-style на стороне Ollama.
- **xlong TTFT у Gemma4 показывает 0.00 с — баг детекции стрима на клиенте**: первый чанк gemma4 не содержит строк `response`/`thinking`, поэтому детектор first-token клиента не срабатывает. Реальный TTFT вычислять как `xlong wall - eval_count / xlong_gen`.
- **Переиспользование KV cache в Ollama**: одинаковые промты на 2-м запуске абсурдно завышают числа prefill. Отчёт берёт только холодный prefill (run 1).

## Лицензия

CC BY-SA 4.0. Цитировать, изменять, перераспространять свободно с указанием авторства.

## Контрибуция

Другие владельцы M5 Pro, тестирующие дополнительные модели (Llama 3.3, DeepSeek, Phi 4, …), могут открыть PR или issue. Если у вас другое железо (M4 / M3 Max / Studio), аналогичный набор данных был бы очень ценен.
