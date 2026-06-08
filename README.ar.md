# M5 Pro LLM Benchmark — اختيار النماذج على Ollama 0.30.6

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · **العربية** · [हिन्दी](./README.hi.md)

يقيس هذا المستودع أداء LLM محلي على **Apple M5 Pro / 64 GB** باستخدام [Ollama](https://ollama.com). النتائج الحالية تستخدم **Ollama 0.30.6** والنماذج المثبتة على هذه الآلة. تبقى مجموعة الاختبار القديمة ذات 10 نماذج كمرجع تاريخي في [REPORT.md](./REPORT.md).

## الاختيار السريع

| الحالة | اختر | السبب |
|---|---|---|
| أسرع Qwen محلي حاليا | `qwen3.6:35b-a3b-mtp-q4_K_M` مع `draft_num_predict=4` | أفضل سرعة decode مقاسة: حتى **87.97 tokens/s** |
| تريد نموذج Gemma | `gemma4:26b-nvfp4` | أفضل Gemma في تشغيل النماذج المثبتة الحالي |
| تحتاج Qwen MTP أصغر | `qwen3.6:27b-mtp-q4_K_M` مع `draft_num_predict=4` | ملف 17 GB، لكنه أبطأ كثيرا من 35B-a3B MTP |
| تضبط MTP | أبق القيمة الافتراضية `draft_num_predict=4` | إجبار `8` كان أبطأ في كلا نموذجي MTP |
| تريد المقارنة التاريخية الكاملة فقط | اقرأ [REPORT.md](./REPORT.md) | يحتوي مقارنة quantization و MLX الأصلية لعشرة نماذج |

## النتائج الحالية

| النموذج | أفضل استخدام | حجم ملف النموذج (GB) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | مصدر البيانات |
|---|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | أسرع Qwen حاليا | 22 | **86.79** | **87.97** | **79.94** | إعادة اختبار MTP، draft 4 |
| `qwen3.6:35b-a3b-coding-nvfp4` | بديل Qwen بدون MTP | 21 | 64.57 | 64.58 | 59.15 | تشغيل النماذج المثبتة |
| `gemma4:26b-nvfp4` | أسرع Gemma حاليا | 16 | 59.16 | 58.33 | 49.07 | تشغيل النماذج المثبتة |
| `qwen3.6:27b-mtp-q4_K_M` | Qwen MTP أصغر | 17 | 17.41 | 20.62 | 15.77 | إعادة اختبار MTP، draft 4 |
| `gemma4:31b-nvfp4` | ليس اختيارا للسرعة | 20 | 10.41 | 10.27 | 9.14 | تشغيل النماذج المثبتة |

## MTP draft tokens

| النموذج | MTP draft tokens (`draft_num_predict`) | Short decode (tokens/s) | Long decode (tokens/s) | 11k-context decode (tokens/s) | التغير مقابل draft 4 |
|---|---:|---:|---:|---:|---|
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 4 | 86.79 | 87.97 | 79.94 | baseline |
| `qwen3.6:35b-a3b-mtp-q4_K_M` | 8 | 35.75 | 45.55 | 39.81 | -58.8% / -48.2% / -50.2% |
| `qwen3.6:27b-mtp-q4_K_M` | 4 | 17.41 | 20.62 | 15.77 | baseline |
| `qwen3.6:27b-mtp-q4_K_M` | 8 | 9.28 | 12.40 | 8.84 | -46.7% / -39.9% / -43.9% |

**خلاصة MTP:** لا تجبر `draft_num_predict=8` على هذه الآلة. استخدم القيمة الافتراضية للنموذج `4`.

## النماذج المختبرة في التحديث الحالي

| العائلة | النموذج | المعلمات | Quantization | حجم ملف النموذج (GB) | ملاحظات |
|---|---|---|---|---:|---|
| Qwen3.6 | `qwen3.6:35b-a3b-mtp-q4_K_M` | 35.5B MoE | Q4_K_M + MTP | 22 | الفائز الحالي |
| Qwen3.6 | `qwen3.6:27b-mtp-q4_K_M` | 27.3B dense | Q4_K_M + MTP | 17 | baseline أصغر لـ MTP |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE | nvfp4 | 21 | فائز تاريخي، أبطأ في التشغيل الحالي |
| Gemma4 | `gemma4:26b-nvfp4` | 6.3B | nvfp4 | 16 | أفضل نتيجة Gemma حاليا |
| Gemma4 | `gemma4:31b-nvfp4` | 31.3B | nvfp4 | 20 | بطيء في هذا التشغيل |

## شكل الاختبار

| الحالة | طول prompt (tokens) | حد التوليد (`num_predict`, tokens) | العينات |
|---|---:|---:|---:|
| Short | 26-32 | 256 | 5 |
| Long | 149-156 | 512 | 4 |
| 11k context | حوالي 11,000 مع `num_ctx=16384` | 256 | 3 |

سرعة decode هي `eval_count / eval_duration` كما يبلغها خادم Ollama. تم تثبيت High Power عبر `pmset powermode=2`، واستُخدم `caffeinate -dimsu` أثناء التشغيلات.

## ملاحظات تاريخية

اختبرت المجموعة الأصلية الكاملة 10 نماذج على Ollama 0.21/run2. استخدمها كمرجع تاريخي للمقارنة بين architecture و quantization و MLX:

| ملاحظة تاريخية | النتيجة |
|---|---|
| أفضل short decode قديم | `qwen3.6:35b-a3b-coding-nvfp4` عند **80.61 tokens/s** |
| أفضل 11k cold prefill قديم | `gemma4:e4b-nvfp4` عند **4205.55 tokens/s** |
| تحذير Apple Silicon | `mxfp8` كان أبطأ من Q4_K_M رغم أن الملفات أكبر |
| تحذير MLX | في زوج Gemma BF16 النظيف، ساعد MLX في prefill لا في decode |

## النتائج الخام

- [مقارنة النماذج المثبتة على Ollama 0.30.6](./results/ollama_0.30.6_update/installed/00_comparison.md)
- [إعادة اختبار MTP draft-4](./results/ollama_0.30.6_update/mtp_draft4/00_comparison.md)
- [إعادة اختبار MTP draft-8](./results/ollama_0.30.6_update/mtp_draft8/00_comparison.md)
- [تقرير 10 نماذج التاريخي](./REPORT.md)

## القرار النهائي

استخدم `qwen3.6:35b-a3b-mtp-q4_K_M` مع القيمة الافتراضية `draft_num_predict=4` ما لم يكن لديك سبب محدد لغير ذلك. اختر `gemma4:26b-nvfp4` فقط عندما تريد Gemma تحديدا. اختر `qwen3.6:27b-mtp-q4_K_M` فقط إذا كان ملف 17 GB أهم من السرعة. لا تجبر MTP draft tokens على `8`.
