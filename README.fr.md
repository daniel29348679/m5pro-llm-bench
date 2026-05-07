# Benchmark LLM sur M5 Pro — Ollama, MLX et l'Impact de la Quantization

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · **Français** · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Ce dépôt mesure la vitesse de **10 LLMs locaux sur Apple M5 Pro / 64 Go** via [Ollama](https://ollama.com), en comparant :

- **MoE vs dense** en vitesse de décodage (Qwen3.6 35b-a3b vs 35b dense)
- **Formats de quantization** et leur impact différent sur prefill vs décodage (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **BF16 étiqueté MLX vs BF16 ordinaire** pour les performances de prefill
- Impact du **mode High Power de macOS** sur le débit

> **TL;DR** : Sur M5 Pro, **taille du modèle > quantization > optimisation d'architecture**. Le décodage est limité par la bande passante mémoire ; le prefill par le kernel de quantization — règles complètement différentes. Données complètes dans [REPORT.md](./REPORT.md).

## Modèles testés (10)

| Famille | Modèle | Paramètres | Quant. | Taille |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 Go |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 Go |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 Go |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 Go |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B actif) | mxfp8 | 37 Go |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B actif) | nvfp4 | 21 Go |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 Go |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 Go |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 Go |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 Go |

## Résultats principaux

### Vitesse de décodage short prompt (moyenne de 5 échantillons)

| Rang | Modèle | tok/s |
|---:|---|---:|
| 1 | `qwen3.6:35b-a3b-coding-nvfp4` | **80.61** |
| 2 | `gemma4:e4b-nvfp4` | **69.34** |
| 3 | `gemma4:e4b` | 68.56 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 60.41 |
| 5 | `qwen3.6:35b` | 41.68 |
| 6 | `gemma4:e4b-it-bf16` | 28.42 |
| 7 | 🍎 `gemma4:e4b-mlx-bf16` | 28.01 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 16.34 |
| 9 | `qwen3.6:27b` | 11.82 |
| 10 | `qwen3.6:27b-coding-mxfp8` | 9.89 |

### Vitesse de prefill cold xlong (~11k tokens)

| Rang | Modèle | prefill tok/s |
|---:|---|---:|
| 1 | `gemma4:e4b-nvfp4` | **4205.55** |
| 2 | 🍎 `gemma4:e4b-mlx-bf16` | **3721.14** |
| 3 | `qwen3.6:35b-a3b-coding-nvfp4` | 2057.40 |
| 4 | `qwen3.6:35b-a3b-coding-mxfp8` | 1908.08 |
| 5 | `gemma4:e4b-it-bf16` | 782.36 |
| 6 | `gemma4:e4b` | 736.34 |
| 7 | `qwen3.6:35b` | 562.50 |
| 8 | `qwen3.6:27b-coding-nvfp4` | 455.78 |
| 9 | `qwen3.6:27b-coding-mxfp8` | 413.21 |
| 10 | `qwen3.6:27b` | 116.00 |

## Conclusions clés

### 1. Décodage et prefill ont des goulots d'étranglement différents

- **Décodage = limité par la bande passante mémoire** : les poids traversent la mémoire une fois par token. Les variantes 4-bit de Gemma4 (e4b, e4b-nvfp4) décodent toutes à ~68 tok/s ; BF16 (it-bf16, mlx-bf16) à ~28 tok/s. **2.4× plus lent correspond exactement à 2× la taille des poids.**
- **Prefill = limité par compute et kernel de quantization** : même 4-bit, même 9.6 Go, e4b vs e4b-nvfp4 décodent identiquement — mais le cold xlong prefill de nvfp4 est **5.7× plus rapide** (4206 vs 736 tok/s).

### 2. nvfp4 est le gagnant universel sur ce M5 Pro

- Dans la même architecture, nvfp4 décode 33–65% plus vite, avec des fichiers 39–43% plus petits.
- Sur Gemma4, nvfp4 n'aide pas le décodage mais accélère le prefill ~5×.
- Conclusion : **toujours choisir nvfp4 si disponible**.

### 3. mxfp8 est un piège sur Apple Silicon

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) est **plus lent que le Q4_K_M original (11.82 tok/s)** malgré sa taille 1.8× supérieure — mxfp8 n'a pas d'accélération native sur le backend Metal.

### 4. L'étiquette MLX n'aide pas le décodage mais accélère le prefill ~5×

🍎 `gemma4:e4b-mlx-bf16` et `gemma4:e4b-it-bf16` décodent identiquement à ~28 tok/s, mais le cold xlong prefill est **3721 vs 782 tok/s (4.8×)**. Choisir les variantes MLX uniquement quand les longs prompts dominent.

### 5. MoE est rentable sur M5 Pro

`qwen3.6:35b-a3b` (3B actif) décode à **~80 tok/s**, deux fois plus vite que le `qwen3.6:35b` dense équivalent (41.68). MoE ne traverse que 3B de poids par token — parfaitement aligné sur le goulot bande passante.

### 6. Le mode énergie macOS est décisif pour les modèles dense

| Modèle | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**Les benchmarks reproductibles doivent verrouiller High Power** :

```bash
sudo pmset -a powermode 2
```

### 7. La pénalité de contexte long 16k est faible

Les 10 modèles ne perdent que **4–10%** de vitesse de décodage en passant de short → 11k tokens xlong. M5 Pro / 64 Go a beaucoup de marge pour le contexte 16k.

## Environnement de test

- **Matériel** : MacBook Pro (Mac17,9) / Apple M5 Pro / 64 Go mémoire unifiée
- **OS** : Darwin 25.5.0 (macOS 26)
- **Ollama** : v0.21.0
- **Alimentation** : AC, `pmset powermode=2` (High Power)
- **Anti-veille** : `caffeinate -dimsu` actif tout le long
- **Python** : 3.14

## Méthodologie

Voir [`bench.py`](./bench.py). Conception clé :

- Pour chaque modèle : `keep_alive=0` pour décharger → cold-start → warmup → mesurer
- Tous avec `temperature=0` `seed=42` `keep_alive=10m` pour reproductibilité
- Trois longueurs de prompt :
  - **short** × 5 : 26~32 tokens → `num_predict=256`
  - **long** × 4 : 149~156 tokens → `num_predict=512`
  - **xlong** × 3 : ~11k tokens → `num_predict=256`, `num_ctx=16384` forcé
- Décodage tok/s = `eval_count / eval_duration` rapporté par le serveur. **Non affecté par les hits de KV cache.**
- Prefill tok/s prend uniquement la **première exécution** de long/xlong (cold prefill) — Ollama réutilise le KV cache pour les prompts répétés et gonfle absurdement les chiffres (100k+ tok/s).

## Reproduire

```bash
# 1. Verrouiller High Power
sudo pmset -a powermode 2

# 2. Vérifier ollama
curl -s http://localhost:11434/api/version

# 3. Pull modèles
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. Anti-veille + mesurer
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

# 5. Générer le rapport
python3 render_report.py
```

## Structure du dépôt

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # Ce fichier en 12 langues
├── REPORT.md                        # Rapport de comparaison complet
├── bench.py                         # Script de mesure
├── render_report.py                 # Post-traitement (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 modèles Qwen3.6 — brut + résumé
    └── gemma4_*.json / .md          # 4 modèles Gemma4 — brut + résumé
```

## Limitations de mesure connues

- **TTFT élevé en short prompt pour Gemma4 (1.6–5.7 s)** : disproportionné avec le temps de prefill (32 / ~1400 ≈ 0.02 s). Probablement traitement du chat-template gemma3-style côté Ollama.
- **TTFT xlong de Gemma4 affiche 0.00 s — bug de détection de streaming côté client** : le premier chunk de gemma4 ne contient pas les chaînes `response`/`thinking`, donc le détecteur first-token côté client ne se déclenche pas. Calculer le TTFT réel avec `xlong wall - eval_count / xlong_gen`.
- **Réutilisation du KV cache d'Ollama** : les prompts identiques au 2ème run gonflent les chiffres de prefill absurdement. Le rapport ne prend que le cold prefill (run 1).

## Licence

CC BY-SA 4.0. Citer, modifier, redistribuer librement avec attribution.

## Contribuer

Autres propriétaires de M5 Pro testant des modèles supplémentaires (Llama 3.3, DeepSeek, Phi 4, …) bienvenus pour ouvrir un PR ou issue. Avec un matériel différent (M4 / M3 Max / Studio), un dataset équivalent serait très précieux.
