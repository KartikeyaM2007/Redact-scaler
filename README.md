# PII Redaction Tool

Author: Kartikeya Mishra

Live demo (Rules only): [Hugging Face Space](https://huggingface.co/spaces/Kartikeym2007/Redact)

Script that reads a `.docx`, finds PII, and writes another `.docx` with stable fake replacements (not `****` masks). Built for the Scaler assignment; works on the Red Herring Prospectus and on ordinary ticket/HR-style Word files.

## Approach

Two modes in `redact_pii.py`:

1. **Rules** — regex + context labels (emails, phones, SSN, Luhn cards, IPs, labelled DOBs, company suffixes, label/value table cells, etc.).
2. **Hybrid ML/NER** — same rules plus spaCy `en_core_web_sm` for unlabelled PERSON/ORG in prose.

I do **not** treat order IDs, ticket IDs, or CIN-style corporate numbers as PII. Those stay in the text on purpose (precision over “redact every number”).

> **Note:** The live Hugging Face Space is a free static browser demo, so **ML / NER is disabled there**. Full Rules + spaCy runs locally (`python web_app.py` or CLI `--mode hybrid`). Longer write-up: [`SUBMISSION.docx`](SUBMISSION.docx) / [`SUBMISSION.md`](SUBMISSION.md).

## Install / run

```powershell
python -m pip install -r requirements.txt
python redact_pii.py "input.docx" "redacted.docx"
python redact_pii.py --mode hybrid "input.docx" "redacted.docx"
python web_app.py
```

## Verified metrics (re-run 18 Jul 2026)

I re-ran the checks with `python verify_metrics.py`. Raw JSON: [`verified_metrics.json`](verified_metrics.json).

### Controlled labelled suite (`python redact_pii.py --evaluate`)

14 cases I wrote: positives for every required PII type, plus negatives (offer date, CIN-like id, order id, generic business phrase).

| Metric | Value |
| --- | ---: |
| Cases | 14 |
| TP | 10 |
| FP | 0 |
| FN | 0 |
| TN | 4 |
| Accuracy | **100.0%** |
| Precision | **100.0%** |
| Recall | **100.0%** |

These scores are for that suite only — not a claim that every paragraph of the prospectus is perfectly labelled.

### Fixture runs (same verification pass)

| Check | Result |
| --- | --- |
| `manual_test.py` | passed — all 9 PII types exercised; originals gone; non-PII control kept |
| `generic_docx_test.py` | passed — 3 scenarios (ticket / HR table / split runs) |
| `ml_ner_test.py` | passed — Rules: **2** redactions (email+phone); Hybrid: **5** (adds 2 names + Microsoft) |

### Prospectus run (live, Rules mode — 18 Jul 2026)

Re-ran on the original Desktop file via `python verify_metrics.py --prospectus "…\Red Herring Prospectus.docx"`. Output refreshed as `Red Herring Prospectus - Redacted.docx`.

| | |
| --- | ---: |
| Changed paragraphs | 255 |
| Unique source values replaced | 187 |
| **Total redactionsions** | **373** |

| PII type | Count |
| --- | ---: |
| Company | 188 |
| Name | 62 |
| Email | 50 |
| Address | 49 |
| Phone | 24 |
| SSN / card / DOB / IP | 0 in this document |

Those four types still pass in the controlled suite; this prospectus just didn’t contain them.

## What’s in the repo

| Path | Role |
| --- | --- |
| `redact_pii.py` | Redaction engine |
| `Red Herring Prospectus - Redacted.docx` | Assignment output |
| `EVALUATION_REPORT.md` | Evaluation write-up |
| `SUBMISSION.docx` | Longer notes + screenshots |
| `verify_metrics.py` | Recomputes the numbers above |
| `web_app.py`, `web/` | Local UI with Rules / ML switch |

## Trade-offs

Rules are predictable for structured PII and miss bare names in prose. Hybrid helps there (`ml_ner_test.py` shows it) but spaCy can still miss legalese or over-tag if you loosen it. Addresses across odd line breaks remain the soft spot. Live static HF ≠ local spaCy — I’m explicit about that instead of faking an online ML switch.
