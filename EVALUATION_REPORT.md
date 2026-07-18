# Evaluation Report

Kartikeya Mishra — Scaler PII Redaction assignment  

**How scored:** fully automated (`python redact_pii.py --evaluate` + `python verify_metrics.py`). Not hand-tallied.  
**Evidence:** `verified_metrics.json` (regenerated 18 Jul 2026)

## What “all-round” means here

One tiny perfect table isn’t enough. I report:

1. Automated labelled suite (**30 cases**) — Rules, Rules-vs-full-gold, and Hybrid  
2. DOCX fixtures — `manual_test.py`, `generic_docx_test.py`, `ml_ner_test.py`  
3. Live prospectus redaction counts on the original assignment file  

**Precision policy:** order / ticket / CIN / DIN / page numbers / offer dates are **not** PII. Leaving them is intentional.

---

## 1) Automated labelled suite (30 cases)

Covers every required PII type (usually twice), unlabelled prose names/orgs, and negatives (ticket/order/CIN/etc.).

### A. Rules vs its own expectations  
(rules are not asked to catch bare prose names)

| Metric | Value |
| --- | ---: |
| Cases | 30 |
| TP | 19 |
| FP | 0 |
| FN | 0 |
| TN | 11 |
| Accuracy | 100.0% |
| Precision | 100.0% |
| Recall | 100.0% |

### B. Rules vs **full** PII gold (all-round honesty)  
Same cases, but gold includes unlabelled Alice Johnson / Robert Chen / Microsoft. Rules miss those → recall drops. This is the number that shows why hybrid exists.

| Metric | Value |
| --- | ---: |
| Cases | 30 |
| TP | 19 |
| FP | 0 |
| FN | 3 |
| TN | 8 |
| Accuracy | **90.0%** |
| Precision | **100.0%** |
| Recall | **86.4%** |

### C. Hybrid (rules + spaCy)

| Metric | Value |
| --- | ---: |
| Cases | 30 |
| TP | 22 |
| FP | 4 |
| FN | 0 |
| TN | 6 |
| Accuracy | **87.5%** |
| Precision | **84.6%** |
| Recall | **100.0%** |

Hybrid picks up the bare names/orgs (recall up) but spaCy also over-tags some ORG-ish junk on negatives (precision down). That’s the real tradeoff — not a fake 100% everywhere.

---

## 2) DOCX fixture runs (automated)

| Script | Result |
| --- | --- |
| `manual_test.py` | passed — all 9 PII types; originals gone; control kept |
| `generic_docx_test.py` | passed — ticket / HR table / split runs |
| `ml_ner_test.py` | passed — Rules **2** redactions vs Hybrid **5** |

---

## 3) Prospectus (live Rules run)

Source: original Desktop `Red Herring Prospectus.docx`  
Command: `python verify_metrics.py --prospectus "…\Red Herring Prospectus.docx"`

| | |
| --- | ---: |
| Changed paragraphs | 255 |
| Unique replacements | 187 |
| **Total redactionsions** | **373** |

| Type | Count |
| --- | ---: |
| company | 188 |
| name | 62 |
| email | 50 |
| address | 49 |
| phone | 24 |
| ssn / card / dob / ip | 0 in this file |

Those four types still clear the labelled suite; this prospectus just didn’t contain them.

---

## Limits / extending

- Unit + fixture scores are automated and reproducible.  
- Prospectus counts are engine tallies from a live run, not a human page-by-page gold label.  
- New PII type: add detector + labelled rows in `EVALUATION_CASES` + a fixture assert, then re-run `verify_metrics.py`.
