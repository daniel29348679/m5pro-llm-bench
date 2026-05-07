# Ollama 速度報告 — 🍎 `qwen3.6:27b-coding-mxfp8`

- 開始: `2026-05-06T18:49:45-07:00`
- 結束: `2026-05-06T18:57:25-07:00`
- 架構: `qwen3_5`
- 參數量: `27.4B`
- 量化格式: `mxfp8`
- 模型檔大小: `31.00 GB`
- 第一次冷啟動載入時間: `2.86 s`

## 量測說明

- 透過 Ollama `/api/generate` 串流 API 量測，溫度 0、`seed=42`、`keep_alive=10m`，每模型 cold-start + warmup 後才取樣。
- **生成 tokens/s** = `eval_count / eval_duration`（伺服器回報），純解碼速度，cache 命中時仍準確。
- **prompt tokens/s** = `prompt_eval_count / prompt_eval_duration`（prefill 速度）。
- ⚠️ Ollama 對相同 prompt 會重複使用 KV cache，第 2 次起的 prefill 幾乎免費。本報告把 prefill 拆成「冷啟（run 1）」與「快取命中（run 2+）」兩列，避免平均值被污染。
- xlong 測試強制 `num_ctx=16384`，prompt 約 11064 tokens（~14k words 合成語料）。

## 摘要 — 生成速度（tokens/s，cache 命中不影響）

| 指標 | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| 生成 tokens/s（mean ± stdev） | 9.89 ± 0.01 | 9.86 ± 0.00 | 9.59 ± 0.00 |
| 生成 tokens/s（median / max） | 9.89 / 9.90 | 9.86 / 9.86 | 9.59 / 9.60 |
| e2e tokens/s（mean） | 9.80 | 9.79 | 7.92 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## Prefill 速度（拆冷啟 / 快取命中）

| 指標 | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| **冷啟 prompt tok/s** (run 1) | 82.32 | 190.56 | 413.21 |
| **快取命中 prompt tok/s** (run 2+ mean) | 137.52 | 675.06 | 44601.81 |
| **冷啟 TTFT 秒** (run 1) | 0.344 | 0.810 | 26.81 |
| **快取命中 TTFT 秒** (run 2+ mean) | 0.217 | 0.264 | 0.30 |

## 每次取樣明細

| # | prompt | run | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | wall (s) |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | 1 | ✅ | 9.90 | 82.32 | 9.77 | 0.344 | 26 | 256 | 26.21 |
| 2 | short | 2 | ✅ | 9.88 | 137.56 | 9.80 | 0.217 | 26 | 256 | 26.12 |
| 3 | short | 3 | ✅ | 9.89 | 137.49 | 9.81 | 0.217 | 26 | 256 | 26.11 |
| 4 | short | 4 | ✅ | 9.89 | 137.43 | 9.80 | 0.217 | 26 | 256 | 26.11 |
| 5 | short | 5 | ✅ | 9.88 | 137.59 | 9.80 | 0.216 | 26 | 256 | 26.12 |
| 6 | long | 1 | ✅ | 9.86 | 190.56 | 9.71 | 0.810 | 149 | 512 | 52.74 |
| 7 | long | 2 🔁 | ✅ | 9.86 | 456.14 | 9.80 | 0.355 | 149 | 512 | 52.27 |
| 8 | long | 3 🔁 | ✅ | 9.86 | 783.72 | 9.82 | 0.218 | 149 | 512 | 52.14 |
| 9 | long | 4 🔁 | ✅ | 9.86 | 785.31 | 9.82 | 0.218 | 149 | 512 | 52.13 |
| 10 | xlong | 1 | ✅ | 9.60 | 413.21 | 4.79 | 26.810 | 11064 | 256 | 53.49 |
| 11 | xlong | 2 🔁 | ✅ | 9.59 | 32869.48 | 9.46 | 0.370 | 11064 | 256 | 27.07 |
| 12 | xlong | 3 🔁 | ✅ | 9.59 | 56334.13 | 9.51 | 0.229 | 11064 | 256 | 26.93 |

> 🔁 = Ollama KV cache 命中（同一 prompt 重複），prefill 為 cache 重用而非真實計算。

