# Qwen3.6 系列 Ollama 速度綜合對比 (run2 — 高效能模式 + 16k 上下文)

- 報告產生時間: `2026-06-07T04:02:33-07:00`
- 主機: Darwin 25.6.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama URL: `http://127.0.0.1:11434`
- 系統電源模式: `pmset powermode=2`（High Power, AC 供電）
- 防睡眠: `caffeinate -dimsu` 全程啟用
- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`
- MTP `draft_num_predict`: `4`
- short/long 採用預設 num_ctx；xlong 強制 `num_ctx=16384`

## 主表 — 三段 prompt 的生成 / prompt eval / TTFT

| 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B | Q4_K_M | 22.00 | 5.04 | 86.79 | 87.97 | 79.94 | 843.26 | 3806.07 | 193867.04 | 0.196 | 0.241 | 3.93 |
| `qwen3.6:27b-mtp-q4_K_M` | 27.3B | Q4_K_M | 17.00 | 4.55 | 17.41 | 20.62 | 15.77 | 175.28 | 787.58 | 43365.99 | 0.341 | 0.512 | 14.46 |

> 所有數值單位：`gen` / `prompt` 為 tokens/s（越大越快）；`TTFT` 為秒（越小越好）。

## 排名

### short prompt 生成速度

| 排名 | 模型 | short gen tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 86.79 |
| 2 | `qwen3.6:27b-mtp-q4_K_M` | 17.41 |

### long prompt 生成速度

| 排名 | 模型 | long gen tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 87.97 |
| 2 | `qwen3.6:27b-mtp-q4_K_M` | 20.62 |

### xlong (16k) 生成速度

| 排名 | 模型 | xlong gen tok/s | 平均 prompt tokens |
|---:|---|---:|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 79.94 | 11064 |
| 2 | `qwen3.6:27b-mtp-q4_K_M` | 15.77 | 11064 |

## 指標說明

- **gen tok/s**：純生成 tokens/s（伺服器回報的 `eval_count / eval_duration`）。
- **prompt tok/s**：prefill 速度，反映模型一次吞下整段 prompt 的能力。
- **TTFT**：client 收到第一個 token 的 wall-clock 秒數，可視為使用者「按下送出後等多久」。
- **冷啟**：模型剛載入記憶體後第一次 forward 的時間（伺服器 `load_duration` 或 wall）。
- **xlong**：以一段 ~14k tokens 的合成語料 + `num_ctx=16384` 量測長上下文 prefill 與生成速度。

