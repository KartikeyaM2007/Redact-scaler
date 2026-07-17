# Evaluation Report

## Scope

This run evaluated the rule-based detector in `redact_pii.py`. The script uses regexes for structured PII and context rules for the more ambiguous categories (names, addresses and DOBs). It creates deterministic fake replacements so a repeated source value is replaced consistently in one document.

The project now also includes a hybrid ML/NER mode. Hybrid mode keeps the rule-based detectors for structured identifiers and adds spaCy `en_core_web_sm` for extra PERSON/ORG recall in unlabelled prose.

## Controlled evaluation set

The reproducible `--evaluate` test suite contains 14 labelled cases: 10 positive PII-type assertions covering every required category and four negative controls (an offer date, a corporate ID, an order number and a business phrase). The result was:

| Metric | Result |
| --- | ---: |
| True positives | 10 |
| False positives | 0 |
| False negatives | 0 |
| True negatives | 4 |
| Accuracy | 100.0% |
| Precision | 100.0% |
| Recall | 100.0% |

This is a targeted unit-level result, not a claim that the same figures apply to every page of the prospectus. A production evaluation should add a reviewer-labelled, stratified sample of the actual document, including names without labels and multi-line addresses.

## Prospectus run

The supplied **Red Herring Prospectus** was processed successfully. The latest local run changed 229 paragraphs and made 347 redactions across 174 unique source values.

| PII type detected in this document | Occurrences |
| --- | ---: |
| Addresses | 48 |
| Company names | 169 |
| Email addresses | 50 |
| Names | 62 |
| Phone numbers | 18 |
| **Total** | **347** |

No SSNs, Luhn-valid credit-card numbers, DOB-labelled dates or IPv4 addresses were detected in this prospectus. Those categories are nevertheless covered by the controlled evaluation set.

## Generic DOCX regression suite

To verify the tool is not tuned only for the supplied prospectus, `generic_docx_test.py` generates and redacts three unrelated `.docx` files:

| Scenario | Structure covered | Result |
| --- | --- | --- |
| Customer support ticket | Ordinary paragraphs with US-style phone, address, DOB, SSN, card, IP, company and email | Passed |
| HR table with header/footer | Table label/value cells plus header/footer PII | Passed |
| Run-split contact note | PII split across Word runs, plus labelled values | Passed |

The latest run removed all seeded original PII values and retained all non-PII control values. Its JSON evidence is written to `examples/generic_regression/generic_docx_report.json`.

## ML / NER mode comparison

`ml_ner_test.py` verifies that the ML/NER switch changes real behaviour rather than just changing UI labels. It generates a DOCX containing unlabelled prose:

- `Alice Johnson`
- `Robert Chen`
- `Microsoft`
- plus structured email and phone values

The latest run produced:

| Mode | Redactions | Behaviour |
| --- | ---: | --- |
| Rules | 2 | Redacted only structured email + phone; left unlabelled names/org in place. |
| Hybrid ML/NER | 5 | Redacted email + phone plus two PERSON entities and one ORG entity. |

The hybrid output removed all seeded PII values and retained the non-PII control ticket ID. Its JSON evidence is written to `examples/ml_ner/ml_ner_report.json`.

## Precision/recall judgement and follow-up

Structured PII should have high recall when it matches the implemented formats. The current implementation now supports prose-style labels, adjacent table label/value layouts, and optional pretrained NER for unlabelled people/organisations. Free-form names, informal company names and addresses remain the main recall risk because broad redaction of capitalised text would reduce precision. The address rule may have false positives where a paragraph contains both a postal code and a location/street word. For a final production release, I would have a reviewer label a sample of redacted and unredacted paragraphs across many document families, calculate document-level precision/recall from that gold set, and train/tune a domain-specific NER model or extend custom dictionaries for missed entities.
