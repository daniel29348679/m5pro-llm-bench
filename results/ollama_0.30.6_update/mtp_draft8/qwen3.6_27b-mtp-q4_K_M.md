# Ollama 速度報告 — `qwen3.6:27b-mtp-q4_K_M`

- 開始: `2026-06-07T02:13:27-07:00`
- 結束: `2026-06-07T02:20:52-07:00`
- 架構: `qwen35`
- 參數量: `27.3B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `17.00 GB`
- 第一次冷啟動載入時間: `5.30 s`
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
| 生成 tokens/s（mean ± stdev） | 9.44 ± 0.01 | 12.61 ± 0.03 | 8.97 ± 0.01 |
| 生成 tokens/s（median / max） | 9.44 / 9.45 | 12.61 / 12.65 | 8.97 / 8.98 |
| prompt eval tokens/s（mean） | 151.47 | 688.01 | 39763.14 |
| e2e tokens/s（mean） | 9.32 | 12.44 | 7.06 |
| TTFT 秒（mean） | 0.361 | 0.545 | 15.375 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 9.43 | 157.75 | 9.31 | 0.364 | 26 | 256 | 1199 | 0 | 27.50 |
| 2 | short | ✅ | 9.45 | 143.37 | 9.33 | 0.375 | 26 | 256 | 1199 | 0 | 27.45 |
| 3 | short | ✅ | 9.45 | 142.88 | 9.33 | 0.370 | 26 | 256 | 1199 | 0 | 27.45 |
| 4 | short | ✅ | 9.44 | 155.95 | 9.32 | 0.360 | 26 | 256 | 1199 | 0 | 27.47 |
| 5 | short | ✅ | 9.43 | 157.42 | 9.32 | 0.338 | 26 | 256 | 1199 | 0 | 27.48 |
| 6 | long | ✅ | 12.57 | 159.33 | 12.24 | 1.113 | 149 | 512 | 2059 | 0 | 41.85 |
| 7 | long | ✅ | 12.62 | 816.17 | 12.50 | 0.377 | 149 | 512 | 2059 | 0 | 40.96 |
| 8 | long | ✅ | 12.60 | 881.82 | 12.49 | 0.346 | 149 | 512 | 2059 | 0 | 40.99 |
| 9 | long | ✅ | 12.65 | 894.71 | 12.54 | 0.343 | 149 | 512 | 2059 | 0 | 40.82 |
| 10 | xlong | ✅ | 8.95 | 268.15 | 3.46 | 45.365 | 11064 | 256 | 1165 | 0 | 73.98 |
| 11 | xlong | ✅ | 8.98 | 58906.84 | 8.86 | 0.384 | 11064 | 256 | 1165 | 0 | 28.90 |
| 12 | xlong | ✅ | 8.97 | 60114.43 | 8.85 | 0.376 | 11064 | 256 | 1165 | 0 | 28.93 |

