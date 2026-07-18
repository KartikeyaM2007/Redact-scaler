# PII Redaction Tool — my submission notes

Kartikeya Mishra  
GitHub: https://github.com/KartikeyaM2007/Redact-scaler  
Try Rules online: https://huggingface.co/spaces/Kartikeym2007/Redact  

Numbers below are from **automated** runs (`python redact_pii.py --evaluate` + `python verify_metrics.py`) on **18 Jul 2026**. Evidence: `verified_metrics.json`. Not eyeballed by hand.

---

## The job

Script reads a `.docx`, swaps PII for stable fakes, writes another `.docx`. Covers names, emails, phones, companies, addresses, SSNs, Luhn cards, DOBs, IPs.  
Core: `redact_pii.py` · Output: `Red Herring Prospectus - Redacted.docx` · UI: `web_app.py`  

Order/ticket/CIN/DIN IDs are **not** treated as PII (precision choice).

---

## Rules vs ML / NER

**Rules** — regex + labels. Strong on structured PII.  
**Hybrid** — rules + spaCy `en_core_web_sm` for bare prose names/orgs.

`ml_ner_test.py`: Rules **2** · Hybrid **5** (adds Alice Johnson, Robert Chen, Microsoft).

![rules](assets/frontend-rules-mode.png)

![ml](assets/frontend-ml-ner-mode.png)

HF live Space is static → ML disabled on purpose:

![hf](assets/hf-space-ml-disabled.png)

---

## All-round evaluation (automated)

### Labelled suite — 30 cases

| View | Acc | Prec | Rec | TP/FP/FN/TN |
| --- | ---: | ---: | ---: | --- |
| Rules (own labels) | 100.0% | 100.0% | 100.0% | 19/0/0/11 |
| Rules vs full gold | **90.0%** | **100.0%** | **86.4%** | 19/0/3/8 |
| Hybrid | **87.5%** | **84.6%** | **100.0%** | 22/4/0/6 |

Full-gold Rules recall 86.4% = misses 3 unlabelled entities. Hybrid recall 100% but precision 84.6% from spaCy ORG false positives. That’s the real tradeoff.

### Fixtures
manual + generic + ml_ner — all passed.

### Prospectus (live Rules)
**373** redactions · 255 paragraphs · 187 unique · company 188 / name 62 / email 50 / address 49 / phone 24.

---

## Trade-offs

Rules miss bare names; hybrid catches them and sometimes over-tags. Addresses can still be messy. Local spaCy is the real ML path; static HF is Rules-only.

## Re-run
```text
python redact_pii.py --evaluate
python verify_metrics.py --prospectus "C:\Users\USER\Desktop\Red Herring Prospectus.docx"
```
