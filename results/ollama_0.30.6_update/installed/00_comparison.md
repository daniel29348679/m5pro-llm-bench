# Qwen3.6 系列 Ollama 速度綜合對比 (run2 — 高效能模式 + 16k 上下文)

- 報告產生時間: `2026-06-07T02:49:51-07:00`
- 主機: Darwin 25.6.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama URL: `http://127.0.0.1:11434`
- 系統電源模式: `pmset powermode=2`（High Power, AC 供電）
- 防睡眠: `caffeinate -dimsu` 全程啟用
- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`
- short/long 採用預設 num_ctx；xlong 強制 `num_ctx=16384`

## 主表 — 三段 prompt 的生成 / prompt eval / TTFT

| 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | short gen | long gen | xlong gen | short prompt | long prompt | xlong prompt | short TTFT | long TTFT | xlong TTFT |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B | Q4_K_M | 22.00 | 2.28 | 83.65 | 84.74 | 76.68 | 813.78 | 3607.53 | 188982.55 | 0.202 | 0.244 | 4.06 |
| `qwen3.6:27b-mtp-q4_K_M` | 27.3B | Q4_K_M | 17.00 | 2.78 | 19.43 | 20.60 | 15.95 | 191.90 | 775.35 | 41709.92 | 0.327 | 0.517 | 15.19 |
| `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20.00 | 2.35 | 10.41 | 10.27 | 9.14 | 177.75 | 680.29 | 25404.11 | 0.000 | 0.000 | 0.00 |
| `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16.00 | 1.85 | 59.16 | 58.33 | 49.07 | 1081.78 | 3799.73 | 140257.35 | 0.000 | 0.000 | 0.00 |
| `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B | nvfp4 | 21.00 | 1.94 | 64.57 | 64.58 | 59.15 | 846.82 | 3542.60 | 181155.37 | 0.056 | 0.119 | 2.40 |

> 所有數值單位：`gen` / `prompt` 為 tokens/s（越大越快）；`TTFT` 為秒（越小越好）。

## 排名

### short prompt 生成速度

| 排名 | 模型 | short gen tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 83.65 |
| 2 | `qwen3.6:35b-a3b-coding-nvfp4` | 64.57 |
| 3 | `gemma4:26b-nvfp4` | 59.16 |
| 4 | `qwen3.6:27b-mtp-q4_K_M` | 19.43 |
| 5 | `gemma4:31b-nvfp4` | 10.41 |

### long prompt 生成速度

| 排名 | 模型 | long gen tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 84.74 |
| 2 | `qwen3.6:35b-a3b-coding-nvfp4` | 64.58 |
| 3 | `gemma4:26b-nvfp4` | 58.33 |
| 4 | `qwen3.6:27b-mtp-q4_K_M` | 20.60 |
| 5 | `gemma4:31b-nvfp4` | 10.27 |

### xlong (16k) 生成速度

| 排名 | 模型 | xlong gen tok/s | 平均 prompt tokens |
|---:|---|---:|---:|
| 1 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 76.68 | 11064 |
| 2 | `qwen3.6:35b-a3b-coding-nvfp4` | 59.15 | 11064 |
| 3 | `gemma4:26b-nvfp4` | 49.07 | 11042 |
| 4 | `qwen3.6:27b-mtp-q4_K_M` | 15.95 | 11064 |
| 5 | `gemma4:31b-nvfp4` | 9.14 | 11042 |

## 指標說明

- **gen tok/s**：純生成 tokens/s（伺服器回報的 `eval_count / eval_duration`）。
- **prompt tok/s**：prefill 速度，反映模型一次吞下整段 prompt 的能力。
- **TTFT**：client 收到第一個 token 的 wall-clock 秒數，可視為使用者「按下送出後等多久」。
- **冷啟**：模型剛載入記憶體後第一次 forward 的時間（伺服器 `load_duration` 或 wall）。
- **xlong**：以一段 ~14k tokens 的合成語料 + `num_ctx=16384` 量測長上下文 prefill 與生成速度。

