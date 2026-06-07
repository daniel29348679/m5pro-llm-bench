# Ollama 速度報告 — `qwen3.6:35b-a3b-mtp-q4_K_M`

- 開始: `2026-06-07T02:20:54-07:00`
- 結束: `2026-06-07T02:22:54-07:00`
- 架構: `qwen35moe`
- 參數量: `35.5B`
- 量化格式: `Q4_K_M`
- 模型檔大小: `22.00 GB`
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
| 生成 tokens/s（mean ± stdev） | 36.67 ± 0.20 | 46.66 ± 0.17 | 40.72 ± 0.26 |
| 生成 tokens/s（median / max） | 36.73 / 36.88 | 46.61 / 46.94 | 40.80 / 41.00 |
| prompt eval tokens/s（mean） | 579.95 | 2587.07 | 133481.98 |
| e2e tokens/s（mean） | 35.56 | 45.53 | 30.51 |
| TTFT 秒（mean） | 0.219 | 0.271 | 4.422 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11064 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 36.30 | 557.78 | 35.16 | 0.230 | 26 | 256 | 1037 | 0 | 7.28 |
| 2 | short | ✅ | 36.73 | 581.03 | 35.60 | 0.220 | 26 | 256 | 1037 | 0 | 7.19 |
| 3 | short | ✅ | 36.75 | 600.70 | 35.64 | 0.215 | 26 | 256 | 1037 | 0 | 7.18 |
| 4 | short | ✅ | 36.71 | 571.18 | 35.61 | 0.214 | 26 | 256 | 1037 | 0 | 7.19 |
| 5 | short | ✅ | 36.88 | 589.03 | 35.77 | 0.216 | 26 | 256 | 1037 | 0 | 7.16 |
| 6 | long | ✅ | 46.94 | 583.17 | 45.17 | 0.428 | 149 | 512 | 2129 | 0 | 11.34 |
| 7 | long | ✅ | 46.62 | 3363.81 | 45.70 | 0.222 | 149 | 512 | 2129 | 0 | 11.21 |
| 8 | long | ✅ | 46.61 | 3355.63 | 45.72 | 0.215 | 149 | 512 | 2129 | 0 | 11.20 |
| 9 | long | ✅ | 46.46 | 3045.66 | 45.55 | 0.221 | 149 | 512 | 2129 | 0 | 11.24 |
| 10 | xlong | ✅ | 41.00 | 1065.49 | 13.47 | 12.763 | 11064 | 256 | 1180 | 0 | 19.02 |
| 11 | xlong | ✅ | 40.37 | 195927.04 | 38.81 | 0.255 | 11064 | 256 | 1180 | 0 | 6.61 |
| 12 | xlong | ✅ | 40.80 | 203453.41 | 39.25 | 0.248 | 11064 | 256 | 1180 | 0 | 6.53 |

