# `muse-glimmer:30b-mlx` Ollama 速度測試（高效能模式 + 16k 上下文）

- 報告產生時間: `2026-08-10T19:01:21-07:00`
- 主機: Darwin 27.0.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama: `0.32.7`
- Ollama URL: `http://localhost:11434`
- 系統電源模式: `pmset powermode=2`（High Power, AC 供電）
- 防睡眠: `caffeinate -dimsu` 全程啟用
- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`
- 模型預設 `draft_num_predict`: `15`（測試未覆寫）
- short/long 採用預設 num_ctx；xlong 強制 `num_ctx=16384`

## 主表 — 三段 prompt 的生成 / prompt eval / TTFT

| 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `muse-glimmer:30b-mlx` | 32.3B | nvfp4 | 21.00 | 2.95 | 24.05 | 26.30 | 24.74 | 8002053.77 | 15205501.65 | 378607105.81 | 0.126 | 0.307 | 10.26 |

> 所有數值單位：`gen` / `prompt` 為 tokens/s（越大越快）；`TTFT` 為秒（越小越好）。

> 同一 prompt 的後續樣本會命中 Ollama KV cache，因此表中的 prompt 平均值包含快取結果。第一次未快取的 long / xlong prefill 分別為 `317.35` / `363.43` tokens/s，xlong 首次 TTFT 為 `30.32 s`。

## 排名

### short prompt 生成速度

| 排名 | 模型 | short gen tok/s |
|---:|---|---:|
| 1 | `muse-glimmer:30b-mlx` | 24.05 |

### long prompt 生成速度

| 排名 | 模型 | long gen tok/s |
|---:|---|---:|
| 1 | `muse-glimmer:30b-mlx` | 26.30 |

### xlong (16k) 生成速度

| 排名 | 模型 | xlong gen tok/s | 平均 prompt tokens |
|---:|---|---:|---:|
| 1 | `muse-glimmer:30b-mlx` | 24.74 | 10837 |

## 指標說明

- **gen tok/s**：純生成 tokens/s（伺服器回報的 `eval_count / eval_duration`）。
- **prompt tok/s**：prefill 速度，反映模型一次吞下整段 prompt 的能力。
- **TTFT**：client 收到第一個 token 的 wall-clock 秒數，可視為使用者「按下送出後等多久」。
- **冷啟**：模型剛載入記憶體後第一次 forward 的時間（伺服器 `load_duration` 或 wall）。
- **xlong**：以一段 ~14k tokens 的合成語料 + `num_ctx=16384` 量測長上下文 prefill 與生成速度。
