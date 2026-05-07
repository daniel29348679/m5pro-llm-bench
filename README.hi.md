# M5 Pro LLM बेंचमार्क — Ollama, MLX और क्वांटाइजेशन का प्रभाव

**Languages**: [English](./README.md) · [繁體中文](./README.zh-Hant.md) · [简体中文](./README.zh-Hans.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Deutsch](./README.de.md) · [Русский](./README.ru.md) · [Português](./README.pt.md) · [العربية](./README.ar.md) · **हिन्दी**

यह रिपॉजिटरी [Ollama](https://ollama.com) के माध्यम से **Apple M5 Pro / 64 GB पर 10 स्थानीय LLMs** की गति मापती है, तुलना करते हुए:

- **MoE बनाम dense** डिकोड स्पीड (Qwen3.6 35b-a3b बनाम 35b dense)
- **क्वांटाइजेशन प्रारूप** prefill बनाम डिकोड पर अलग प्रभाव (Q4_K_M / mxfp8 / nvfp4 / BF16)
- **MLX-टैग्ड BF16 बनाम साधारण BF16** prefill प्रदर्शन
- **macOS High Power मोड** का throughput पर प्रभाव

> **TL;DR**: M5 Pro पर, **मॉडल आकार > क्वांटाइजेशन > आर्किटेक्चर ऑप्टिमाइजेशन**. डिकोड मेमोरी बैंडविड्थ-बाउंड है; prefill quant-kernel-बाउंड — पूरी तरह से अलग नियम। पूर्ण डेटा [REPORT.md](./REPORT.md) में।

## परीक्षण किए गए मॉडल (10)

| परिवार | मॉडल | पैरामीटर | क्वांट | फ़ाइल आकार |
|---|---|---|---|---:|
| Qwen3.6 | `qwen3.6:35b` | 36.0B dense | Q4_K_M | 23 GB |
| Qwen3.6 | `qwen3.6:27b` | 27.8B dense | Q4_K_M | 17 GB |
| Qwen3.6 | `qwen3.6:27b-coding-mxfp8` | 27.4B dense | mxfp8 | 31 GB |
| Qwen3.6 | `qwen3.6:27b-coding-nvfp4` | 27.4B dense | nvfp4 | 19 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-mxfp8` | 35.1B MoE (3B सक्रिय) | mxfp8 | 37 GB |
| Qwen3.6 | `qwen3.6:35b-a3b-coding-nvfp4` | 35.1B MoE (3B सक्रिय) | nvfp4 | 21 GB |
| Gemma4 | `gemma4:e4b` | 8.0B dense | Q4_K_M | 9.6 GB |
| Gemma4 | `gemma4:e4b-it-bf16` | 8.0B dense | BF16 | 16 GB |
| Gemma4 | 🍎 `gemma4:e4b-mlx-bf16` | 8.0B dense | BF16 (MLX) | 16 GB |
| Gemma4 | `gemma4:e4b-nvfp4` | 8.0B dense | nvfp4 | 9.6 GB |

## मुख्य परिणाम

### Short-prompt डिकोड स्पीड (5 नमूनों का माध्य)

| रैंक | मॉडल | tok/s |
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

### xlong (~11k टोकन) कोल्ड prefill स्पीड

| रैंक | मॉडल | prefill tok/s |
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

## मुख्य निष्कर्ष

### 1. डिकोड और prefill के बाधाक अलग हैं

- **डिकोड = मेमोरी बैंडविड्थ-बाउंड**: weights हर टोकन पर मेमोरी से एक बार गुजरते हैं। Gemma4 के 4-bit वेरिएंट (e4b, e4b-nvfp4) सभी ~68 tok/s पर डिकोड करते हैं; BF16 (it-bf16, mlx-bf16) ~28 tok/s पर। **2.4× धीमा बिल्कुल 2× weight आकार से मेल खाता है।**
- **Prefill = compute और quant-kernel-बाउंड**: समान 4-bit, समान 9.6 GB, e4b बनाम e4b-nvfp4 समान डिकोड करते हैं — लेकिन nvfp4 का कोल्ड xlong prefill **5.7× तेज़** है (4206 बनाम 736 tok/s)।

### 2. nvfp4 इस M5 Pro पर सर्वांगीण विजेता है

- एक ही आर्किटेक्चर के भीतर, nvfp4 33–65% तेज़ डिकोड करता है, फ़ाइलें 39–43% छोटी।
- Gemma4 पर nvfp4 डिकोड में मदद नहीं करता लेकिन prefill ~5× तेज़ करता है।
- निष्कर्ष: **यदि उपलब्ध हो तो हमेशा nvfp4 चुनें**।

### 3. mxfp8 Apple Silicon पर एक जाल है

`qwen3.6:27b-coding-mxfp8` (9.86 tok/s) **मूल Q4_K_M (11.82 tok/s) से धीमा** है, हालाँकि 1.8× बड़ा है — mxfp8 का Metal backend पर कोई नेटिव त्वरण नहीं।

### 4. MLX टैग डिकोड में मदद नहीं करता पर prefill ~5× तेज़ करता है

🍎 `gemma4:e4b-mlx-bf16` और `gemma4:e4b-it-bf16` ~28 tok/s पर समान डिकोड करते हैं, लेकिन कोल्ड xlong prefill **3721 बनाम 782 tok/s (4.8×)** है। MLX वेरिएंट केवल तब चुनें जब लंबे प्रॉम्प्ट प्रबल हों।

### 5. MoE M5 Pro पर लाभदायक है

`qwen3.6:35b-a3b` (3B सक्रिय) **~80 tok/s** पर डिकोड करता है, समकक्ष dense `qwen3.6:35b` (41.68) से दोगुना तेज़। MoE प्रति टोकन केवल 3B weights मेमोरी से गुजारता है — बैंडविड्थ बाधा से पूर्णतः मेल खाता है।

### 6. macOS पावर मोड dense मॉडल के लिए निर्णायक है

| मॉडल | Automatic (run1) | High Power (run2) | Δ |
|---|---:|---:|---:|
| `qwen3.6:35b` | 27.36 | 41.68 | +52% |
| `qwen3.6:27b` | 6.24 | 11.82 | +89% |
| `qwen3.6:27b-coding-mxfp8` | 5.27 | 9.89 | +88% |
| `qwen3.6:27b-coding-nvfp4` | 16.32 | 16.34 | +0% |

**पुनरुत्पाद्य बेंचमार्क के लिए High Power को लॉक करना अनिवार्य**:

```bash
sudo pmset -a powermode 2
```

### 7. 16k लंबे संदर्भ का दंड छोटा है

सभी 10 मॉडल short → 11k टोकन xlong में जाने पर डिकोड स्पीड में केवल **4–10%** खोते हैं। M5 Pro / 64 GB के पास 16k संदर्भ के लिए पर्याप्त गुंजाइश है।

## परीक्षण वातावरण

- **हार्डवेयर**: MacBook Pro (Mac17,9) / Apple M5 Pro / 64 GB एकीकृत मेमोरी
- **OS**: Darwin 25.5.0 (macOS 26)
- **Ollama**: v0.21.0
- **पावर**: AC, `pmset powermode=2` (High Power)
- **नो-स्लीप**: `caffeinate -dimsu` पूरे समय सक्रिय
- **Python**: 3.14

## कार्यप्रणाली

[`bench.py`](./bench.py) देखें। मुख्य डिज़ाइन:

- प्रत्येक मॉडल के लिए: `keep_alive=0` अनलोड → cold-start → warmup → मापें
- सभी `temperature=0` `seed=42` `keep_alive=10m` से पुनरुत्पाद्यता के लिए
- तीन प्रॉम्प्ट लंबाइयाँ:
  - **short** × 5: 26~32 टोकन → `num_predict=256`
  - **long** × 4: 149~156 टोकन → `num_predict=512`
  - **xlong** × 3: ~11k टोकन → `num_predict=256`, बलात `num_ctx=16384`
- डिकोड tok/s = सर्वर-रिपोर्ट किया गया `eval_count / eval_duration`. **KV cache hits से प्रभावित नहीं**.
- Prefill tok/s केवल long/xlong का **पहला रन** लेता है (कोल्ड prefill) — Ollama दोहराए गए प्रॉम्प्ट के लिए KV cache पुनः उपयोग करता है और अगले prefill संख्याओं को बेतुके ढंग से बढ़ाता है (100k+ tok/s)।

## पुनरुत्पादन

```bash
# 1. High Power लॉक करें
sudo pmset -a powermode 2

# 2. ollama की पुष्टि करें
curl -s http://localhost:11434/api/version

# 3. मॉडल पुल करें
for m in qwen3.6:35b qwen3.6:27b qwen3.6:27b-coding-mxfp8 \
         qwen3.6:27b-coding-nvfp4 qwen3.6:35b-a3b-coding-mxfp8 \
         qwen3.6:35b-a3b-coding-nvfp4 \
         gemma4:e4b gemma4:e4b-it-bf16 gemma4:e4b-mlx-bf16 gemma4:e4b-nvfp4; do
  ollama pull "$m"
done

# 4. नो-स्लीप + मापें
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

# 5. रिपोर्ट जनरेट करें
python3 render_report.py
```

## रिपॉजिटरी संरचना

```
m5pro-llm-bench/
├── README.md / README.<lang>.md    # 12 भाषाओं में यह फ़ाइल
├── REPORT.md                        # पूर्ण तुलना रिपोर्ट
├── bench.py                         # मापन स्क्रिप्ट
├── render_report.py                 # पोस्ट-प्रोसेसर (results/*.json → REPORT.md)
└── results/
    ├── qwen3.6_*.json / .md         # 6 Qwen3.6 मॉडल — कच्चा + सारांश
    └── gemma4_*.json / .md          # 4 Gemma4 मॉडल — कच्चा + सारांश
```

## ज्ञात मापन सीमाएँ

- **Gemma4 short-prompt TTFT उच्च (1.6–5.7 स)**: prefill समय (32 / ~1400 ≈ 0.02 स) के साथ अनुपातहीन। संभवतः Ollama-side gemma3-style chat-template प्रोसेसिंग।
- **Gemma4 xlong TTFT 0.00 स दिखाता है — क्लाइंट-साइड स्ट्रीमिंग डिटेक्शन बग**: gemma4 के पहले स्ट्रीम chunk में `response`/`thinking` स्ट्रिंग्स नहीं हैं, इसलिए क्लाइंट का first-token डिटेक्टर कभी ट्रिगर नहीं होता। वास्तविक TTFT `xlong wall - eval_count / xlong_gen` से गणना करें।
- **Ollama KV-cache पुनः उपयोग**: समान प्रॉम्प्ट दूसरे रन पर prefill संख्याओं को बेतुके ढंग से बढ़ाते हैं। रिपोर्ट केवल कोल्ड prefill (run 1) लेती है।

## लाइसेंस

CC BY-SA 4.0. एट्रिब्यूशन के साथ स्वतंत्र रूप से उद्धृत, संशोधित, पुनर्वितरित करें।

## योगदान

अन्य M5 Pro मालिक अतिरिक्त मॉडल (Llama 3.3, DeepSeek, Phi 4, …) चलाने के लिए PR या issue खोलने के लिए स्वागत है। यदि आपके पास अलग हार्डवेयर है (M4 / M3 Max / Studio), समान सेटिंग का डेटासेट बहुत मूल्यवान होगा।
