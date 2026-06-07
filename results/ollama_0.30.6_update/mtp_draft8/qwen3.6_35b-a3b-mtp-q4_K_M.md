# Ollama 速度報告 — `qwen3.6:35b-a3b-mtp-q4_K_M`

- 開始: `2026-06-07T04:02:48-07:00`
- 結束: `2026-06-07T04:04:49-07:00`
- 架構: `qwen35moe`
- 參數量: `35.5B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `22.00 GB`
- 第一次冷啟動載入時間: `3.04 s`
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
| 生成 tokens/s（mean ± stdev） | 35.75 ± 0.05 | 45.55 ± 0.23 | 39.81 ± 0.15 |
| 生成 tokens/s（median / max） | 35.78 / 35.82 | 45.49 / 45.92 | 39.73 / 40.03 |
| prompt eval tokens/s（mean） | 558.61 | 2621.09 | 140224.85 |
| e2e tokens/s（mean） | 34.68 | 44.49 | 29.96 |
| TTFT 秒（mean） | 0.221 | 0.268 | 4.520 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 35.70 | 580.63 | 34.63 | 0.223 | 26 | 256 | 1037 | 0 | 7.39 |
| 2 | short | ✅ | 35.78 | 572.47 | 34.68 | 0.226 | 26 | 256 | 1037 | 0 | 7.38 |
| 3 | short | ✅ | 35.78 | 581.40 | 34.73 | 0.216 | 26 | 256 | 1037 | 0 | 7.37 |
| 4 | short | ✅ | 35.69 | 521.03 | 34.62 | 0.221 | 26 | 256 | 1037 | 0 | 7.39 |
| 5 | short | ✅ | 35.82 | 537.53 | 34.75 | 0.220 | 26 | 256 | 1037 | 0 | 7.37 |
| 6 | long | ✅ | 45.92 | 619.03 | 44.29 | 0.411 | 149 | 512 | 2129 | 0 | 11.56 |
| 7 | long | ✅ | 45.42 | 3304.21 | 44.53 | 0.227 | 149 | 512 | 2129 | 0 | 11.50 |
| 8 | long | ✅ | 45.31 | 3281.36 | 44.47 | 0.214 | 149 | 512 | 2129 | 0 | 11.52 |
| 9 | long | ✅ | 45.56 | 3279.77 | 44.69 | 0.218 | 149 | 512 | 2129 | 0 | 11.46 |
| 10 | xlong | ✅ | 39.73 | 1034.01 | 13.12 | 13.063 | 11064 | 256 | 1180 | 0 | 19.52 |
| 11 | xlong | ✅ | 40.03 | 204178.05 | 38.52 | 0.250 | 11064 | 256 | 1180 | 0 | 6.66 |
| 12 | xlong | ✅ | 39.69 | 215462.51 | 38.22 | 0.248 | 11064 | 256 | 1180 | 0 | 6.71 |

