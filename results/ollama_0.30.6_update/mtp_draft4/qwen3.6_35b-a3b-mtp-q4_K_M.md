# Ollama 速度報告 — `qwen3.6:35b-a3b-mtp-q4_K_M`

- 開始: `2026-06-07T03:56:47-07:00`
- 結束: `2026-06-07T03:57:54-07:00`
- 架構: `qwen35moe`
- 參數量: `35.5B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `22.00 GB`
- 第一次冷啟動載入時間: `5.04 s`
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
| 生成 tokens/s（mean ± stdev） | 86.79 ± 0.21 | 87.97 ± 0.20 | 79.94 ± 0.01 |
| 生成 tokens/s（median / max） | 86.85 / 87.02 | 88.02 / 88.18 | 79.93 / 79.95 |
| prompt eval tokens/s（mean） | 843.26 | 3806.07 | 193867.04 |
| e2e tokens/s（mean） | 81.41 | 84.49 | 55.50 |
| TTFT 秒（mean） | 0.196 | 0.241 | 3.928 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 87.02 | 846.68 | 81.59 | 0.197 | 26 | 256 | 1076 | 0 | 3.14 |
| 2 | short | ✅ | 86.41 | 842.76 | 81.05 | 0.196 | 26 | 256 | 1076 | 0 | 3.16 |
| 3 | short | ✅ | 86.78 | 829.21 | 81.43 | 0.194 | 26 | 256 | 1076 | 0 | 3.15 |
| 4 | short | ✅ | 86.90 | 856.87 | 81.54 | 0.194 | 26 | 256 | 1076 | 0 | 3.14 |
| 5 | short | ✅ | 86.85 | 840.77 | 81.44 | 0.197 | 26 | 256 | 1076 | 0 | 3.15 |
| 6 | long | ✅ | 88.18 | 825.84 | 83.20 | 0.348 | 149 | 512 | 2181 | 0 | 6.16 |
| 7 | long | ✅ | 87.97 | 4750.22 | 84.82 | 0.217 | 149 | 512 | 2181 | 0 | 6.04 |
| 8 | long | ✅ | 88.06 | 4821.23 | 85.16 | 0.199 | 149 | 512 | 2181 | 0 | 6.01 |
| 9 | long | ✅ | 87.65 | 4827.01 | 84.76 | 0.200 | 149 | 512 | 2181 | 0 | 6.04 |
| 10 | xlong | ✅ | 79.95 | 1238.71 | 17.64 | 11.311 | 11064 | 256 | 1229 | 0 | 14.52 |
| 11 | xlong | ✅ | 79.93 | 293537.09 | 74.46 | 0.236 | 11064 | 256 | 1229 | 0 | 3.45 |
| 12 | xlong | ✅ | 79.93 | 286825.32 | 74.40 | 0.238 | 11064 | 256 | 1229 | 0 | 3.45 |

