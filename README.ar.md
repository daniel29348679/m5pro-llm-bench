# قياس أداء LLM على M5 Pro — Ollama و MLX وتأثير التكميم

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · **العربية** · [हिन्दी](./README.hi.md)

<div dir="rtl">

يقيس هذا المستودع سرعة **10 نماذج LLM محلية على Apple M5 Pro / 64 GB** عبر [Ollama](https://ollama.com)، مقارنًا:

- **MoE مقابل dense** في سرعة فك التشفير (Qwen3.6 35b-a3b مقابل 35b dense)
- **تنسيقات التكميم** وتأثيرها المختلف على prefill مقابل فك التشفير (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **BF16 الموسوم MLX مقابل BF16 العادي** في أداء prefill
- تأثير **وضع macOS High Power** على الإنتاجية

> **الخلاصة**: على M5 Pro، **حجم النموذج > التكميم > تحسين البنية**. فك التشفير مقيد بعرض النطاق الترددي للذاكرة؛ prefill مقيد بنواة التكميم — قواعد مختلفة تمامًا. البيانات الكاملة في [REPORT.md](./REPORT.md).

</div>

## النماذج المُختبرة (10)

| العائلة | النموذج | المعلمات | تكميم | الحجم |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | 🍎 `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B نشط) | mxfp8 | 37 GB |
| Qwen3.6 | 🍎 `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B نشط) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## النتائج الرئيسية

### سرعة فك التشفير لـ short prompt (متوسط 5 عينات)

| الترتيب | النموذج | tok/s |
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

### سرعة prefill البارد لـ xlong (~11k رمز)

| الترتيب | النموذج | prefill tok/s |
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

<div dir="rtl">

## الاستنتاجات الرئيسية

### 1. فك التشفير و prefill لهما اختناقات مختلفة

- **فك التشفير = مقيد بعرض النطاق الترددي للذاكرة**: الأوزان تعبر الذاكرة مرة واحدة لكل رمز. متغيرات Gemma4 4-bit (e4b, e4b-nvfp4) كلها تفك بسرعة ~68 tok/s؛ BF16 (it-bf16, mlx-bf16) بسرعة ~28 tok/s. **2.4× أبطأ يطابق تمامًا 2× حجم الأوزان.**
- **Prefill = مقيد بـ compute ونواة التكميم**: نفس 4-bit، نفس 9.6 GB، e4b مقابل e4b-nvfp4 يفكان بشكل متطابق — لكن prefill xlong البارد لـ nvfp4 **أسرع 5.7×** (4206 مقابل 736 tok/s).

### 2. nvfp4 هو الفائز الشامل على هذا M5 Pro

- في نفس البنية، nvfp4 يفك التشفير بسرعة أعلى 33–65%، بملفات أصغر 39–43%.
- على Gemma4، nvfp4 لا يساعد فك التشفير لكنه يسرّع prefill ~5×.
- الخلاصة: **اختر nvfp4 دائمًا إذا كان متاحًا**.

### 3. mxfp8 فخ على Apple Silicon

🍎 `qwen3.6:27b-coding-mxfp8` (9.86 tok/s) **أبطأ من Q4_K_M الأصلي (11.82 tok/s)** رغم كونه أكبر بـ 1.8× — mxfp8 ليس له تسريع أصلي على backend Metal.

### 4. علامة MLX لا تساعد فك التشفير لكنها تسرّع prefill ~5×

🍎 `gemma4:e4b-mlx-bf16` و `gemma4:e4b-it-bf16` يفكان بشكل متطابق بسرعة ~28 tok/s، لكن prefill xlong البارد هو **3721 مقابل 782 tok/s (4.8×)**. اختر متغيرات MLX فقط عندما تهيمن المطالبات الطويلة.

### 5. MoE يستحق الاستخدام على M5 Pro

`qwen3.6:35b-a3b` (3B نشط) يفك التشفير بسرعة **~80 tok/s**، أسرع مرتين من نظيره dense `qwen3.6:35b` (41.68). MoE يمر بـ 3B فقط من الأوزان عبر الذاكرة لكل رمز — متماشٍ تمامًا مع اختناق عرض النطاق.

### 6. وضع طاقة macOS حاسم للنماذج dense

</div>

| النموذج | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| 🍎 `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| 🍎 `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

<div dir="rtl">

**المعايير القابلة للتكرار يجب أن تثبّت High Power**:

</div>

```bash
sudo pmset -a powermode 2
```

<div dir="rtl">

### 7. عقوبة السياق الطويل 16k صغيرة

جميع النماذج العشرة تفقد فقط **4–10%** من سرعة فك التشفير عند الانتقال من short → 11k رمز xlong. M5 Pro / 64 GB لديه هامش كبير لسياق 16k.

## بيئة الاختبار

- **العتاد**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB ذاكرة موحدة
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **الطاقة**: AC، `pmset powermode=2` (High Power)
- **منع النوم**: `caffeinate -dimsu` نشط طوال الوقت
- **Python**: 3.14

## المنهجية

انظر [`bench.py`](./bench.py). التصميم الرئيسي:

- لكل نموذج: `keep_alive=0` للتفريغ → cold-start → warmup → قياس
- جميعها بـ `temperature=0` `seed=42` `keep_alive=10m` لقابلية التكرار
- ثلاثة أطوال للمطالبة:
  - **short** × 5: 26~32 رمز → `num_predict=256`
  - **long** × 4: 149~156 رمز → `num_predict=512`
  - **xlong** × 3: ~11k رمز → `num_predict=256`، `num_ctx=16384` إجباري
- فك التشفير tok/s = `eval_count / eval_duration` المُبلَّغ عنه من الخادم. **لا يتأثر بإصابات KV cache.**
- prefill tok/s يأخذ فقط **التشغيل الأول** لـ long/xlong (prefill بارد) — Ollama يعيد استخدام KV cache للمطالبات المتكررة ويضخّم الأرقام بشكل سخيف (100k+ tok/s).

## التكرار

</div>

```bash
# 1. تثبيت High Power
sudo pmset -a powermode 2

# 2. التحقق من ollama
curl -s http://localhost:11434/api/version

# 3. سحب النماذج
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. منع النوم + قياس
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

# 5. توليد التقرير
python3 render_report.py
```

<div dir="rtl">

## بنية المستودع

</div>

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # هذا الملف بـ 12 لغة
├── REPORT.md                        # تقرير المقارنة الكامل
├── bench.py                         # نص القياس
├── render_report.py                 # المعالجة اللاحقة (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 نماذج Qwen3.6 — خام + ملخص
    └── gemma4_*.json / .md          # 4 نماذج Gemma4 — خام + ملخص
```

<div dir="rtl">

## القيود المعروفة في القياس

- **TTFT مرتفع لـ short prompt في Gemma4 (1.6–5.7 ث)**: غير متناسب مع وقت prefill (32 / ~1400 ≈ 0.02 ث). على الأرجح معالجة chat-template gemma3-style على جانب Ollama.
- **TTFT xlong في Gemma4 يظهر 0.00 ث — خطأ في كشف البث على جانب العميل**: أول chunk من gemma4 لا يحتوي على سلاسل `response`/`thinking`، لذلك كاشف first-token للعميل لا يُشغَّل. حساب TTFT الحقيقي بـ `xlong wall - eval_count / xlong_gen`.
- **إعادة استخدام KV cache في Ollama**: المطالبات المتطابقة في التشغيل الثاني تضخّم أرقام prefill بشكل سخيف. التقرير يأخذ فقط prefill البارد (run 1).

## الترخيص

CC BY-SA 4.0. الاقتباس والتعديل وإعادة التوزيع بحرية مع نسب المصدر.

## المساهمة

مالكو M5 Pro الآخرون الذين يجرّبون نماذج إضافية (Llama 3.3، DeepSeek، Phi 4، …) مرحب بهم لفتح PR أو issue. مع عتاد مختلف (M4 / M3 Max / Studio)، مجموعة بيانات مكافئة ستكون قيّمة جدًا.

</div>
