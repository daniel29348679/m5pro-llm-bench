# Ollama 速度報告 — `gemma4:26b-nvfp4`

- 開始: `2026-06-07T02:47:08-07:00`
- 結束: `2026-06-07T02:48:33-07:00`
- 架構: `gemma4`
- 參數量: `6.3B`
- 量化格式: `nvfp4`
- 模型檔大小: `16.00 GB`
- 第一次冷啟動載入時間: `1.85 s`

## 量測說明

- 透過 Ollama `/api/generate` 串流 API 量測；以伺服器回報的 `eval_count / eval_duration` 計算純生成 tokens/s。
- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`，反映 prefill 速度。
- `e2e tokens/s` = `eval_count / total_duration`，含 prompt prefill。
- TTFT 為串流首個 token 抵達 client 的 wall-clock 時間。
- 全部測試使用 `temperature=0`、`seed=42`，`keep_alive=10m`，先 warmup 再取樣。
- xlong 測試強制 `num_ctx=16384`，使用約 14k tokens 的 prompt 量測長上下文 prefill 與生成速度。

## 摘要

| 指標 | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| 生成 tokens/s（mean ± stdev） | 59.16 ± 0.58 | 58.33 ± 0.17 | 49.07 ± 0.31 |
| 生成 tokens/s（median / max） | 59.43 / 59.58 | 58.32 / 58.55 | 49.04 / 49.47 |
| prompt eval tokens/s（mean） | 1081.78 | 3799.73 | 140257.35 |
| e2e tokens/s（mean） | 58.46 | 57.22 | 38.93 |
| TTFT 秒（mean） | 0.000 | 0.000 | 0.000 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11042 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 58.02 | 1083.89 | 57.33 | 0.000 | 32 | 256 | 0 | 0 | 4.47 |
| 2 | short | ✅ | 59.58 | 1071.13 | 58.87 | 0.000 | 32 | 256 | 0 | 0 | 4.35 |
| 3 | short | ✅ | 59.43 | 1131.25 | 58.73 | 0.000 | 32 | 256 | 0 | 0 | 4.36 |
| 4 | short | ✅ | 59.44 | 1072.18 | 58.73 | 0.000 | 32 | 256 | 0 | 0 | 4.36 |
| 5 | short | ✅ | 59.35 | 1050.48 | 58.62 | 0.000 | 32 | 256 | 0 | 0 | 4.37 |
| 6 | long | ✅ | 58.25 | 305.91 | 54.92 | 0.000 | 156 | 512 | 0 | 0 | 9.33 |
| 7 | long | ✅ | 58.11 | 4765.86 | 57.74 | 0.000 | 156 | 512 | 0 | 0 | 8.87 |
| 8 | long | ✅ | 58.55 | 5009.24 | 58.20 | 0.000 | 156 | 512 | 0 | 0 | 8.80 |
| 9 | long | ✅ | 58.40 | 5117.90 | 58.04 | 0.000 | 156 | 512 | 0 | 0 | 8.82 |
| 10 | xlong | ✅ | 49.04 | 1553.28 | 20.68 | 0.000 | 11042 | 256 | 0 | 0 | 12.41 |
| 11 | xlong | ✅ | 48.70 | 136264.07 | 47.48 | 0.000 | 11042 | 256 | 0 | 0 | 5.42 |
| 12 | xlong | ✅ | 49.47 | 282954.69 | 48.63 | 0.000 | 11042 | 256 | 0 | 0 | 5.29 |

