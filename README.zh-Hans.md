# M5 Pro LLM Benchmark — Ollama 0.30.6 模型选择

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · **简体中文** · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

这个 repo 测试 **Apple M5 Pro / 64 GB** 在 [Ollama](https://ollama.com) 上运行本地 LLM 的吞吐量。当前结果使用 **Ollama 0.30.6** 和这台机器上已安装的模型；旧的 10 模型完整测试保留在 [REPORT.md](./REPORT.md) 作为历史资料。

## 快速选择

| 情况 | 直接选 | 原因 |
|---|---|---|
| 当前最快的本地 Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M`，`draft_num_predict=4` | 最高实测解码速度到 **87.97 tokens/s** |
| 你要用 Gemma | `gemma4:26b-nvfp4` | 当前已安装 Gemma 里速度最好 |
| 你需要较小的 Qwen MTP | `qwen3.6:27b-mtp-q4_K_M`，`draft_num_predict=4` | 模型文件 17 GB，但比 35B-a3B MTP 慢很多 |
| 你在调 MTP | 保持模型默认 `draft_num_predict=4` | 强制改成 `8` 两个 MTP 模型都变慢 |
| 你只看旧完整比较 | 看 [REPORT.md](./REPORT.md) | 原始 10 模型量化与 MLX 比较在那里 |

## 当前结果

| 模型 | 最适合用途 | 模型文件大小 (GB) | 短输出解码 (tokens/s) | 长输出解码 (tokens/s) | 11k 上下文解码 (tokens/s) | 数据来源 |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 当前最快 Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP 重测，draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | 非 MTP Qwen 备选 | 21 | 64.57 | 64.58 | 59.15 | 已安装模型测试 |
| `gemma4:26b-nvfp4` | 当前最快 Gemma | 16 | 59.16 | 58.33 | 49.07 | 已安装模型测试 |
| `qwen3.6:27b-mtp-q4_K_M` | 较小 Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP 重测，draft 4 |
| `gemma4:31b-nvfp4` | 不建议当速度首选 | 20 | 10.41 | 10.27 | 9.14 | 已安装模型测试 |

## MTP 预测 tokens

| 模型 | MTP 预测 tokens (`draft_num_predict`) | 短输出解码 (tokens/s) | 长输出解码 (tokens/s) | 11k 上下文解码 (tokens/s) | 相对 draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP 结论：**这台机器不要强制 `draft_num_predict=8`，用模型默认 `4`。

## 当前更新实测模型

| 系列 | 模型 | 参数 | 量化 | 模型文件大小 (GB) | 备注 |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | 当前赢家 |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | 较小 MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | 历史赢家，当前 run 较慢 |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | 当前 Gemma 最佳结果 |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | 这次速度慢 |

## 测试形状

| 测试场景 | Prompt 长度 (tokens) | 生成上限 (`num_predict`, tokens) | 取样次数 |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | 约 11,000，`num_ctx=16384` | 256 | 3 |

解码速度采用 Ollama server 回报的 `eval_count / eval_duration`。测试时锁定 High Power：`pmset powermode=2`，并全程使用 `caffeinate -dimsu`。

## 历史资料重点

原始完整测试在 Ollama 0.21/run2 上跑 10 个模型。架构、量化、MLX 比较请以它作为历史对照：

| 历史发现 | 结果 |
|---|---|
| 旧测试短输出解码最快 | `qwen3.6:35b-a3b-coding-nvfp4`，**80.61 tokens/s** |
| 旧测试 11k cold prefill 最快 | `gemma4:e4b-nvfp4`，**4205.55 tokens/s** |
| Apple Silicon 注意事项 | `mxfp8` 文件更大，速度却比 Q4_K_M 慢 |
| MLX 注意事项 | 干净的 Gemma BF16 对照里，MLX 帮 prefill，不帮 decode |

## 原始结果

- [Ollama 0.30.6 已安装模型比较](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 重测](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 重测](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [历史 10 模型报告](./REPORT.md)

## 最后结论

没有特殊限制时，直接用 `qwen3.6:35b-a3b-mtp-q4_K_M`，并保持默认 `draft_num_predict=4`。只有明确要 Gemma 时才选 `gemma4:26b-nvfp4`。只有在 22 GB 模型文件不适合、比较在意 17 GB 文件大小时，才选 `qwen3.6:27b-mtp-q4_K_M`。不要把 MTP 预测 tokens 强制改成 `8`。
