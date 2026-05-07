# M5 Pro LLM Benchmark — Ollama、MLX 与量化的影响

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · **简体中文** · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

本仓库测试 **Apple M5 Pro / 64 GB** 在 [Ollama](https://ollama.com) 上运行 10 个本地 LLM 的速度,重点比较:

- **MoE 对 dense** 的解码速度差距(Qwen3.6 35b-a3b vs 35b dense)
- **量化格式**对 prefill 与解码的不同影响(Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX 变体 vs 普通 BF16** 在 Ollama 上的 prefill 差距
- **macOS High Power 模式**对性能的决定性影响

> **TL;DR**:在 M5 Pro 上跑这些模型,**模型大小 > 量化格式 > 架构优化**;解码受内存带宽绑住、prefill 受 quant kernel 绑住,两者规律完全不同。详细数据见 [REPORT.md](./REPORT.md)。

## 受测模型(10 个)

| 系列 | 模型 | 参数 | 量化 | 模型文件大小 |
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

## 主要结果

### Short prompt 解码速度排名(5 次取样平均)

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

### xlong(11k tokens)冷启 prefill 速度排名

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

## 重点发现

### 1. 解码 vs Prefill 的瓶颈不同

- **解码受内存带宽绑住**:模型 weights 每生成一个 token 就要走过内存一次。Gemma4 e4b 的 4-bit (e4b, e4b-nvfp4) 都是 ~68 tok/s;BF16 (it-bf16, mlx-bf16) 都是 ~28 tok/s。**慢 2.4 倍刚好对应 weight 大小 2 倍**。
- **Prefill 受 compute 与 quant kernel 绑住**:同样 4-bit、同样 9.6 GB 的 e4b vs e4b-nvfp4 解码几乎相同,但 nvfp4 的 cold xlong prefill **快 5.7 倍**(4206 vs 736 tok/s)。

### 2. nvfp4 是这台 M5 Pro 上的全方位赢家

- 同架构下 nvfp4 解码 +33%~+65%、模型文件小 39%~43%。
- 在 Gemma4 上 nvfp4 对解码几乎没帮助,但 prefill 快 5x 级别。
- 结论:**只要有 nvfp4 版就选 nvfp4**。

### 3. mxfp8 在 Apple Silicon 是地雷

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) **比原版 Q4_K_M (11.82 tok/s) 还慢**,且文件大 1.8 倍——mxfp8 在 Metal backend 上没有原生加速。

### 4. MLX 标签对解码没用,但 prefill 大幅领先

🍎 `gemma4:e4b-mlx-bf16` 与 `gemma4:e4b-it-bf16` 解码都是 ~28 tok/s,但 cold xlong prefill 是 **3721 vs 782 tok/s(4.8 倍)**。长 prompt 场景优先选 MLX 变体;短 prompt 完全没差。

### 5. MoE 在 M5 Pro 上很有价值

`qwen3.6:35b-a3b` (3B active) 解码 **~80 tok/s**,是同 35B 级 dense (`qwen3.6:35b` 41.68) 的两倍。MoE 推理时 weights 走过内存只有 3B,刚好对齐「解码受内存带宽绑住」这条规律。

### 6. macOS 电源模式对 dense 模型影响极大

| 模型 | Automatic (run1) | High Power (run2) | 增幅 |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**精准测量必须先锁 High Power**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k 长上下文惩罚很小

所有 10 个模型从 short → 11k token xlong 解码速度只衰减 **4–10%**。Apple M5 Pro / 64 GB 对 16k context 仍未撞瓶颈,KV cache 容量充足。

<!-- mlx-caveat:v1 -->
## ⚠️ MLX 对照组精确说明 — 引用 finding 3 / 4 前必读

10 个受测模型中,有 5 个是 MLX 变体(🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

对 finding 3 / 4 的精确读法:

- **Finding 3「mxfp8 是地雷」**:对比是 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs 非 MLX 的 `qwen3.6:27b` Q4_K_M (11.82 tok/s)。精准说法:**Ollama Metal backend 上的 MLX mxfp8 路径比 base GGUF Q4_K_M 路径慢**,尽管文件还大 1.8 倍。
- **Finding 4「MLX 标签对解码没用,但 prefill 大幅领先」**:只有 gemma4 那组是干净的「MLX vs 非 MLX 同 BF16」对比(🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`)。Qwen3.6 的 `-coding-mxfp8` / `-coding-nvfp4` *两个都是* MLX,所以那边的 nvfp4-vs-mxfp8 对比其实是 **MLX 内部的量化差异**,不是隔离 MLX 路径本身的效应。

简言之:🍎 = MLX 变体;本实验组唯一真正「MLX vs 非 MLX、其他不变」的干净对比是 gemma4 的 BF16 两个。

## 测试环境

- **硬件**:MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB 统一内存
- **OS**:Darwin 25.5.0 (macOS 26)
- **Ollama**:v0.21.0
- **电源**:AC 供电,`pmset powermode=2`(High Power)
- **防睡眠**:`caffeinate -dimsu` 全程启用
- **Python**:3.14

## 测量方法

完整脚本见 [`bench.py`](./bench.py)。关键设计:

- 每模型先 `keep_alive=0` 卸载、cold-start、warmup,再正式取样
- 全部 `temperature=0` `seed=42` `keep_alive=10m`,确保可重现
- 三段 prompt:
  - **short** × 5:26~32 token prompt → `num_predict=256`
  - **long** × 4:149~156 token prompt → `num_predict=512`
  - **xlong** × 3:~11k token prompt → `num_predict=256`、强制 `num_ctx=16384`
- 纯解码速度用服务器回报的 `eval_count / eval_duration`,**不受 KV cache 命中影响**
- Prefill 速度只取每模型 long/xlong 的 **第一笔**(cold prefill),避免 Ollama 对相同 prompt 的 KV cache 重用污染平均值

> ⚠️ Ollama 对相同 prompt 连续送出时会直接重用 KV cache,第 2 次起的 `prompt_eval_duration` 会异常巨大(cache hit)。本项目的报告把 prefill 拆成「冷启 (run 1)」与「缓存命中 (run 2+)」两列。

## 重现步骤

```bash
# 1. 切到 High Power
sudo pmset -a powermode 2

# 2. 确保 ollama 服务在跑
curl -s http://localhost:11434/api/version

# 3. 拉模型
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. 防系统睡眠并执行 benchmark
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

# 5. 产生对比报告
python3 render_report.py
```

## 文件结构

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # 12 种语言版本
├── REPORT.md                        # 完整对比报告
├── bench.py                         # 测量脚本
├── render_report.py                 # 后处理(results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 个 Qwen3.6 模型 — 原始 + 摘要
    └── gemma4_*.json / .md          # 4 个 Gemma4 模型 — 原始 + 摘要
```

## 已知测量限制

- **Gemma4 系列在 short prompt 下 TTFT 偏高(1.6–5.7s)**:与 prefill 时间 (32 / ~1400 ≈ 0.02s) 不成比例,可能是 Ollama 对 gemma3-style chat template 的处理。
- **Gemma4 xlong TTFT 显示 0.00s 是 client 端流式检测 bug**:gemma4 流式首 chunk 不含 `response`/`thinking` 字符串,客户端的 first-token 检测未触发。实际 TTFT 应该以 `xlong wall - eval_count / xlong_gen` 推算。
- **Ollama 的 KV cache 重用**:同一 prompt 第 2 次起 prefill 几乎免费,本项目的 prefill 数值只取每组第一笔冷启。

## 许可

CC BY-SA 4.0。欢迎引用、修改、再发布,请标注来源。

## 后记

如果你也是 M5 Pro 用户,想跑类似的测试或追加模型(例如 Llama 3.3、DeepSeek、Phi 4),欢迎开 PR 或 issue。如果你的硬件不一样(M4 / M3 Max / Studio),跑一份相同设定的数据也很有价值。
