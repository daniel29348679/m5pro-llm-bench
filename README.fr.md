# M5 Pro LLM Benchmark — Choix de modèles Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · **Français** · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · [हिन्दी](./README.hi.md)

Ce dépôt mesure le débit de LLM locaux sur **Apple M5 Pro / 64 GB** avec [Ollama](https://ollama.com). Les résultats actuels utilisent **Ollama 0.30.6** et les modèles installés sur cette machine. L'ancienne suite de 10 modèles reste disponible comme référence historique dans [REPORT.md](./REPORT.md).

## Choix rapide

| Situation | Choisir | Raison |
|---|---|---|
| Qwen local le plus rapide actuellement | `qwen3.6:35b-a3b-mtp-q4_K_M` avec `draft_num_predict=4` | Meilleure vitesse mesurée : jusqu'à **87.97 tokens/s** |
| Vous voulez un modèle Gemma | `gemma4:26b-nvfp4` | Meilleur Gemma dans le run actuel des modèles installés |
| Vous avez besoin du Qwen MTP plus petit | `qwen3.6:27b-mtp-q4_K_M` avec `draft_num_predict=4` | Fichier de 17 GB, mais beaucoup plus lent que le 35B-a3B MTP |
| Vous ajustez MTP | Garder la valeur par défaut `draft_num_predict=4` | Forcer `8` a ralenti les deux modèles MTP |
| Vous voulez seulement la comparaison historique complète | Lire [REPORT.md](./REPORT.md) | Comparaison originale de quantification et MLX sur 10 modèles |

## Résultats actuels

| Modèle | Meilleur usage | Taille du fichier modèle (GB) | Décodage short (tokens/s) | Décodage long (tokens/s) | Décodage contexte 11k (tokens/s) | Source |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | Qwen actuel le plus rapide | 22 | **86.79** | **87.97** | **79.94** | Retest MTP, draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | Repli Qwen sans MTP | 21 | 64.57 | 64.58 | 59.15 | Run modèles installés |
| `gemma4:26b-nvfp4` | Gemma actuel le plus rapide | 16 | 59.16 | 58.33 | 49.07 | Run modèles installés |
| `qwen3.6:27b-mtp-q4_K_M` | Qwen MTP plus petit | 17 | 17.41 | 20.62 | 15.77 | Retest MTP, draft 4 |
| `gemma4:31b-nvfp4` | Pas un choix de vitesse | 20 | 10.41 | 10.27 | 9.14 | Run modèles installés |

## Tokens de brouillon MTP

| Modèle | Tokens MTP de brouillon (`draft_num_predict`) | Décodage short (tokens/s) | Décodage long (tokens/s) | Décodage contexte 11k (tokens/s) | Écart vs draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**Conclusion MTP :** ne forcez pas `draft_num_predict=8` sur cette machine. Utilisez la valeur par défaut `4`.

## Modèles testés dans la mise à jour actuelle

| Famille | Modèle | Paramètres | Quantification | Taille du fichier modèle (GB) | Notes |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | Gagnant actuel |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | Baseline MTP plus petit |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | Gagnant historique, plus lent dans le run actuel |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | Meilleur résultat Gemma actuel |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | Lent dans ce run |

## Forme du benchmark

| Cas | Longueur du prompt (tokens) | Limite de génération (`num_predict`, tokens) | Échantillons |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| Contexte 11k | environ 11,000 avec `num_ctx=16384` | 256 | 3 |

La vitesse de décodage est `eval_count / eval_duration`, telle que rapportée par le serveur Ollama. Le mode High Power était fixé avec `pmset powermode=2`, et `caffeinate -dimsu` a été utilisé pendant les runs.

## Notes historiques

La suite complète originale a testé 10 modèles avec Ollama 0.21/run2. Elle reste utile pour les comparaisons d'architecture, de quantification et de MLX :

| Constat historique | Résultat |
|---|---|
| Meilleur ancien résultat en short decode | `qwen3.6:35b-a3b-coding-nvfp4` à **80.61 tokens/s** |
| Meilleur ancien résultat en 11k cold prefill | `gemma4:e4b-nvfp4` à **4205.55 tokens/s** |
| Avertissement Apple Silicon | `mxfp8` était plus lent que Q4_K_M malgré des fichiers plus gros |
| Avertissement MLX | Dans la paire Gemma BF16 propre, MLX aidait le prefill, pas le decode |

## Résultats bruts

- [Comparaison des modèles installés sur Ollama 0.30.6](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [Retest MTP draft-4](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [Retest MTP draft-8](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [Rapport historique 10 modèles](./REPORT.md)

## Décision finale

Utilisez `qwen3.6:35b-a3b-mtp-q4_K_M` avec la valeur par défaut `draft_num_predict=4`, sauf contrainte spécifique. Choisissez `gemma4:26b-nvfp4` uniquement si vous voulez Gemma. Choisissez `qwen3.6:27b-mtp-q4_K_M` uniquement si le fichier de 17 GB compte plus que la vitesse. Ne forcez pas les tokens de brouillon MTP à `8`.
