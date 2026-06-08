# M5 Pro LLM Benchmark — Ollama 0.30.6 モデル選択

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · **日本語** · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

このリポジトリは **Apple M5 Pro / 64 GB** 上で [Ollama](https://ollama.com) のローカル LLM スループットを測定します。現在の結果は **Ollama 0.30.6** とこのマシンにインストール済みのモデルを使っています。古い 10 モデルの完全比較は履歴データとして [REPORT.md](./REPORT.md) に残しています。

## すぐ選ぶなら

| 状況 | 選ぶモデル | 理由 |
|---|---|---|
| 現在最速のローカル Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M`、`draft_num_predict=4` | 実測デコード速度が最大 **87.97 tokens/s** |
| Gemma を使いたい | `gemma4:26b-nvfp4` | 現在インストール済み Gemma の中で最速 |
| 小さめの Qwen MTP が必要 | `qwen3.6:27b-mtp-q4_K_M`、`draft_num_predict=4` | 17 GB だが 35B-a3B MTP よりかなり遅い |
| MTP を調整している | モデル既定の `draft_num_predict=4` のまま | `8` に強制すると両方の MTP モデルで遅くなった |
| 古い完全比較だけ見たい | [REPORT.md](./REPORT.md) | 元の 10 モデル量子化・MLX 比較がある |

## 現在の結果

| モデル | 主な用途 | モデルファイルサイズ (GB) | Short デコード (tokens/s) | Long デコード (tokens/s) | 11k コンテキストデコード (tokens/s) | データソース |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 現在最速の Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP 再測定、draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | 非 MTP Qwen の代替 | 21 | 64.57 | 64.58 | 59.15 | インストール済みモデル測定 |
| `gemma4:26b-nvfp4` | 現在最速の Gemma | 16 | 59.16 | 58.33 | 49.07 | インストール済みモデル測定 |
| `qwen3.6:27b-mtp-q4_K_M` | 小さめの Qwen MTP baseline | 17 | 17.41 | 20.62 | 15.77 | MTP 再測定、draft 4 |
| `gemma4:31b-nvfp4` | 速度優先では非推奨 | 20 | 10.41 | 10.27 | 9.14 | インストール済みモデル測定 |

## MTP 予測 tokens

| モデル | MTP 予測 tokens (`draft_num_predict`) | Short デコード (tokens/s) | Long デコード (tokens/s) | 11k コンテキストデコード (tokens/s) | draft 4 比 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP 結論:** このマシンでは `draft_num_predict=8` を強制しない。モデル既定の `4` を使う。

## 現在の更新で測定したモデル

| ファミリー | モデル | パラメータ | 量子化 | モデルファイルサイズ (GB) | メモ |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | 現在の勝者 |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | 小さめの MTP baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | 履歴上の勝者、現在の run では低下 |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | 現在の Gemma 最良結果 |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | 今回は遅い |

## ベンチマーク条件

| ケース | Prompt 長 (tokens) | 生成上限 (`num_predict`, tokens) | サンプル数 |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | 約 11,000、`num_ctx=16384` | 256 | 3 |

デコード速度は Ollama server が返す `eval_count / eval_duration` です。High Power は `pmset powermode=2` で固定し、測定中は `caffeinate -dimsu` を使いました。

## 履歴データの要点

元の完全比較は Ollama 0.21/run2 で 10 モデルを測定しました。アーキテクチャ、量子化、MLX の比較には履歴対照として使ってください。

| 履歴上の発見 | 結果 |
|---|---|
| 古い short デコード最速 | `qwen3.6:35b-a3b-coding-nvfp4`、**80.61 tokens/s** |
| 古い 11k cold prefill 最速 | `gemma4:e4b-nvfp4`、**4205.55 tokens/s** |
| Apple Silicon 注意点 | `mxfp8` はファイルが大きいのに Q4_K_M より遅かった |
| MLX 注意点 | きれいな Gemma BF16 比較では、MLX は prefill に効き、decode には効かなかった |

## 生データ

- [Ollama 0.30.6 インストール済みモデル比較](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 再測定](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 再測定](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [履歴 10 モデルレポート](./REPORT.md)

## 最終結論

特別な制約がなければ、`qwen3.6:35b-a3b-mtp-q4_K_M` を使い、既定の `draft_num_predict=4` のままにする。Gemma が必要な場合だけ `gemma4:26b-nvfp4` を選ぶ。22 GB ファイルが合わず、17 GB の小ささを速度より重視する場合だけ `qwen3.6:27b-mtp-q4_K_M` を選ぶ。MTP 予測 tokens を `8` に強制しない。
