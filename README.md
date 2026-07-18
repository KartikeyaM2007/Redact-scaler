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

## Verified metrics (automated — 18 Jul 2026)

Not hand-scored. Recompute anytime:

```powershell
python redact_pii.py --evaluate
python verify_metrics.py --prospectus "C:\Users\USER\Desktop\Red Herring Prospectus.docx"
```

Raw dump: [`verified_metrics.json`](verified_metrics.json). Full write-up: [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md).

### Labelled suite (30 automated cases)

| View | Accuracy | Precision | Recall | Notes |
| --- | ---: | ---: | ---: | --- |
| Rules (own labels) | 100.0% | 100.0% | 100.0% | Structured PII + negatives |
| Rules vs **full** gold | **90.0%** | **100.0%** | **86.4%** | Misses bare prose names/orgs (FN=3) |
| Hybrid (rules+spaCy) | **87.5%** | **84.6%** | **100.0%** | Catches bare entities; some ORG false positives (FP=4) |

### Fixtures

| Check | Result |
| --- | --- |
| `manual_test.py` | passed — all 9 types |
| `generic_docx_test.py` | passed — ticket / HR table / split runs |
| `ml_ner_test.py` | passed — Rules **2** vs Hybrid **5** |

### Prospectus (live Rules)

| | |
| --- | ---: |
| Changed paragraphs | 255 |
| Unique replacements | 187 |
| **Total redactions** | **373** |
| company / name / email / address / phone | 188 / 62 / 50 / 49 / 24 |

SSN/card/DOB/IP: 0 in this file (still covered in the labelled suite).

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
