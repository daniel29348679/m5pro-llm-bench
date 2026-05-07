#!/usr/bin/env python3
"""Insert an "MLX control-group caveat" section into every language's README
(before the test-environment heading) and into REPORT.md (before the
observations heading). Idempotent: re-running won't duplicate the section.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Each entry: (language code, README filename, heading anchor (the next
# section's title, before which we insert), translated caveat block).
# `MARKER` at the top of every block is used for idempotency.
MARKER = "<!-- mlx-caveat:v1 -->"


SECTIONS: dict[str, tuple[str, str, str]] = {
    "en": (
        "README.md",
        "## Test environment",
        f"""{MARKER}
## ⚠️ MLX control-group caveat — read before citing findings 3 & 4

Five of the ten benchmarked models are MLX variants (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

This affects how findings 3 and 4 should be read:

- **Finding 3 (mxfp8 is a trap)**: the comparison is 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs non-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Precise statement: **the MLX mxfp8 path on Ollama's Metal backend is slower than the base-GGUF Q4_K_M path**, despite being 1.8× larger.
- **Finding 4 (MLX tag doesn't help decode but boosts prefill)**: only the gemma4 pair has a clean MLX vs non-MLX BF16 comparison (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). The qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` pairs are *both* MLX, so the nvfp4-vs-mxfp8 contrast there is **a quantization comparison within MLX**, not an isolation of the MLX path itself.

In short: 🍎 marks MLX variants, and the only true "MLX vs non-MLX, all else equal" pair in the suite is the gemma4 BF16 pair.

""",
    ),
    "zh-Hant": (
        "README.zh-Hant.md",
        "## 測試環境",
        f"""{MARKER}
## ⚠️ MLX 對照組精確說明 — 引用 finding 3 / 4 前必讀

10 個受測模型中,有 5 個是 MLX 變體（🍎）:

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

對 finding 3 / 4 的精確讀法:

- **Finding 3「mxfp8 是地雷」**:對比是 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs 非 MLX 的 `qwen3.6:27b` Q4_K_M (11.82 tok/s)。精準說法:**Ollama Metal backend 上的 MLX mxfp8 路徑比 base GGUF Q4_K_M 路徑慢**,雖然檔案還大 1.8 倍。
- **Finding 4「MLX 標籤對解碼沒用,但 prefill 大幅領先」**:只有 gemma4 那組是乾淨的「MLX vs 非 MLX 同 BF16」對比(🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`)。Qwen3.6 的 `-coding-mxfp8` / `-coding-nvfp4` *兩個都是* MLX,所以那邊的 nvfp4-vs-mxfp8 對比其實是 **MLX 內部的量化差異**,不是隔離 MLX 路徑本身的效應。

簡言之:🍎 = MLX 變體;本實驗組唯一一組真正「MLX vs 非 MLX、其他不變」的乾淨對比是 gemma4 的 BF16 兩個。

""",
    ),
    "zh-Hans": (
        "README.zh-Hans.md",
        "## 测试环境",
        f"""{MARKER}
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

""",
    ),
    "ja": (
        "README.ja.md",
        "## テスト環境",
        f"""{MARKER}
## ⚠️ MLX コントロールグループの注意事項 — finding 3 / 4 を引用する前に必読

10 個のテスト対象モデルのうち、5 個は MLX 変種(🍎)です:

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

これは finding 3 / 4 の正確な読み方に影響します:

- **Finding 3「mxfp8 は罠」**: 比較対象は 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs 非 MLX の `qwen3.6:27b` Q4_K_M (11.82 tok/s)。正確な表現は: **Ollama Metal backend 上の MLX mxfp8 パスは base GGUF Q4_K_M パスより遅い**(ファイルは 1.8 倍大きいにもかかわらず)。
- **Finding 4「MLX タグはデコードには効かないが、prefill が大幅向上」**: gemma4 のペアだけが「MLX vs 非 MLX、同じ BF16」のクリーンな比較(🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`)。Qwen3.6 の `-coding-mxfp8` / `-coding-nvfp4` は *両方とも* MLX なので、そこでの nvfp4-vs-mxfp8 比較は **MLX 内部の量子化差**であり、MLX パス自体を分離した検証ではありません。

要するに: 🍎 = MLX 変種; この実験で唯一の真の「MLX vs 非 MLX、他は同じ」のクリーンな比較は gemma4 の BF16 ペアです。

""",
    ),
    "ko": (
        "README.ko.md",
        "## 테스트 환경",
        f"""{MARKER}
## ⚠️ MLX 대조군 정확한 설명 — finding 3 / 4 인용 전 필독

10개 측정 모델 중 5개는 MLX 변형(🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

이것이 finding 3 / 4 의 정확한 해석에 영향:

- **Finding 3「mxfp8 은 함정」**: 비교 대상은 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs 비 MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). 정확한 표현: **Ollama Metal backend 의 MLX mxfp8 경로가 base GGUF Q4_K_M 경로보다 느림** (파일은 1.8 배 큼에도 불구하고).
- **Finding 4「MLX 태그는 디코딩에 도움 안 되지만 prefill 은 향상」**: gemma4 쌍만이 깨끗한 「MLX vs 비 MLX, 같은 BF16」 비교 (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Qwen3.6 의 `-coding-mxfp8` / `-coding-nvfp4` 는 *둘 다* MLX 이므로, 거기서의 nvfp4 vs mxfp8 비교는 **MLX 내부의 양자화 차이**일 뿐, MLX 경로 자체를 격리한 테스트가 아님.

요약: 🍎 = MLX 변형; 이 스위트에서 유일한 진정한 「MLX vs 비 MLX, 나머지 동일」 깨끗한 비교는 gemma4 의 BF16 쌍.

""",
    ),
    "es": (
        "README.es.md",
        "## Entorno de prueba",
        f"""{MARKER}
## ⚠️ Aviso sobre el grupo control de MLX — leer antes de citar findings 3 y 4

Cinco de los diez modelos probados son variantes MLX (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Esto afecta cómo deben leerse los findings 3 y 4:

- **Finding 3 (mxfp8 es una trampa)**: la comparación es 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs el no-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Enunciado preciso: **la ruta mxfp8 de MLX sobre el backend Metal de Ollama es más lenta que la ruta GGUF Q4_K_M base**, a pesar de ser 1.8× más grande.
- **Finding 4 (la etiqueta MLX no ayuda al decode pero acelera prefill)**: solo el par gemma4 ofrece una comparación limpia "MLX vs no-MLX, mismo BF16" (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Los pares qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` son *ambos* MLX, así que el contraste nvfp4-vs-mxfp8 allí es **una comparación de cuantización dentro de MLX**, no un aislamiento de la ruta MLX en sí.

En resumen: 🍎 marca variantes MLX, y el único par verdaderamente "MLX vs no-MLX, todo lo demás igual" en la suite es el par BF16 de gemma4.

""",
    ),
    "fr": (
        "README.fr.md",
        "## Environnement de test",
        f"""{MARKER}
## ⚠️ Avis sur le groupe contrôle MLX — à lire avant de citer findings 3 et 4

Cinq des dix modèles testés sont des variantes MLX (🍎) :

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Cela affecte comment lire les findings 3 et 4 :

- **Finding 3 (mxfp8 est un piège)** : la comparaison est 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs le non-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Énoncé précis : **le chemin mxfp8 de MLX sur le backend Metal d'Ollama est plus lent que le chemin GGUF Q4_K_M de base**, bien que 1.8× plus gros.
- **Finding 4 (l'étiquette MLX n'aide pas le décodage mais accélère le prefill)** : seule la paire gemma4 offre une comparaison propre « MLX vs non-MLX, même BF16 » (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Les paires qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` sont *toutes les deux* MLX, donc le contraste nvfp4-vs-mxfp8 là est **une comparaison de quantization à l'intérieur de MLX**, pas un isolement du chemin MLX lui-même.

En bref : 🍎 marque les variantes MLX, et la seule vraie paire « MLX vs non-MLX, tout le reste égal » de la suite est la paire BF16 de gemma4.

""",
    ),
    "de": (
        "README.de.md",
        "## Testumgebung",
        f"""{MARKER}
## ⚠️ MLX-Kontrollgruppen-Hinweis — vor Zitieren von Findings 3 und 4 lesen

Fünf der zehn getesteten Modelle sind MLX-Varianten (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Das betrifft, wie Findings 3 und 4 zu lesen sind:

- **Finding 3 (mxfp8 ist eine Falle)**: Der Vergleich ist 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs Nicht-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Präzise Aussage: **Der MLX-mxfp8-Pfad auf Ollamas Metal-Backend ist langsamer als der Basis-GGUF-Q4_K_M-Pfad**, obwohl 1.8× größer.
- **Finding 4 (MLX-Tag hilft Decode nicht, beschleunigt aber Prefill)**: Nur das gemma4-Paar bietet einen sauberen „MLX vs Nicht-MLX, gleiches BF16"-Vergleich (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Die qwen3.6 `-coding-mxfp8` / `-coding-nvfp4`-Paare sind *beide* MLX, daher ist der nvfp4-vs-mxfp8-Kontrast dort **ein Quantisierungsvergleich innerhalb MLX**, keine Isolation des MLX-Pfads selbst.

Kurz gesagt: 🍎 markiert MLX-Varianten, und das einzige wirklich „MLX vs Nicht-MLX, alles andere gleich"-Paar in der Suite ist das gemma4-BF16-Paar.

""",
    ),
    "ru": (
        "README.ru.md",
        "## Окружение тестирования",
        f"""{MARKER}
## ⚠️ Уточнение про контрольную группу MLX — прочитать перед цитированием findings 3 и 4

Пять из десяти протестированных моделей — это варианты MLX (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Это влияет на правильное прочтение findings 3 и 4:

- **Finding 3 (mxfp8 — ловушка)**: сравнение это 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs не-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Точная формулировка: **путь MLX-mxfp8 на бэкенде Metal Ollama медленнее, чем базовый путь GGUF Q4_K_M**, несмотря на то, что в 1.8× больше.
- **Finding 4 (тег MLX не помогает decode, но ускоряет prefill)**: только пара gemma4 даёт чистое сравнение «MLX vs не-MLX, тот же BF16» (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Пары qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` *обе* являются MLX, так что контраст nvfp4-vs-mxfp8 там — это **сравнение квантизации внутри MLX**, а не изоляция самого MLX-пути.

Кратко: 🍎 — варианты MLX; единственная по-настоящему чистая пара «MLX vs не-MLX, всё остальное одинаково» в наборе — это пара BF16 у gemma4.

""",
    ),
    "pt": (
        "README.pt.md",
        "## Ambiente de teste",
        f"""{MARKER}
## ⚠️ Aviso sobre o grupo controle de MLX — ler antes de citar findings 3 e 4

Cinco dos dez modelos testados são variantes MLX (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

Isso afeta como findings 3 e 4 devem ser lidos:

- **Finding 3 (mxfp8 é uma armadilha)**: a comparação é 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) vs o não-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). Enunciado preciso: **o caminho mxfp8 de MLX no backend Metal do Ollama é mais lento que o caminho GGUF Q4_K_M base**, apesar de ser 1.8× maior.
- **Finding 4 (a tag MLX não ajuda a decodificação mas acelera prefill)**: apenas o par gemma4 oferece uma comparação limpa "MLX vs não-MLX, mesmo BF16" (🍎 `gemma4:e4b-mlx-bf16` vs `gemma4:e4b-it-bf16`). Os pares qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` são *ambos* MLX, então o contraste nvfp4-vs-mxfp8 ali é **uma comparação de quantização dentro de MLX**, não um isolamento do caminho MLX em si.

Resumindo: 🍎 marca variantes MLX, e o único par verdadeiramente "MLX vs não-MLX, tudo o mais igual" da suite é o par BF16 de gemma4.

""",
    ),
    "ar": (
        "README.ar.md",
        "## بيئة الاختبار",
        f"""{MARKER}
<div dir="rtl">

## ⚠️ تنبيه حول مجموعة التحكم MLX — اقرأه قبل الاستشهاد بـ finding 3 و 4

خمسة من النماذج العشرة المُختبرة هي متغيرات MLX (🍎):

</div>

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

<div dir="rtl">

هذا يؤثر على كيفية قراءة finding 3 و 4 بدقة:

- **Finding 3 (mxfp8 فخ)**: المقارنة هي 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) مقابل غير-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s). البيان الدقيق: **مسار MLX mxfp8 على backend Metal لـ Ollama أبطأ من مسار GGUF Q4_K_M الأساسي**، رغم كونه أكبر بـ 1.8×.
- **Finding 4 (علامة MLX لا تساعد فك التشفير لكنها تسرّع prefill)**: زوج gemma4 فقط يوفر مقارنة نظيفة «MLX مقابل غير-MLX، نفس BF16» (🍎 `gemma4:e4b-mlx-bf16` مقابل `gemma4:e4b-it-bf16`). أزواج qwen3.6 `-coding-mxfp8` / `-coding-nvfp4` *كلاهما* MLX، لذا فإن تناقض nvfp4-vs-mxfp8 هناك هو **مقارنة تكميم داخل MLX**، وليس عزلًا لمسار MLX نفسه.

باختصار: 🍎 يميز متغيرات MLX، والزوج الوحيد حقًا «MLX مقابل غير-MLX، كل شيء آخر متساوٍ» في المجموعة هو زوج BF16 من gemma4.

</div>

""",
    ),
    "hi": (
        "README.hi.md",
        "## परीक्षण वातावरण",
        f"""{MARKER}
## ⚠️ MLX नियंत्रण समूह सटीक स्पष्टीकरण — finding 3 / 4 उद्धृत करने से पहले अवश्य पढ़ें

10 परीक्षित मॉडलों में से 5 MLX वेरिएंट हैं (🍎):

- 🍎 `qwen3.6:27b-coding-mxfp8`
- 🍎 `qwen3.6:27b-coding-nvfp4`
- 🍎 `qwen3.6:35b-a3b-coding-mxfp8`
- 🍎 `qwen3.6:35b-a3b-coding-nvfp4`
- 🍎 `gemma4:e4b-mlx-bf16`

यह finding 3 / 4 की सटीक व्याख्या को प्रभावित करता है:

- **Finding 3 (mxfp8 एक जाल है)**: तुलना है 🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) बनाम गैर-MLX `qwen3.6:27b` Q4_K_M (11.82 tok/s)। सटीक कथन: **Ollama के Metal backend पर MLX mxfp8 पथ बेस GGUF Q4_K_M पथ से धीमा है**, हालाँकि फ़ाइल 1.8× बड़ी है।
- **Finding 4 (MLX टैग डिकोड में मदद नहीं करता पर prefill तेज़ करता है)**: केवल gemma4 जोड़ी ही स्वच्छ «MLX बनाम गैर-MLX, समान BF16» तुलना देती है (🍎 `gemma4:e4b-mlx-bf16` बनाम `gemma4:e4b-it-bf16`)। qwen3.6 की `-coding-mxfp8` / `-coding-nvfp4` जोड़ियाँ *दोनों* MLX हैं, इसलिए वहाँ nvfp4-vs-mxfp8 तुलना **MLX के भीतर की क्वांटाइजेशन तुलना** है, MLX पथ का अलगाव नहीं।

संक्षेप में: 🍎 = MLX वेरिएंट; इस सूट में एकमात्र वास्तविक «MLX बनाम गैर-MLX, बाकी सब समान» स्वच्छ तुलना gemma4 BF16 जोड़ी है।

""",
    ),
    "report": (
        "REPORT.md",
        "## 觀察與分析",
        f"""{MARKER}
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

""",
    ),
}


def patch_one(path: Path, anchor: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        # idempotent: strip out the previous block (between MARKER and the
        # anchor, exclusive) and reinsert.
        pattern = re.compile(
            r"<!-- mlx-caveat:v1 -->\n(.*?)(?=^" + re.escape(anchor) + r")",
            re.DOTALL | re.MULTILINE,
        )
        text = pattern.sub("", text, count=1)
    # Now insert before the anchor heading line.
    if anchor not in text:
        print(f"  ! anchor not found in {path.name}: {anchor!r}")
        return False
    text = text.replace(anchor, block + anchor, 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for key, (filename, anchor, block) in SECTIONS.items():
        p = ROOT / filename
        if not p.exists():
            print(f"  missing: {filename}")
            continue
        if patch_one(p, anchor, block):
            print(f"  patched {filename}")
            changed += 1
    print(f"\n{changed} file(s) patched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
