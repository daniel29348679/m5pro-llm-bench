# M5 Pro LLM Benchmark — Ollama, MLX und der Einfluss der Quantisierung

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · **Deutsch** · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Dieses Repo misst die Geschwindigkeit von **10 lokalen LLMs auf Apple M5 Pro / 64 GB** via [Ollama](https://ollama.com) und vergleicht:

- **MoE vs dense** Decodier-Geschwindigkeit (Qwen3.6 35b-a3b vs 35b dense)
- **Quantisierungsformate** und ihre unterschiedliche Wirkung auf Prefill vs Decode (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX-getaggtes BF16 vs gewöhnliches BF16** in Prefill-Performance
- Auswirkung des **macOS High-Power-Modus** auf Durchsatz

> **TL;DR**: Auf M5 Pro gilt **Modellgröße > Quantisierung > Architektur-Optimierung**. Decodieren ist speicherbandbreitenbegrenzt; Prefill ist quant-kernel-begrenzt — völlig unterschiedliche Regeln. Vollständige Daten in [REPORT.md](./REPORT.md).

## Getestete Modelle (10)

| Familie | Modell | Parameter | Quant | Größe |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B aktiv) | mxfp8 | 37 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B aktiv) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## Top-Ergebnisse

### Short-Prompt-Decodier-Geschwindigkeit (Mittel von 5 Samples)

| Rang | Modell | tok/s |
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

### xlong (~11k Token) Cold-Prefill-Geschwindigkeit

| Rang | Modell | prefill tok/s |
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

## Wichtigste Erkenntnisse

### 1. Decode und Prefill haben unterschiedliche Engpässe

- **Decode = speicherbandbreiten-gebunden**: Gewichte durchqueren den Speicher einmal pro Token. Gemma4 4-Bit-Varianten (e4b, e4b-nvfp4) decodieren alle bei ~68 tok/s; BF16 (it-bf16, mlx-bf16) bei ~28 tok/s. **2.4× langsamer entspricht exakt 2× Gewichtsgröße.**
- **Prefill = compute- und quant-kernel-gebunden**: Gleiches 4-Bit, gleiche 9.6 GB, e4b vs e4b-nvfp4 decodieren identisch — aber nvfp4s Cold-xlong-Prefill ist **5.7× schneller** (4206 vs 736 tok/s).

### 2. nvfp4 ist der Allround-Sieger auf diesem M5 Pro

- Innerhalb derselben Architektur decodiert nvfp4 33–65% schneller, bei 39–43% kleineren Dateien.
- Auf Gemma4 hilft nvfp4 dem Decodieren nicht, beschleunigt aber Prefill ~5×.
- Fazit: **Immer nvfp4 wählen, wenn verfügbar**.

### 3. mxfp8 ist eine Falle auf Apple Silicon

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) ist **langsamer als das Original Q4_K_M (11.82 tok/s)**, obwohl es 1.8× größer ist — mxfp8 hat keine native Metal-Backend-Beschleunigung.

### 4. Das MLX-Tag hilft beim Decode nicht, beschleunigt aber Prefill ~5×

🍎 `gemma4:e4b-mlx-bf16` und `gemma4:e4b-it-bf16` decodieren identisch bei ~28 tok/s, aber Cold-xlong-Prefill ist **3721 vs 782 tok/s (4.8×)**. MLX-Varianten nur bei dominierenden langen Prompts wählen.

### 5. MoE rechnet sich auf M5 Pro

`qwen3.6:35b-a3b` (3B aktiv) decodiert bei **~80 tok/s**, doppelt so schnell wie das gleichwertige dense `qwen3.6:35b` (41.68). MoE läuft pro Token nur 3B Gewichte durch den Speicher — perfekt auf den Bandbreiten-Bottleneck abgestimmt.

### 6. macOS Power-Modus ist entscheidend für dense Modelle

| Modell | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Reproduzierbare Benchmarks müssen High Power festlegen**:

```bash
sudo pmset -a powermode 2
```

### 7. Long-Context-16k-Penalty ist klein

Alle 10 Modelle verlieren nur **4–10%** Decodier-Geschwindigkeit von short → 11k Token xlong. M5 Pro / 64 GB hat noch viel Reserve für 16k Context.

## Testumgebung

- **Hardware**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB Unified Memory
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **Strom**: AC, `pmset powermode=2` (High Power)
- **Schlafverhinderung**: `caffeinate -dimsu` durchgehend aktiv
- **Python**: 3.14

## Methodik

Siehe [`bench.py`](./bench.py). Schlüsseldesign:

- Pro Modell: `keep_alive=0` zum Entladen → Cold-Start → Warmup → Messen
- Alle mit `temperature=0` `seed=42` `keep_alive=10m` für Reproduzierbarkeit
- Drei Prompt-Längen:
  - **short** × 5: 26~32 Token → `num_predict=256`
  - **long** × 4: 149~156 Token → `num_predict=512`
  - **xlong** × 3: ~11k Token → `num_predict=256`, erzwungenes `num_ctx=16384`
- Decode tok/s = vom Server gemeldetes `eval_count / eval_duration`. **Nicht von KV-Cache-Hits beeinflusst.**
- Prefill tok/s nimmt nur den **ersten Lauf** von long/xlong (Cold-Prefill) — Ollama wiederverwendet KV-Cache für wiederholte Prompts und bläht die Zahlen absurd auf (100k+ tok/s).

## Reproduzieren

```bash
# 1. High Power festlegen
sudo pmset -a powermode 2

# 2. ollama prüfen
curl -s http://localhost:11434/api/version

# 3. Modelle pullen
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. Schlafverhinderung + Messung
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

# 5. Bericht erzeugen
python3 render_report.py
```

## Repo-Struktur

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # Diese Datei in 12 Sprachen
├── REPORT.md                        # Vollständiger Vergleichsbericht
├── bench.py                         # Mess-Skript
├── render_report.py                 # Nachverarbeitung (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 Qwen3.6-Modelle — Rohdaten + Zusammenfassung
    └── gemma4_*.json / .md          # 4 Gemma4-Modelle — Rohdaten + Zusammenfassung
```

## Bekannte Mess-Einschränkungen

- **Hohes TTFT für Gemma4 short prompt (1.6–5.7 s)**: Im Verhältnis zur Prefill-Zeit (32 / ~1400 ≈ 0.02 s) zu hoch. Wahrscheinlich gemma3-style-Chat-Template-Verarbeitung auf Ollama-Seite.
- **Gemma4 xlong TTFT zeigt 0.00 s — Client-Streaming-Erkennungsbug**: Gemma4s erster Stream-Chunk enthält keine `response`/`thinking`-Strings, daher löst der First-Token-Detektor des Clients nie aus. Tatsächliches TTFT mit `xlong wall - eval_count / xlong_gen` zurückrechnen.
- **Ollama KV-Cache-Wiederverwendung**: Identische Prompts beim 2. Lauf blähen Prefill-Zahlen absurd auf. Der Bericht nimmt nur Cold-Prefill (Run 1).

## Lizenz

CC BY-SA 4.0. Zitieren, ändern, weiterverbreiten frei mit Quellenangabe.

## Mitwirken

Andere M5-Pro-Besitzer, die zusätzliche Modelle (Llama 3.3, DeepSeek, Phi 4, …) ausprobieren möchten, sind willkommen, einen PR oder Issue zu eröffnen. Bei anderer Hardware (M4 / M3 Max / Studio) wäre ein passender Datensatz sehr wertvoll.
