# Ollama 速度報告 — `gemma4:31b-nvfp4`

- 開始: `2026-06-07T02:39:25-07:00`
- 結束: `2026-06-07T02:47:06-07:00`
- 架構: `gemma4`
- 參數量: `31.3B`
- 量化格式: `nvfp4`
- 模型檔大小: `20.00 GB`
- 第一次冷啟動載入時間: `2.35 s`

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
| 生成 tokens/s（mean ± stdev） | 10.41 ± 0.02 | 10.27 ± 0.01 | 9.14 ± 0.02 |
| 生成 tokens/s（median / max） | 10.40 / 10.45 | 10.27 / 10.28 | 9.13 / 9.17 |
| prompt eval tokens/s（mean） | 177.75 | 680.29 | 25404.11 |
| e2e tokens/s（mean） | 10.32 | 10.18 | 7.28 |
| TTFT 秒（mean） | 0.000 | 0.000 | 0.000 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 11042 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 10.39 | 177.34 | 10.30 | 0.000 | 32 | 256 | 0 | 0 | 24.86 |
| 2 | short | ✅ | 10.45 | 175.18 | 10.36 | 0.000 | 32 | 256 | 0 | 0 | 24.71 |
| 3 | short | ✅ | 10.40 | 169.94 | 10.31 | 0.000 | 32 | 256 | 0 | 0 | 24.83 |
| 4 | short | ✅ | 10.39 | 185.20 | 10.30 | 0.000 | 32 | 256 | 0 | 0 | 24.85 |
| 5 | short | ✅ | 10.42 | 181.08 | 10.33 | 0.000 | 32 | 256 | 0 | 0 | 24.77 |
| 6 | long | ✅ | 10.27 | 157.91 | 10.07 | 0.000 | 156 | 512 | 0 | 0 | 50.87 |
| 7 | long | ✅ | 10.26 | 827.87 | 10.22 | 0.000 | 156 | 512 | 0 | 0 | 50.10 |
| 8 | long | ✅ | 10.26 | 855.37 | 10.22 | 0.000 | 156 | 512 | 0 | 0 | 50.11 |
| 9 | long | ✅ | 10.28 | 880.01 | 10.24 | 0.000 | 156 | 512 | 0 | 0 | 50.03 |
| 10 | xlong | ✅ | 9.13 | 276.75 | 3.77 | 0.000 | 11042 | 256 | 0 | 0 | 68.02 |
| 11 | xlong | ✅ | 9.17 | 27230.14 | 9.03 | 0.000 | 11042 | 256 | 0 | 0 | 28.39 |
| 12 | xlong | ✅ | 9.13 | 48705.44 | 9.04 | 0.000 | 11042 | 256 | 0 | 0 | 28.35 |

