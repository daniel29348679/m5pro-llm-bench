# Ollama 速度報告 — `qwen3.6:35b-a3b-coding-nvfp4`

- 開始: `2026-06-07T02:48:35-07:00`
- 結束: `2026-06-07T02:49:51-07:00`
- 架構: `qwen3_5_moe`
- 參數量: `35.1B`
- 量化格式: `nvfp4`
- 模型檔大小: `21.00 GB`
- 第一次冷啟動載入時間: `1.94 s`

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
| 生成 tokens/s（mean ± stdev） | 64.57 ± 0.77 | 64.58 ± 0.09 | 59.15 ± 0.06 |
| 生成 tokens/s（median / max） | 64.94 / 65.02 | 64.58 / 64.69 | 59.19 / 59.19 |
| prompt eval tokens/s（mean） | 846.82 | 3542.60 | 181155.37 |
| e2e tokens/s（mean） | 63.68 | 63.64 | 46.32 |
| TTFT 秒（mean） | 0.056 | 0.119 | 2.395 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 64.94 | 494.85 | 63.72 | 0.076 | 26 | 256 | 1054 | 0 | 4.02 |
| 2 | short | ✅ | 64.95 | 933.30 | 64.12 | 0.052 | 26 | 256 | 1054 | 0 | 3.99 |
| 3 | short | ✅ | 65.02 | 943.23 | 64.20 | 0.051 | 26 | 256 | 1054 | 0 | 3.99 |
| 4 | short | ✅ | 64.91 | 955.76 | 64.10 | 0.050 | 26 | 256 | 1054 | 0 | 4.00 |
| 5 | short | ✅ | 63.03 | 906.95 | 62.23 | 0.053 | 26 | 256 | 1054 | 0 | 4.11 |
| 6 | long | ✅ | 64.51 | 569.78 | 62.22 | 0.293 | 149 | 512 | 1932 | 0 | 8.23 |
| 7 | long | ✅ | 64.66 | 2816.20 | 64.03 | 0.078 | 149 | 512 | 1932 | 0 | 8.00 |
| 8 | long | ✅ | 64.69 | 5316.68 | 64.26 | 0.053 | 149 | 512 | 1932 | 0 | 7.97 |
| 9 | long | ✅ | 64.46 | 5467.75 | 64.05 | 0.052 | 149 | 512 | 1932 | 0 | 8.00 |
| 10 | xlong | ✅ | 59.07 | 1577.86 | 22.51 | 7.041 | 11064 | 256 | 1218 | 0 | 11.38 |
| 11 | xlong | ✅ | 59.19 | 190621.82 | 58.04 | 0.086 | 11064 | 256 | 1218 | 0 | 4.42 |
| 12 | xlong | ✅ | 59.19 | 351266.44 | 58.41 | 0.058 | 11064 | 256 | 1218 | 0 | 4.39 |

