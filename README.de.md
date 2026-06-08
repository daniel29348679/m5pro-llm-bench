# M5 Pro LLM Benchmark — Modellauswahl für Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · **Deutsch** · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Dieses Repo misst den lokalen LLM-Durchsatz auf **Apple M5 Pro / 64 GB** mit [Ollama](https://ollama.com). Die aktuellen Ergebnisse verwenden **Ollama 0.30.6** und die auf dieser Maschine installierten Modelle. Die ältere vollständige 10-Modell-Suite bleibt als historische Referenz in [REPORT.md](./REPORT.md).

## Schnelle Auswahl

| Situation | Auswahl | Grund |
|---|---|---|
| Schnellstes aktuelles lokales Qwen | `qwen3.6:35b-a3b-mtp-q4_K_M` mit `draft_num_predict=4` | Beste gemessene Decode-Geschwindigkeit: bis **87.97 tokens/s** |
| Sie wollen ein Gemma-Modell | `gemma4:26b-nvfp4` | Bestes aktuelles Gemma im Lauf der installierten Modelle |
| Sie brauchen das kleinere Qwen MTP | `qwen3.6:27b-mtp-q4_K_M` mit `draft_num_predict=4` | 17-GB-Datei, aber deutlich langsamer als 35B-a3B MTP |
| Sie optimieren MTP | Standardwert `draft_num_predict=4` beibehalten | Erzwungenes `8` war bei beiden MTP-Modellen langsamer |
| Sie wollen nur den historischen Komplettvergleich | [REPORT.md](./REPORT.md) lesen | Dort steht der ursprüngliche Quantisierungs- und MLX-Vergleich mit 10 Modellen |

## Aktuelle Ergebnisse

| Modell | Bester Einsatz | Modelldateigröße (GB) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-Kontext decode (tokens/s) | Datenquelle |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Schnellstes aktuelles Qwen | 22 | **86.79** | **87.97** | **79.94** | MTP-Retest, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Qwen-Fallback ohne MTP | 21 | 64.57 | 64.58 | 59.15 | Lauf installierter Modelle |
| `gemma4:26b-nvfp4` | Schnellstes aktuelles Gemma | 16 | 59.16 | 58.33 | 49.07 | Lauf installierter Modelle |
| `qwen3.6:27b-mtp-q4_K_M` | Kleineres Qwen-MTP-Baseline | 17 | 17.41 | 20.62 | 15.77 | MTP-Retest, draft 4 |
| `gemma4:31b-nvfp4` | Keine Speed-Empfehlung | 20 | 10.41 | 10.27 | 9.14 | Lauf installierter Modelle |

## MTP-Draft-Tokens

| Modell | MTP-Draft-Tokens (`draft_num_predict`) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-Kontext decode (tokens/s) | Änderung vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**MTP-Fazit:** Erzwingen Sie auf dieser Maschine nicht `draft_num_predict=8`. Verwenden Sie den Modellstandard `4`.

## In der aktuellen Aktualisierung getestete Modelle

| Familie | Modell | Parameter | Quantisierung | Modelldateigröße (GB) | Notizen |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Aktueller Sieger |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Kleineres MTP-Baseline |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Historischer Sieger, jetzt langsamer |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Bestes aktuelles Gemma-Ergebnis |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | In diesem Lauf langsam |

## Benchmark-Form

| Fall | Prompt-Länge (tokens) | Generierungslimit (`num_predict`, tokens) | Samples |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | ca. 11,000 mit `num_ctx=16384` | 256 | 3 |

Decode-Geschwindigkeit ist `eval_count / eval_duration`, wie vom Ollama-Server gemeldet. High Power wurde mit `pmset powermode=2` fixiert, und während der Läufe wurde `caffeinate -dimsu` verwendet.

## Historische Notizen

Die ursprüngliche vollständige Suite testete 10 Modelle auf Ollama 0.21/run2. Sie bleibt nützlich für Vergleiche zu Architektur, Quantisierung und MLX:

| Historische Beobachtung | Ergebnis |
|---|---|
| Bestes altes Short-decode-Ergebnis | `qwen3.6:35b-a3b-coding-nvfp4` mit **80.61 tokens/s** |
| Bestes altes 11k-cold-prefill-Ergebnis | `gemma4:e4b-nvfp4` mit **4205.55 tokens/s** |
| Apple-Silicon-Warnung | `mxfp8` war trotz größerer Dateien langsamer als Q4_K_M |
| MLX-Warnung | Im sauberen Gemma-BF16-Paar half MLX beim prefill, nicht beim decode |

## Rohdaten

- [Ollama 0.30.6 Vergleich installierter Modelle](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [MTP draft-4 Retest](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [MTP draft-8 Retest](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Historischer 10-Modell-Bericht](./REPORT.md)

## Endgültige Entscheidung

Verwenden Sie `qwen3.6:35b-a3b-mtp-q4_K_M` mit dem Standard `draft_num_predict=4`, außer es gibt einen konkreten Grund dagegen. Wählen Sie `gemma4:26b-nvfp4` nur, wenn Sie gezielt Gemma wollen. Wählen Sie `qwen3.6:27b-mtp-q4_K_M` nur, wenn die 17-GB-Datei wichtiger ist als Geschwindigkeit. Erzwingen Sie MTP-Draft-Tokens nicht auf `8`.
