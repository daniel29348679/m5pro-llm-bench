# Ollama 速度報告 — `qwen3.6:27b-mtp-q4_K_M`

- 開始: `2026-06-07T04:04:51-07:00`
- 結束: `2026-06-07T04:12:18-07:00`
- 架構: `qwen35`
- 參數量: `27.3B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `17.00 GB`
- 第一次冷啟動載入時間: `2.79 s`
- MTP draft_num_predict: `8`

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
| 生成 tokens/s（mean ± stdev） | 9.28 ± 0.04 | 12.40 ± 0.01 | 8.84 ± 0.00 |
| 生成 tokens/s（median / max） | 9.30 / 9.32 | 12.40 / 12.42 | 8.84 / 8.85 |
| prompt eval tokens/s（mean） | 153.99 | 700.41 | 39212.69 |
| e2e tokens/s（mean） | 9.17 | 12.24 | 6.99 |
| TTFT 秒（mean） | 0.344 | 0.542 | 14.906 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 9.22 | 152.46 | 9.10 | 0.360 | 26 | 256 | 1199 | 0 | 28.12 |
| 2 | short | ✅ | 9.26 | 153.86 | 9.14 | 0.352 | 26 | 256 | 1199 | 0 | 28.01 |
| 3 | short | ✅ | 9.30 | 154.48 | 9.19 | 0.335 | 26 | 256 | 1199 | 0 | 27.86 |
| 4 | short | ✅ | 9.31 | 155.08 | 9.20 | 0.337 | 26 | 256 | 1199 | 0 | 27.84 |
| 5 | short | ✅ | 9.32 | 154.08 | 9.21 | 0.338 | 26 | 256 | 1199 | 0 | 27.80 |
| 6 | long | ✅ | 12.40 | 155.10 | 12.07 | 1.129 | 149 | 512 | 2059 | 0 | 42.42 |
| 7 | long | ✅ | 12.38 | 885.44 | 12.27 | 0.360 | 149 | 512 | 2059 | 0 | 41.73 |
| 8 | long | ✅ | 12.41 | 877.83 | 12.30 | 0.340 | 149 | 512 | 2059 | 0 | 41.61 |
| 9 | long | ✅ | 12.42 | 883.27 | 12.32 | 0.339 | 149 | 512 | 2059 | 0 | 41.58 |
| 10 | xlong | ✅ | 8.84 | 267.81 | 3.51 | 43.950 | 11064 | 256 | 1165 | 0 | 72.92 |
| 11 | xlong | ✅ | 8.84 | 58316.29 | 8.73 | 0.384 | 11064 | 256 | 1165 | 0 | 29.35 |
| 12 | xlong | ✅ | 8.85 | 59053.98 | 8.73 | 0.382 | 11064 | 256 | 1165 | 0 | 29.32 |

