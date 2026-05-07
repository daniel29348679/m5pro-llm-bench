# M5 Pro LLM ベンチマーク — Ollama、MLX、量子化の影響

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · **日本語** · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

このリポジトリは **Apple M5 Pro / 64 GB** 上で [Ollama](https://ollama.com) を使い、10 個のローカル LLM の速度を計測します。重点比較項目:

- **MoE と dense** のデコード速度差(Qwen3.6 35b-a3b vs 35b dense)
- **量子化フォーマット**が prefill とデコードに与える異なる影響(Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX タグ付き BF16 vs 通常の BF16** の prefill 性能差
- **macOS High Power モード**がスループットに与える決定的影響

> **TL;DR**:M5 Pro 上では **モデルサイズ > 量子化 > アーキテクチャ最適化**。デコードはメモリ帯域でボトルネック、prefill は量子化カーネルでボトルネック — 完全に異なる規則に従います。詳細は [REPORT.md](./REPORT.md) を参照。

## 計測対象モデル(10 個)

| ファミリー | モデル | パラメータ | 量子化 | モデルサイズ |
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

### Short prompt デコード速度ランキング(5 サンプル平均)

| 順位 | モデル | tok/s |
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

### xlong(11k tokens)コールド prefill 速度

| 順位 | モデル | prefill tok/s |
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

## 主な発見

### 1. デコードと Prefill のボトルネックが異なる

- **デコードはメモリ帯域でボトルネック**:1 トークン生成するたびにモデルの重み全体がメモリを通過する必要がある。Gemma4 e4b の 4-bit 系(e4b, e4b-nvfp4)はすべて ~68 tok/s、BF16 系(it-bf16, mlx-bf16)はすべて ~28 tok/s。**2.4 倍遅いのは weight サイズが 2 倍であることに正確に対応**。
- **Prefill は計算と量子化カーネルでボトルネック**:同じ 4-bit、同じ 9.6 GB の e4b と e4b-nvfp4 のデコードはほぼ同じだが、nvfp4 のコールド xlong prefill は **5.7 倍速い**(4206 vs 736 tok/s)。

### 2. nvfp4 はこの M5 Pro での万能勝者

- 同じアーキテクチャで nvfp4 はデコード +33%~+65%、モデルファイル -39%~-43%。
- Gemma4 では nvfp4 はデコードにはほぼ寄与しないが、prefill は ~5 倍速くなる。
- 結論:**nvfp4 版があれば必ず nvfp4 を選ぶ**。

### 3. mxfp8 は Apple Silicon の地雷

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) は **元の Q4_K_M (11.82 tok/s) より遅い**、しかもファイルは 1.8 倍大きい — mxfp8 は Metal backend のネイティブ加速がない。

### 4. MLX タグはデコードには効かないが、prefill が ~5 倍速い

🍎 `gemma4:e4b-mlx-bf16` と `gemma4:e4b-it-bf16` のデコードは同じ ~28 tok/s だが、コールド xlong prefill は **3721 vs 782 tok/s(4.8 倍)**。長プロンプトが多いシナリオでのみ MLX 版を選ぶ。

### 5. MoE は M5 Pro でとても有効

`qwen3.6:35b-a3b` (3B active) はデコード **~80 tok/s**、同等の dense `qwen3.6:35b` (41.68) の 2 倍速い。MoE は推論時に 3B 分の重みしかメモリを通過しないため、メモリ帯域ボトルネックに完全に整合する。

### 6. macOS 電源モードは dense モデルに大きく影響

| モデル | Automatic (run1) | High Power (run2) | 増加率 |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**再現可能なベンチマークには High Power をロックすべし**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k 長コンテキストのペナルティは小さい

10 モデルすべてで short → 11k トークン xlong のデコード速度低下は **4–10%** のみ。Apple M5 Pro / 64 GB は 16k コンテキストでもまだ余裕がある。

## テスト環境

- **ハードウェア**:MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB ユニファイドメモリ
- **OS**:Darwin 25.5.0 (macOS 26)
- **Ollama**:v0.21.0
- **電源**:AC、`pmset powermode=2`(High Power)
- **スリープ防止**:`caffeinate -dimsu` を計測中ずっと有効
- **Python**:3.14

## 計測手法

完全なスクリプトは [`bench.py`](./bench.py) を参照。設計の要点:

- 各モデル:`keep_alive=0` でアンロード → cold-start → warmup → 計測
- すべて `temperature=0` `seed=42` `keep_alive=10m` で再現性を確保
- 3 つのプロンプト長:
  - **short** × 5:26~32 トークン → `num_predict=256`
  - **long** × 4:149~156 トークン → `num_predict=512`
  - **xlong** × 3:~11k トークン → `num_predict=256`、`num_ctx=16384` を強制
- デコード tok/s = サーバ報告の `eval_count / eval_duration`、**KV cache hit の影響を受けない**
- Prefill tok/s は各モデルの long/xlong **最初の 1 回**(コールド prefill)のみ採用 — Ollama は同一プロンプトで KV cache を再利用するため、2 回目以降の prefill 数値は異常に大きくなる(100k+ tok/s)。

## 再現手順

```bash
# 1. High Power をロック
sudo pmset -a powermode 2

# 2. ollama サーバ確認
curl -s http://localhost:11434/api/version

# 3. モデル取得
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. スリープ防止 + 計測実行
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

# 5. レポート生成
python3 render_report.py
```

## ファイル構成

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # 12 言語版
├── REPORT.md                        # 完全比較レポート
├── bench.py                         # 計測スクリプト
├── render_report.py                 # 後処理(results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 個の Qwen3.6 モデル — 生データ + 要約
    └── gemma4_*.json / .md          # 4 個の Gemma4 モデル — 生データ + 要約
```

## 既知の計測上の制限

- **Gemma4 系列の short prompt TTFT が高い(1.6–5.7s)**:prefill 時間 (32 / ~1400 ≈ 0.02s) と釣り合わない。Ollama 側の gemma3-style chat template 処理の可能性。
- **Gemma4 xlong TTFT が 0.00s と表示されるのはクライアント側ストリーミング検出のバグ**:gemma4 の最初のチャンクは `response`/`thinking` 文字列を含まないため、クライアントの first-token 検出器がトリガーされない。実際の TTFT は `xlong wall - eval_count / xlong_gen` で逆算する。
- **Ollama の KV cache 再利用**:同じプロンプトの 2 回目以降は prefill がほぼ無料。本プロジェクトの prefill 値は最初の 1 回(コールド)のみ採用。

## ライセンス

CC BY-SA 4.0。引用、改変、再配布は自由(出典明記)。

## コントリビューション

他の M5 Pro オーナーで追加モデル(Llama 3.3、DeepSeek、Phi 4 など)を試したい方、PR や issue 歓迎。異なるハードウェア(M4 / M3 Max / Studio)で同じ設定のデータを取ってもらえると非常に価値があります。
