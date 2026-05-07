# M5 Pro LLM Benchmark — Ollama、MLX 與量化的影響

**Languages**: [English](./README.md) · **繁體中文** · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

這個 repo 量測 **Apple M5 Pro / 64 GB** 在 [Ollama](https://ollama.com) 上跑 10 個本地 LLM 的速度,重點比較:

- **MoE 對 dense** 的解碼速度差距(Qwen3.6 35b-a3b vs 35b dense)
- **量化格式**對 prefill 與解碼的不同影響(Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX 變體 vs 一般 BF16** 在 Ollama 上的 prefill 差距
- **macOS High Power 模式**對效能的決定性影響

> **TL;DR**:在 M5 Pro 上跑這些模型,**模型大小 > 量化格式 > 架構優化**;解碼受記憶體頻寬綁住、prefill 受 quant kernel 綁住,兩者規律完全不同。詳細數據看 [REPORT.md](./REPORT.md)。

## 受測模型(10 個)

| 系列 | 模型 | 參數 | 量化 | 模型檔大小 |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B active) | mxfp8 | 37 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B active) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## 主要結果

### Short prompt 解碼速度排名(5 次取樣平均)

| 排名 | 模型 | tok/s |
|---:|---|---:|
| 1 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | 🍎 `qwen3.6:27b-coding-mxfp8` | 9.89 |

### xlong(11k tokens)冷啟 prefill 速度排名

| 排名 | 模型 | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | 🍎 `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | 🍎 `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | 🍎 `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## 重點發現

### 1. 解碼 vs Prefill 的瓶頸不同

- **解碼受記憶體頻寬綁住**:模型 weights 每生成一個 token 就要走過記憶體一次。Gemma4 e4b 的 4-bit (e4b, e4b-nvfp4) 都是 ~68 tok/s;BF16 (it-bf16, mlx-bf16) 都是 ~28 tok/s。**慢 2.4 倍剛好對應 weight 大小 2 倍**。
- **Prefill 受 compute 與 quant kernel 綁住**:同樣 4-bit、同樣 9.6 GB 的 e4b vs e4b-nvfp4 解碼幾乎相同,但 nvfp4 的 cold xlong prefill **快 5.7 倍**(4206 vs 736 tok/s)。

### 2. nvfp4 是這台 M5 Pro 上的全方位贏家

- 同架構下 nvfp4 解碼 +33%~+65%、模型檔小 39%~43%。
- 在 Gemma4 上 nvfp4 對解碼幾乎沒幫助,但 prefill 快 5x 級別。
- 結論:**只要有 nvfp4 版就選 nvfp4**。

### 3. mxfp8 在 Apple Silicon 是地雷

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) **比原版 Q4_K_M (11.82 tok/s) 還慢**,且檔案大 1.8 倍——mxfp8 在 Metal backend 上沒有原生加速。

### 4. MLX 標籤對解碼沒用,但 prefill 大幅領先

🍎 `gemma4:e4b-mlx-bf16` 與 `gemma4:e4b-it-bf16` 解碼都是 ~28 tok/s,但 cold xlong prefill 是 **3721 vs 782 tok/s(4.8 倍)**。長 prompt 場景優先選 MLX 變體;短 prompt 完全沒差。

### 5. MoE 在 M5 Pro 上很有價值

`qwen3.6:35b-a3b` (3B active) 解碼 **~80 tok/s**,是同 35B 級 dense (`qwen3.6:35b` 41.68) 的兩倍。MoE 推論時 weights 走過記憶體只有 3B,剛好對齊「解碼受記憶體頻寬綁住」這條規律。

### 6. macOS 電源模式對 dense 模型影響極大

| 模型 | Automatic (run1) | High Power (run2) | 增幅 |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**精準量測必須先鎖 High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k 長上下文懲罰很小

所有 10 個模型從 short → 11k token xlong 解碼速度只衰減 **4–10%**。Apple M5 Pro / 64 GB 對 16k context 仍未撞瓶頸,KV cache 容量充足。

## 測試環境

- **硬體**:MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB Unified Memory
- **OS**:Darwin 25.5.0 (macOS 26)
- **Ollama**:v0.21.0
- **電源**:AC 供電,`pmset powermode=2`(High Power)
- **防睡眠**:`caffeinate -dimsu` 全程啟用
- **Python**:3.14

## 量測方法

完整腳本見 [`bench.py`](./bench.py)。關鍵設計:

- 每模型先 `keep_alive=0` 卸載、cold-start、warmup,再正式取樣
- 全部 `temperature=0` `seed=42` `keep_alive=10m`,確保可重現
- 三段 prompt:
  - **short** × 5:26~32 token prompt → `num_predict=256`
  - **long** × 4:149~156 token prompt → `num_predict=512`
  - **xlong** × 3:~11k token prompt → `num_predict=256`、強制 `num_ctx=16384`
- 純解碼速度用伺服器回報的 `eval_count / eval_duration`,**不受 KV cache 命中影響**
- Prefill 速度只取每模型 long/xlong 的 **第一筆**(cold prefill),避免 Ollama 對相同 prompt 的 KV cache 重用污染平均值

> ⚠️ Ollama 對相同 prompt 連續送出時會直接重用 KV cache,第 2 次起的 `prompt_eval_duration` 會異常巨大(cache hit)。本專案的報告把 prefill 拆成「冷啟 (run 1)」與「快取命中 (run 2+)」兩列。

## 重現步驟

```bash
# 1. 切到 High Power
sudo pmset -a powermode 2

# 2. 確保 ollama 服務在跑
curl -s http://localhost:11434/api/version

# 3. 拉模型
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. 防系統睡眠並執行 benchmark
caffeinate -dimsu -t 18000 &
python3 bench.py \
  --models qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
           qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
           qwen3.6:35b-a3b-coding-nvfp4 \
           gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4 \
  --output-dir results \
  --short-runs 5 --long-runs 4 --xlong-runs 3 \
  --short-predict 256 --long-predict 512 --xlong-predict 256 \
  --xlong-num-ctx 16384

# 5. 產生對比報告
python3 render_report.py
```

## 檔案結構

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # 12 種語言版本
├── REPORT.md                        # 完整對比報告
├── bench.py                         # 量測腳本
├── render_report.py                 # 後處理(results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 個 Qwen3.6 模型 — 原始 + 摘要
    └── gemma4_*.json / .md          # 4 個 Gemma4 模型 — 原始 + 摘要
```

## 已知量測限制

- **Gemma4 系列在 short prompt 下 TTFT 偏高(1.6–5.7s)**:與 prefill 時間 (32 / ~1400 ≈ 0.02s) 不成比例,可能是 Ollama 對 gemma3-style chat template 的處理。
- **Gemma4 xlong TTFT 顯示 0.00s 是 client 端串流偵測 bug**:gemma4 串流首 chunk 不含 `response`/`thinking` 字串,客戶端的 first-token 偵測未觸發。實際 TTFT 應該以 `xlong wall - eval_count / xlong_gen` 推算。
- **Ollama 的 KV cache 重用**:同一 prompt 第 2 次起 prefill 幾乎免費,本專案的 prefill 數值只取每組第一筆冷啟。

## 授權

CC BY-SA 4.0。歡迎引用、修改、再發佈,請標註來源。

## 後話

如果你也是 M5 Pro 用戶,想跑類似的測試或追加模型(例如 Llama 3.3、DeepSeek、Phi 4),歡迎開 PR 或 issue。如果你的硬體不一樣(M4 / M3 Max / Studio),跑一份相同設定的數據也很有價值。
