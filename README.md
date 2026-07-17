# PII Redaction Tool

Author: Kartikeya Mishra

Live demo: [Hugging Face Space](https://huggingface.co/spaces/Kartikeym2007/Redact)

This project redacts personally identifiable information from `.docx` files and replaces detected values with consistent synthetic alternatives. It was built for the Scaler PII Redaction assignment, but the core script works on arbitrary Word documents such as ticket logs, HR forms, support exports, and prospectus-style documents.

## What is included

| File/folder | Purpose |
| --- | --- |
| `redact_pii.py` | Main DOCX redaction script. |
| `Red Herring Prospectus - Redacted.docx` | Redacted output for the provided assignment document. |
| `EVALUATION_REPORT.md` | Evaluation approach, metrics, and known trade-offs. |
| `requirements.txt` | Python dependencies, including spaCy and the NER model wheel. |
| `manual_test.py` | End-to-end fixture covering all required PII categories. |
| `generic_docx_test.py` | Multi-document regression test for generic DOCX layouts. |
| `ml_ner_test.py` | Proves ML/NER mode adds recall beyond rules-only mode. |
| `web_app.py`, `web/` | Local frontend with a Rules vs ML/NER switch. |
| `assets/` | README screenshots showing Rules and ML/NER frontend runs. |

## Redaction modes

The tool supports two modes:

1. **Rules mode**: deterministic regex and context rules.
2. **Hybrid ML/NER mode**: the same rules plus spaCy `en_core_web_sm` to catch extra unlabelled PERSON and ORG entities.

Rules remain the best fit for structured PII such as emails, phone numbers, SSNs, credit cards, DOB-labelled dates, and IP addresses. The NER layer improves recall for ambiguous names and organisation names in normal prose.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run the redactor

Rules mode:

```powershell
python redact_pii.py "input.docx" "redacted.docx"
```

Hybrid ML/NER mode:

```powershell
python redact_pii.py --mode hybrid "input.docx" "redacted.docx"
```

Optional local-only mapping:

```powershell
python redact_pii.py --mapping mapping.json "input.docx" "redacted.docx"
```

Do not submit or share the mapping file; it contains original-to-fake value relationships.

## Local frontend

```powershell
python web_app.py
```

Open `http://127.0.0.1:8000/`, choose **Rules** or **ML / NER**, upload a `.docx`, run redaction, preview the result, and download the generated redacted DOCX.

The live Hugging Face link is a static browser demo. The full Python backend, including spaCy ML/NER mode, is available through the local frontend and CLI.

## Frontend screenshots

Rules mode redacts the structured email and phone number while leaving unlabelled prose entities unchanged:

![Rules mode frontend result](assets/frontend-rules-mode.png)

ML/NER mode uses the same rules plus spaCy NER, so it also catches unlabelled person and company entities:

![ML NER mode frontend result](assets/frontend-ml-ner-mode.png)

## Tests and evaluation

Run all checks:

```powershell
python redact_pii.py --evaluate
python manual_test.py
python generic_docx_test.py
python ml_ner_test.py
```

Current controlled metrics from `python redact_pii.py --evaluate`:

| Metric | Result |
| --- | ---: |
| Accuracy | 100.0% |
| Precision | 100.0% |
| Recall | 100.0% |

These numbers are for the labelled deterministic test set, not a claim of perfect performance on every possible document.

`ml_ner_test.py` verifies the ML/NER switch with a fixture containing unlabelled prose entities:

- Rules mode redacts only structured email + phone.
- Hybrid ML/NER mode also redacts `Alice Johnson`, `Robert Chen`, and `Microsoft`.

## PII categories covered

- Full names
- Email addresses
- Phone numbers
- Company names
- Physical/mailing addresses
- SSNs
- Credit card numbers, validated with Luhn
- Dates of birth
- IP addresses

## Trade-offs

Regex and context rules are transparent, deterministic, and easy to evaluate. They are strong for structured PII, but can miss free-form names, informal company names, or unusual addresses. Hybrid mode improves recall using pretrained spaCy NER, but a production system should still use a reviewer-labelled corpus to tune precision/recall and possibly train a domain-specific NER model.
