# Qwen3.6 + Gemma4 Ollama 速度綜合對比 — run2 (高效能模式 + 16k 上下文)

- 報告產生時間: `2026-05-07T04:33:47-07:00`
- 主機: Darwin 25.5.0 / Apple M5 Pro / 64 GB
- Python: `3.14.4`
- Ollama URL: `http://localhost:11434`
- 系統電源模式: `pmset powermode=2` (High Power, AC 供電)
- 防睡眠: `caffeinate -dimsu` 全程啟用
- 測試設定: `temperature=0` `seed=42` `keep_alive=10m`,每模型 cold-start + warmup 後才取樣
- 取樣: short × 5 (256 tok)、long × 4 (512 tok)、xlong × 3 (256 tok, num_ctx=16384, prompt ~11k tok)
- 受測模型: 6 × Qwen3.6 系列 + 4 × Gemma4 e4b 系列 = 10 個模型

## TL;DR — 一句話結論

### Qwen3.6 系列
- **MoE 35b-a3b 在解碼上完勝 dense**：🍎 `qwen3.6:35b-a3b-coding-nvfp4` (80.6 tok/s) 是 Qwen 最快,約是 dense 35b 的 2 倍、dense 27b 的 7 倍。
- **nvfp4 量化壓倒性勝過 mxfp8**：同架構下 nvfp4 解碼快 1.3–1.7 倍,模型檔小 40%~43%。
- **dense 27b-coding-mxfp8 反常**：9.86 tok/s 比原版 27b 的 11.82 還慢,且檔案大 1.8 倍 — mxfp8 在 Apple Silicon Metal backend 沒有原生加速。

### Gemma4 e4b 系列
- **e4b 4-bit 與 nvfp4 解碼幾乎相同**：68.6 vs 69.3 tok/s,差距 1%。
- **但 nvfp4 的 prefill 快很多**：xlong cold prefill 4206 vs 736 tok/s,**5.7 倍**。長 prompt 場景 nvfp4 明顯較佳。
- **BF16 變體解碼慢 2.4 倍**：28.0–28.4 vs 4-bit 的 68 tok/s,符合 BF16 記憶體頻寬需求 2x 的理論。
- **`mlx-bf16` 解碼與 `it-bf16` 相同,但 prefill 大幅領先**：xlong cold prefill 3721 vs 782 tok/s (4.8 倍);長 prompt 場景 mlx 較佳。
- **`e4b-nvfp4` 是 8B 級最佳全能選擇**：69 tok/s 解碼、9.6 GB 檔案、1.09s 載入、prefill 也最快。

### 跨系列比較
- **8B Gemma4 e4b 解碼完勝 27B Qwen dense**：69 vs 11.8 tok/s (5.8x)。要快先看模型大小,再看 quant。
- **35B-MoE (3B active) 仍微勝 8B dense**：80.6 vs 69.3 tok/s,只快 16%,但模型大 2x 且品質應較高。
- **長上下文懲罰一致很小**：所有 10 個模型從 short → 11k token xlong 解碼速度只掉 4–10%。M5 Pro 的記憶體頻寬對 16k context 仍未撞瓶頸。
- **電源模式必須鎖 High Power**：上一輪 Automatic 模式下 dense 模型慢 50%~90%;nvfp4 在兩種模式下都已跑滿。

## 主表 — 生成速度 (cache 不影響)

| 系列 | 模型 | 參數 | 量化 | 大小 (GB) | 冷啟 (s) | short gen | long gen | xlong gen |
|---|---|---|---|---:|---:|---:|---:|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B | Q4_K_M | 23.00 | 4.36 | 41.68 | 41.71 | 39.05 |
| Qwen3.6 | `qwen3.6:27b` | 27.8B | Q4_K_M | 17.00 | 4.12 | 11.82 | 11.82 | 11.32 |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B | mxfp8 | 31.00 | 2.86 | 9.89 | 9.86 | 9.59 |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B | nvfp4 | 19.00 | 1.66 | 16.34 | 16.30 | 15.53 |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B | mxfp8 | 37.00 | 3.25 | 60.41 | 60.47 | 56.48 |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B | nvfp4 | 21.00 | 1.86 | 80.61 | 80.74 | 73.97 |
| Gemma4 | `gemma4:e4b` | 8.0B | Q4_K_M | 9.60 | 3.27 | 68.56 | 68.30 | 62.01 |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B | F16 | 16.00 | 4.58 | 28.42 | 28.13 | 26.87 |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B | ? | 16.00 | 1.79 | 28.01 | 27.60 | 26.51 |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B | nvfp4 | 9.60 | 1.09 | 69.34 | 68.89 | 61.62 |

> `gen` 為純解碼 tokens/s (`eval_count / eval_duration`,越大越快)。受 KV cache 命中影響極小,是最穩定的速度指標。

## Prefill 主表 — 冷啟 (run 1, KV cache 未命中)

Ollama 對相同 prompt 會重用 KV cache,所以第 2 次起的 prefill 不是真正的 prefill 速度。下表只取每個模型 long/xlong 的第一筆 (冷啟) 作為代表。

| 系列 | 模型 | short prompt tok/s | long prompt tok/s (cold) | xlong prompt tok/s (cold) | short TTFT (s) | long TTFT (s) cold | xlong TTFT (s) cold | xlong wall (s) cold |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.6 | `qwen3.6:35b` | 217.07 | 402.74 | 562.50 | 0.212 | 0.475 | 23.87 | 30.52 |
| Qwen3.6 | `qwen3.6:27b` | 73.16 | 106.13 | 116.00 | 0.458 | 1.517 | 98.22 | 120.95 |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 82.32 | 190.56 | 413.21 | 0.344 | 0.810 | 26.81 | 53.49 |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 138.62 | 243.73 | 455.78 | 0.216 | 0.639 | 24.31 | 40.78 |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 477.67 | 326.68 | 1908.08 | 0.079 | 0.482 | 5.83 | 10.34 |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 662.03 | 434.54 | 2057.40 | 0.063 | 0.367 | 5.41 | 8.85 |
| Gemma4 | `gemma4:e4b` | 1382.82 | 735.24 | 736.34 | 2.728 | 5.766 | 0.00 | 21.29 |
| Gemma4 | `gemma4:e4b-it-bf16` | 756.27 | 746.10 | 782.36 | 5.660 | 13.574 | 0.00 | 27.57 |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 497.21 | 980.52 | 3721.14 | 5.627 | 15.013 | 0.00 | 12.64 |
| Gemma4 | `gemma4:e4b-nvfp4` | 1434.16 | 1873.90 | 4205.55 | 1.603 | 6.672 | 6.64 | 6.86 |

> xlong prompt 約 11064 tokens; TTFT 為 client 收到第一個 token 的 wall-clock 秒數。
> ⚠️ Gemma4 系列的 xlong TTFT 顯示 0.00s 是量測 bug — gemma4 的串流首 chunk 行為與 qwen 不同,不含 response/thinking 字串,導致客戶端的 TTFT 偵測未觸發。請以 `xlong wall` 減去 `eval_count / xlong_gen` 推算實際 TTFT。

## 排名

### short prompt 解碼速度

| 排名 | 系列 | 模型 | short gen tok/s |
|---:|---|---|---:|
| 1 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 80.61 |
| 2 | Gemma4 | `gemma4:e4b-nvfp4` | 69.34 |
| 3 | Gemma4 | `gemma4:e4b` | 68.56 |
| 4 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | Qwen3.6 | `qwen3.6:35b` | 41.68 |
| 6 | Gemma4 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | Qwen3.6 | `qwen3.6:27b` | 11.82 |
| 10 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.89 |

### long prompt 解碼速度

| 排名 | 系列 | 模型 | long gen tok/s |
|---:|---|---|---:|
| 1 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 80.74 |
| 2 | Gemma4 | `gemma4:e4b-nvfp4` | 68.89 |
| 3 | Gemma4 | `gemma4:e4b` | 68.30 |
| 4 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.47 |
| 5 | Qwen3.6 | `qwen3.6:35b` | 41.71 |
| 6 | Gemma4 | `gemma4:e4b-it-bf16` | 28.13 |
| 7 | Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 27.60 |
| 8 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 16.30 |
| 9 | Qwen3.6 | `qwen3.6:27b` | 11.82 |
| 10 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.86 |

### xlong (16k 上下文) 解碼速度

| 排名 | 系列 | 模型 | xlong gen tok/s | 平均 prompt tokens |
|---:|---|---|---:|---:|
| 1 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 73.97 | 11064 |
| 2 | Gemma4 | `gemma4:e4b` | 62.01 | 11042 |
| 3 | Gemma4 | `gemma4:e4b-nvfp4` | 61.62 | 11042 |
| 4 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 56.48 | 11064 |
| 5 | Qwen3.6 | `qwen3.6:35b` | 39.05 | 11064 |
| 6 | Gemma4 | `gemma4:e4b-it-bf16` | 26.87 | 11042 |
| 7 | Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 26.51 | 11042 |
| 8 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 15.53 | 11064 |
| 9 | Qwen3.6 | `qwen3.6:27b` | 11.32 | 11064 |
| 10 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.59 | 11064 |

### long prompt 冷啟 prefill 速度 (吃 prompt 能力)

| 排名 | 系列 | 模型 | long prompt tok/s (cold) |
|---:|---|---|---:|
| 1 | Gemma4 | `gemma4:e4b-nvfp4` | 1873.90 |
| 2 | Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 980.52 |
| 3 | Gemma4 | `gemma4:e4b-it-bf16` | 746.10 |
| 4 | Gemma4 | `gemma4:e4b` | 735.24 |
| 5 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 434.54 |
| 6 | Qwen3.6 | `qwen3.6:35b` | 402.74 |
| 7 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 326.68 |
| 8 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 243.73 |
| 9 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 190.56 |
| 10 | Qwen3.6 | `qwen3.6:27b` | 106.13 |

### xlong (11k tokens) 冷啟 prefill 速度

| 排名 | 系列 | 模型 | xlong prompt tok/s (cold) | xlong wall (s) |
|---:|---|---|---:|---:|
| 1 | Gemma4 | `gemma4:e4b-nvfp4` | 4205.55 | 6.86 |
| 2 | Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 3721.14 | 12.64 |
| 3 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 | 8.85 |
| 4 | Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 | 10.34 |
| 5 | Gemma4 | `gemma4:e4b-it-bf16` | 782.36 | 27.57 |
| 6 | Gemma4 | `gemma4:e4b` | 736.34 | 21.29 |
| 7 | Qwen3.6 | `qwen3.6:35b` | 562.50 | 30.52 |
| 8 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 455.78 | 40.78 |
| 9 | Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 413.21 | 53.49 |
| 10 | Qwen3.6 | `qwen3.6:27b` | 116.00 | 120.95 |

<!-- mlx-caveat:v1 -->
## ⚠️ MLX 對照組精確說明

10 個受測模型中,有 5 個是 MLX 變體(🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

對下面「dense 27b-coding-mxfp8 異常」與「Gemma4 系列」這兩段觀察的精確讀法:

- **「dense 27b-coding-mxfp8 異常」**:對比是 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs 非 MLX 的 `qwen3.6:27b` Q4_K_M (11.82 tok/s)。精準說法:**Ollama Metal backend 上的 MLX mxfp8 路徑比 base GGUF Q4_K_M 路徑慢**,雖然檔案還大 1.8 倍。
- **「Gemma4 系列 — `mlx-bf16` 對解碼沒幫助但 prefill 大幅領先」**:這個結論只能由 gemma4 對比得出(🍎 `gemma4:e4b-mlx-bf16` vs 非 MLX 的 `gemma4:e4b-it-bf16`,兩者都是 BF16)。Qwen3.6 系列的 `-coding-mxfp8` / `-coding-nvfp4` *兩個都是* MLX,所以那邊的 nvfp4 vs mxfp8 比較是 **MLX 內部的量化差異**,不是隔離 MLX 路徑本身的效應。

簡言之:🍎 = MLX 變體;本實驗組唯一一組真正「MLX vs 非 MLX、其他不變」的乾淨對比是 gemma4 的 BF16 兩個。

## 觀察與分析

### 1. MoE vs Dense (Qwen3.6 內部)
- `35b-a3b-coding-nvfp4` (MoE, 3B active)：80.6 tok/s short
- `35b` (dense)：41.7 tok/s short
- 兩者參數量相近 (35–36B),但 MoE 推論時只啟用 3B → 解碼速度幾乎兩倍。

### 2. 量化格式：nvfp4 vs mxfp8 (Qwen3.6)
同架構 `35b-a3b-coding`：
- nvfp4：80.6 tok/s short / 21 GB
- mxfp8：60.4 tok/s short / 37 GB
- nvfp4 解碼 +33%、模型檔 -43%。

同架構 `27b-coding`：
- nvfp4：16.3 tok/s short / 19 GB
- mxfp8：9.9 tok/s short / 31 GB
- nvfp4 解碼 +65%、模型檔 -39%。

### 3. dense 27b-coding-mxfp8 的異常
`27b-coding-mxfp8` (9.9 tok/s) 比原版 `qwen3.6:27b` Q4_K_M (11.8 tok/s) 還慢,且檔案大 1.8 倍。
- mxfp8 在 Apple Silicon 的 Metal backend 上沒有原生加速。
- 推論：在 M5 Pro 上跑 27b dense 程式碼模型應選 nvfp4 (16.3 tok/s)。

### 4. Gemma4 系列 — 量化對 prefill vs 解碼的影響
Gemma4 e4b 4 個變體解碼速度只有 2 個層級 (4-bit ~68, BF16 ~28),但 prefill 卻有顯著差異：

| 變體 | 大小 | 解碼 (short) | xlong cold prefill | xlong wall (s) |
|---|---:|---:|---:|---:|
| `gemma4:e4b` | 9.60 GB | 68.56 | 736.34 | 21.29 |
| `gemma4:e4b-it-bf16` | 16.00 GB | 28.42 | 782.36 | 27.57 |
| 🍎 `gemma4:e4b-mlx-bf16` | 16.00 GB | 28.01 | 3721.14 | 12.64 |
| `gemma4:e4b-nvfp4` | 9.60 GB | 69.34 | 4205.55 | 6.86 |

**關鍵發現**：
- **解碼 = 記憶體頻寬綁住**：4-bit (e4b, e4b-nvfp4) 都是 ~68 tok/s,BF16 (it-bf16, mlx-bf16) 都是 ~28 tok/s。一個模型 weights 走過記憶體一次/token,bytes 越少越快。
- **Prefill = compute 綁住,quant kernel 重要**：
  - `e4b-nvfp4` 的 xlong prefill 4206 tok/s 是同樣 9.6 GB 的 `e4b` Q4-equivalent (736 tok/s) 的 **5.7 倍**。
  - `e4b-mlx-bf16` 的 xlong prefill 3721 tok/s 是同樣 16 GB 的 `e4b-it-bf16` (782 tok/s) 的 **4.8 倍**。
  - 同 quant 用 mlx-friendly 格式或 nvfp4 路徑,prefill 速度提升 5x 級別。
- 對於長 prompt (RAG、code review、長文翻譯),quant 格式對 TTFT 的影響比解碼速度還大。

### 5. 跨系列：Gemma4 8B vs Qwen 27B / 35B
解碼速度排序：
  1. 🍎 `qwen3.6:35b-a3b-coding-nvfp4` (Qwen3.6) — 80.61 tok/s
  2. `gemma4:e4b-nvfp4` (Gemma4) — 69.34 tok/s
  3. `gemma4:e4b` (Gemma4) — 68.56 tok/s
  4. 🍎 `qwen3.6:35b-a3b-coding-mxfp8` (Qwen3.6) — 60.41 tok/s
  5. `qwen3.6:35b` (Qwen3.6) — 41.68 tok/s

`gemma4:e4b-nvfp4` (8B nvfp4, 9.6 GB) 排第 2,只比 🍎 `qwen3.6:35b-a3b-coding-nvfp4` (35B MoE, 21 GB) 慢 16%。
但前者參數量是後者的 1/4,品質應較弱。模型大小通常壓過 quant 與架構優化的速度差。

### 6. 長上下文懲罰 (短 prompt → 11k token prompt)

| 模型 | short → xlong | 衰減 |
|---|---|---:|
| `qwen3.6:35b` | 41.68 → 39.05 | -6.3% |
| `qwen3.6:27b` | 11.82 → 11.32 | -4.3% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 9.89 → 9.59 | -3.0% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.34 → 15.53 | -5.0% |
| 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 → 56.48 | -6.5% |
| 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 80.61 → 73.97 | -8.2% |
| `gemma4:e4b` | 68.56 → 62.01 | -9.6% |
| `gemma4:e4b-it-bf16` | 28.42 → 26.87 | -5.4% |
| 🍎 `gemma4:e4b-mlx-bf16` | 28.01 → 26.51 | -5.4% |
| `gemma4:e4b-nvfp4` | 69.34 → 61.62 | -11.1% |

所有模型衰減都在 4–10%,M5 Pro 的記憶體頻寬對 16k context 仍很穩。

### 7. Gemma4 的 TTFT 異常
Gemma4 系列在 short prompt 下 TTFT 介於 1.6–5.7s,而 prefill 32 token / 1400 tok/s ≈ 0.02s。
差距 1.5–5.7s 不在 prefill,可能是 ollama 對 gemma3-style chat template 處理或某種延遲首 chunk 的行為。
xlong run 中,gemma4 的 TTFT 量測都顯示 0.00s — 這是 client 串流端偵測 bug:gemma4 的首 chunk 不含 response/thinking 字串,客戶端的 first-token 偵測未觸發。**真實 TTFT 請以 `xlong wall - eval_count / xlong_gen` 推算**。

## 與 run1 (Automatic powermode) 的對照 — 僅 Qwen 系列

上一輪在 `powermode=0` (Automatic) 下執行,未鎖定 High Power。

| 模型 | run1 short gen | run2 short gen (High Power) | 增幅 |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

> nvfp4 在 Automatic 模式下幾乎已跑滿,dense 模型則受 powermode 影響極大。建議任何需要可重現的速度量測都先把 macOS 切到 High Power (`sudo pmset -a powermode 2`)。

## 指標說明

- **gen tok/s**：純解碼 tokens/s (`eval_count / eval_duration`)。受 KV cache 命中影響極小,是最穩定的速度指標。
- **prompt tok/s**：prefill 速度。⚠️ Ollama 在相同 prompt 連續送出時會直接重用 KV cache,第 2 次起的數值會異常巨大 (cache hit)。本報告用「冷啟 (run 1)」代表真正的 prefill 速度。
- **TTFT**：client 收到第一個 token 的 wall-clock 秒數。受 prompt 長度與 prefill 速度雙重影響。⚠️ Gemma4 xlong TTFT 為量測 bug,請看 `xlong wall`。
- **冷啟 (load)**：模型剛載入記憶體後第一次 forward 的時間。
- **xlong**：~11k tokens 合成語料 + `num_ctx=16384` 量測長上下文 prefill 與解碼速度。

