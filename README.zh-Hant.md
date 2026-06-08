# M5 Pro LLM Benchmark — Ollama 0.30.6 模型選擇

**Languages**: [English](./README.md) · **繁體中文** · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

這個 repo 測試 **Apple M5 Pro / 64 GB** 在 [Ollama](https://ollama.com) 上跑本地 LLM 的吞吐量。目前結果使用 **Ollama 0.30.6** 與這台機器上已安裝的模型；舊的 10 模型完整測試保留在 [REPORT.md](./REPORT.md) 作為歷史資料。

## 快速選擇

| 情況 | 直接選 | 原因 |
|---|---|---|
| 目前最快的本地 Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M`，`draft_num_predict=4` | 最高實測解碼速度到 **87.97 tokens/s** |
| 你要用 Gemma | `gemma4:26b-nvfp4` | 目前已安裝 Gemma 裡速度最好 |
| 你需要較小的 Qwen MTP | `qwen3.6:27b-mtp-q4_K_M`，`draft_num_predict=4` | 模型檔 17 GB，但比 35B-a3B MTP 慢很多 |
| 你在調 MTP | 保持模型預設 `draft_num_predict=4` | 強制改成 `8` 兩個 MTP 模型都變慢 |
| 你只看舊完整比較 | 看 [REPORT.md](./REPORT.md) | 原始 10 模型量化與 MLX 比較在那裡 |

## 目前結果

| 模型 | 最適合用途 | 模型檔大小 (GB) | 短輸出解碼 (tokens/s) | 長輸出解碼 (tokens/s) | 11k 上下文解碼 (tokens/s) | 資料來源 |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 目前最快 Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP 重測，draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | 非 MTP Qwen 備選 | 21 | 64.57 | 64.58 | 59.15 | 已安裝模型測試 |
| `gemma4:26b-nvfp4` | 目前最快 Gemma | 16 | 59.16 | 58.33 | 49.07 | 已安裝模型測試 |
| `qwen3.6:27b-mtp-q4_K_M` | 較小 Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP 重測，draft 4 |
| `gemma4:31b-nvfp4` | 不建議當速度首選 | 20 | 10.41 | 10.27 | 9.14 | 已安裝模型測試 |

## MTP 預測 tokens

| 模型 | MTP 預測 tokens (`draft_num_predict`) | 短輸出解碼 (tokens/s) | 長輸出解碼 (tokens/s) | 11k 上下文解碼 (tokens/s) | 相對 draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP 結論：**這台機器不要強制 `draft_num_predict=8`，用模型預設 `4`。

## 目前更新實測模型

| 系列 | 模型 | 參數 | 量化 | 模型檔大小 (GB) | 備註 |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | 目前贏家 |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | 較小 MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | 歷史贏家，目前 run 較慢 |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | 目前 Gemma 最佳結果 |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | 這次速度慢 |

## 測試形狀

| 測試情境 | Prompt 長度 (tokens) | 生成上限 (`num_predict`, tokens) | 取樣次數 |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | 約 11,000，`num_ctx=16384` | 256 | 3 |

解碼速度採用 Ollama server 回報的 `eval_count / eval_duration`。測試時鎖定 High Power：`pmset powermode=2`，並全程使用 `caffeinate -dimsu`。

## 歷史資料重點

原始完整測試在 Ollama 0.21/run2 上跑 10 個模型。架構、量化、MLX 比較請以它作為歷史對照：

| 歷史發現 | 結果 |
|---|---|
| 舊測試短輸出解碼最快 | `qwen3.6:35b-a3b-coding-nvfp4`，**80.61 tokens/s** |
| 舊測試 11k cold prefill 最快 | `gemma4:e4b-nvfp4`，**4205.55 tokens/s** |
| Apple Silicon 注意事項 | `mxfp8` 檔案更大，速度卻比 Q4_K_M 慢 |
| MLX 注意事項 | 乾淨的 Gemma BF16 對照裡，MLX 幫 prefill，不幫 decode |

## 原始結果

- [Ollama 0.30.6 已安裝模型比較](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 重測](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 重測](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [歷史 10 模型報告](./REPORT.md)

## 最後結論

沒有特殊限制時，直接用 `qwen3.6:35b-a3b-mtp-q4_K_M`，並保持預設 `draft_num_predict=4`。只有明確要 Gemma 時才選 `gemma4:26b-nvfp4`。只有在 22 GB 模型檔不適合、比較在意 17 GB 檔案大小時，才選 `qwen3.6:27b-mtp-q4_K_M`。不要把 MTP 預測 tokens 強制改成 `8`。
