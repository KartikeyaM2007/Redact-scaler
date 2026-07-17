# Evaluation Report

## Scope

This run evaluated the rule-based detector in `redact_pii.py`. The script uses regexes for structured PII and context rules for the more ambiguous categories (names, addresses and DOBs). It creates deterministic fake replacements so a repeated source value is replaced consistently in one document.

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

## Precision/recall judgement and follow-up

Structured PII should have high recall when it matches the implemented formats. The current implementation now supports prose-style labels and adjacent table label/value layouts, but free-form names and informal company names remain the main recall risk because the script deliberately avoids broadly redacting ordinary capitalised text. The address rule may have false positives where a paragraph contains both a postal code and a location/street word. For a final production release, I would have a reviewer label a sample of redacted and unredacted paragraphs across many document families, calculate document-level precision/recall from that gold set, and extend the custom dictionaries or NER layer for missed entities.
