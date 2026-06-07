# Ollama 速度報告 — `qwen3.6:27b-mtp-q4_K_M`

- 開始: `2026-06-07T03:57:57-07:00`
- 結束: `2026-06-07T04:02:33-07:00`
- 架構: `qwen35`
- 參數量: `27.3B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `17.00 GB`
- 第一次冷啟動載入時間: `4.55 s`
- MTP draft_num_predict: `4`

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
| 生成 tokens/s（mean ± stdev） | 17.41 ± 0.58 | 20.62 ± 0.35 | 15.77 ± 0.05 |
| 生成 tokens/s（median / max） | 17.22 / 18.53 | 20.71 / 20.99 | 15.76 / 15.84 |
| prompt eval tokens/s（mean） | 175.28 | 787.58 | 43365.99 |
| e2e tokens/s（mean） | 17.02 | 20.22 | 11.74 |
| TTFT 秒（mean） | 0.341 | 0.512 | 14.464 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 18.53 | 211.88 | 18.12 | 0.312 | 26 | 256 | 1199 | 0 | 14.13 |
| 2 | short | ✅ | 17.24 | 175.50 | 16.84 | 0.353 | 26 | 256 | 1199 | 0 | 15.21 |
| 3 | short | ✅ | 17.20 | 158.87 | 16.80 | 0.351 | 26 | 256 | 1199 | 0 | 15.24 |
| 4 | short | ✅ | 16.86 | 154.88 | 16.48 | 0.354 | 26 | 256 | 1199 | 0 | 15.54 |
| 5 | short | ✅ | 17.22 | 175.24 | 16.85 | 0.332 | 26 | 256 | 1199 | 0 | 15.20 |
| 6 | long | ✅ | 20.09 | 166.83 | 19.27 | 1.074 | 149 | 512 | 2059 | 0 | 26.57 |
| 7 | long | ✅ | 20.99 | 1005.16 | 20.70 | 0.333 | 149 | 512 | 2059 | 0 | 24.73 |
| 8 | long | ✅ | 20.86 | 1012.51 | 20.60 | 0.315 | 149 | 512 | 2059 | 0 | 24.86 |
| 9 | long | ✅ | 20.55 | 965.83 | 20.29 | 0.325 | 149 | 512 | 2059 | 0 | 25.24 |
| 10 | xlong | ✅ | 15.76 | 276.52 | 4.35 | 42.664 | 11064 | 256 | 1165 | 0 | 58.91 |
| 11 | xlong | ✅ | 15.84 | 64886.55 | 15.49 | 0.366 | 11064 | 256 | 1165 | 0 | 16.53 |
| 12 | xlong | ✅ | 15.71 | 64934.91 | 15.37 | 0.362 | 11064 | 256 | 1165 | 0 | 16.66 |

