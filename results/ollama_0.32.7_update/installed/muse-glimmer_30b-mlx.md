# Ollama 速度報告 — `muse-glimmer:30b-mlx`

- 開始: `2026-08-10T18:57:59-07:00`
- 結束: `2026-08-10T19:01:21-07:00`
- 架構: `muse_glimmer`
- 參數量: `32.3B`
- 量化格式: `nvfp4`
- 模型檔大小: `21.00 GB`
- Ollama: `0.32.7`
- 模型預設 `draft_num_predict`: `15`（測試未覆寫）
- 第一次冷啟動載入時間: `2.95 s`

## 量測說明

- 透過 Ollama `/api/generate` 串流 API 量測；以伺服器回報的 `eval_count / eval_duration` 計算純生成 tokens/s。
- `prompt eval tokens/s` = `prompt_eval_count / prompt_eval_duration`，反映 prefill 速度。
- `e2e tokens/s` = `eval_count / total_duration`，含 prompt prefill。
- TTFT 為串流首個 token 抵達 client 的 wall-clock 時間。
- 全部測試使用 `temperature=0`、`seed=42`，`keep_alive=10m`，先 warmup 再取樣。
- xlong 測試強制 `num_ctx=16384`，使用約 14k tokens 的 prompt 量測長上下文 prefill 與生成速度。
- 同一 prompt 的後續樣本會命中 Ollama KV cache；prompt eval 平均值包含快取樣本，冷 prefill 應查看各組第一個未快取樣本。

## 摘要

| 指標 | short prompt | long prompt | xlong prompt (16k) |
|---|---:|---:|---:|
| 生成 tokens/s（mean ± stdev） | 24.05 ± 0.29 | 26.30 ± 0.25 | 24.74 ± 0.24 |
| 生成 tokens/s（median / max） | 23.98 / 24.50 | 26.20 / 26.71 | 24.69 / 25.05 |
| prompt eval tokens/s（mean，含快取） | 8002053.77 | 15205501.65 | 378607105.81 |
| e2e tokens/s（mean） | 23.97 | 26.06 | 18.48 |
| TTFT 秒（mean） | 0.126 | 0.307 | 10.264 |
| 樣本數 (n) | 5 | 4 | 3 |
| 平均 prompt_eval_count | - | - | 10837 tokens |

## 每次取樣明細

| # | prompt | ok | gen tok/s | prompt tok/s | e2e tok/s | TTFT (s) | prompt_n | eval_n | think chars | resp chars | wall (s) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | short | ✅ | 23.65 | 10799460.03 | 23.56 | 0.133 | 72 | 256 | 934 | 301 | 10.87 |
| 2 | short | ✅ | 24.50 | 9142857.14 | 24.43 | 0.126 | 72 | 256 | 934 | 301 | 10.48 |
| 3 | short | ✅ | 23.98 | 6995724.83 | 23.91 | 0.124 | 72 | 256 | 934 | 301 | 10.71 |
| 4 | short | ✅ | 24.21 | 6400000.00 | 24.13 | 0.125 | 72 | 256 | 934 | 301 | 10.61 |
| 5 | short | ✅ | 23.90 | 6672226.86 | 23.82 | 0.123 | 72 | 256 | 934 | 301 | 10.75 |
| 6 | long | ✅ | 26.10 | 317.35 | 25.27 | 0.833 | 194 | 512 | 2391 | 0 | 20.26 |
| 7 | long | ✅ | 26.09 | 24767011.36 | 26.05 | 0.140 | 194 | 512 | 2391 | 0 | 19.66 |
| 8 | long | ✅ | 26.30 | 17504285.84 | 26.25 | 0.129 | 194 | 512 | 2391 | 0 | 19.51 |
| 9 | long | ✅ | 26.71 | 18550392.04 | 26.67 | 0.126 | 194 | 512 | 2391 | 0 | 19.20 |
| 10 | xlong | ✅ | 24.69 | 363.43 | 6.36 | 30.323 | 10837 | 256 | 1409 | 0 | 40.25 |
| 11 | xlong | ✅ | 24.47 | 105171.13 | 24.13 | 0.289 | 10837 | 256 | 1420 | 0 | 10.62 |
| 12 | xlong | ✅ | 25.05 | 1135715782.85 | 24.95 | 0.180 | 10837 | 256 | 1420 | 0 | 10.28 |
