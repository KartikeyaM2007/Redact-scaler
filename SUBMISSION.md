# PII Redaction Tool — my submission notes

Kartikeya Mishra  
GitHub: https://github.com/KartikeyaM2007/Redact-scaler  
Try Rules online: https://huggingface.co/spaces/Kartikeym2007/Redact  

I’m submitting this for the Scaler AI Labs PII redaction task. Numbers below were re-checked with `python verify_metrics.py` on **18 Jul 2026** (`verified_metrics.json`).

---

## The job, in my words

I needed a script that reads a Word file full of personal data (they gave a Red Herring Prospectus; the same code also works on ticket-style docs) and writes a second `.docx` where real PII is swapped for fake but believable values. Masking with `****` wasn’t the ask — they wanted stand-ins like a fake name/email so the doc still looks readable.

I cover at least: names, emails, phones, companies, addresses, SSNs, cards (Luhn), DOBs, IPs.

Core file: `redact_pii.py`  
My redacted prospectus: `Red Herring Prospectus - Redacted.docx`  
Optional UI: `web_app.py`

I do **not** redact order/ticket/CIN-style IDs. That’s a deliberate precision choice.

---

## How detection works (two modes)

**Rules** — regexes + labels I care about (`Contact Person`, `DOB`, `Registered Office`, Ltd/LLC endings, label→value table cells). Good for structured PII; I can usually explain each hit.

**Hybrid (ML / NER)** — rules + spaCy `en_core_web_sm`. Added because rules ignore bare names/companies in prose. Verified: Rules = 2 hits (email+phone); Hybrid = 5 (adds Alice Johnson, Robert Chen, Microsoft). See `ml_ner_test.py`.

### Screens from my local UI

Rules:

![rules](assets/frontend-rules-mode.png)

Hybrid:

![ml](assets/frontend-ml-ner-mode.png)

---

## Live demo vs local

HF Space is static → no Python spaCy → ML toggle stays off on purpose.

![hf note](assets/hf-space-ml-disabled.png)

Local: `pip install -r requirements.txt` then `python web_app.py`, or `python redact_pii.py --mode hybrid in.docx out.docx`.

---

## Verified evaluation numbers

### Accuracy / precision / recall (`redact_pii.py --evaluate`)

| Metric | Value |
| --- | ---: |
| Cases | 14 |
| TP | 10 |
| FP | 0 |
| FN | 0 |
| TN | 4 |
| Accuracy | 100.0% |
| Precision | 100.0% |
| Recall | 100.0% |

Unit suite only — not “I labelled the whole prospectus by hand.”

### Other live checks

- `manual_test.py` — passed (all 9 types)  
- `generic_docx_test.py` — passed (3 layouts)  
- `ml_ner_test.py` — passed (Rules 2 vs Hybrid 5)

### What’s inside the submitted redacted prospectus (counted today)

| Marker | Count |
| --- | ---: |
| Non-empty paragraphs | 694 |
| `@example.com` emails | 38 |
| `Example Entity … Limited` | 77 |
| Example Avenue addresses | 27 |
| Synthetic `+91` phones | 13 |

Original file isn’t in git. To reprint a full engine summary:  
`python verify_metrics.py --prospectus "PATH\original.docx"`

---

## Trade-offs

Rules miss bare names; hybrid helps but isn’t perfect on legalese. Weird multi-line addresses still hurt. Free cloud for spaCy didn’t stick, so local is the real ML path.

---

## Grading pack

1. Code — repo / `redact_pii.py`  
2. Output — `Red Herring Prospectus - Redacted.docx`  
3. This note + `EVALUATION_REPORT.md`  
4. Recompute — `python verify_metrics.py`
