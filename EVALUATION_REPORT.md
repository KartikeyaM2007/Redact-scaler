# Evaluation Report

Kartikeya Mishra — Scaler PII Redaction assignment  

**Verified:** 18 Jul 2026 via `python verify_metrics.py`  
**Evidence file:** `verified_metrics.json`

## Evaluation approach

1. **Controlled suite** — `python redact_pii.py --evaluate`  
   Fixed labelled strings for every required PII type, plus negatives I refuse to redact (offer dates, CIN-like ids, order numbers, bland “Book Running Lead Managers” phrasing). From that I compute TP / FP / FN / TN → accuracy, precision, recall.

2. **End-to-end fixtures** — `manual_test.py`, `generic_docx_test.py`  
   Build real `.docx` files, redact, assert originals are gone and control IDs remain.

3. **Rules vs ML** — `ml_ner_test.py`  
   Same unlabelled prose under both modes; hybrid must remove the extra PERSON/ORG values Rules leave behind.

4. **Assignment output check** — inspect submitted `Red Herring Prospectus - Redacted.docx` for this tool’s synthetic replacement markers (original prospectus kept out of git because it contains real PII).

**Precision policy:** order / ticket / CIN-style identifiers are **not** treated as PII. Leaving them is intentional.

## Controlled suite results (live)

| Metric | Value |
| --- | ---: |
| Cases | 14 |
| True positives (TP) | 10 |
| False positives (FP) | 0 |
| False negatives (FN) | 0 |
| True negatives (TN) | 4 |
| **Accuracy** | **100.0%** |
| **Precision** | **100.0%** |
| **Recall** | **100.0%** |

Per-type TPs in that suite: name×2, email×1, phone×1, company×1, address×1, ssn×1, card×1, dob×1, ip×1.

## Fixture results (live)

| Script | Passed | Notes |
| --- | --- | --- |
| `manual_test.py` | yes | 9 types; 0 originals left; control retained |
| `generic_docx_test.py` | yes | ticket / HR table / split runs all passed |
| `ml_ner_test.py` | yes | Rules redactions = 2; Hybrid = 5 (+3 unlabelled entities) |

## Prospectus output (verified on submitted file)

Scanned `Red Herring Prospectus - Redacted.docx` today:

| Marker | Count |
| --- | ---: |
| Non-empty paragraphs | 694 |
| `@example.com` emails | 38 |
| `Example Entity … Limited` | 77 |
| Example Avenue addresses | 27 |
| Synthetic `+91` phones | 13 |
| Synthetic SSN / card / IP | 0 |

No live “347 total redactions” claim here — that needs a fresh run on the **original** prospectus:

`python verify_metrics.py --prospectus "PATH\Red Herring Prospectus.docx"`

## Limits

Unit scores are high because the suite is designed and labelled. Real recall on bare names still needs hybrid mode; addresses and domain legalese can still slip. Extending to a new PII type = add a detector in `detect_pii` / known-value seeding, plus a row in `EVALUATION_CASES` and a fixture assert.
