# Project Plan: PII Redaction Tool

## 1. Purpose and use case

This project de-identifies Word documents containing personally identifiable information (PII). It was built for the supplied Red Herring Prospectus assignment, but the script can be used for other `.docx` documents such as ticket logs, customer correspondence, investigation records, or vendor files before those documents are shared for review, testing, or analytics.

The goal is to retain a readable document while replacing detected sensitive values with consistent fake alternatives. For example, a repeated email address is replaced by the same `@example.com` address everywhere in a single run.

## 2. What has been made

| Item | Purpose |
| --- | --- |
| `redact_pii.py` | Main DOCX redaction program and deterministic pseudonym generator. |
| `Red Herring Prospectus - Redacted.docx` | Redacted output generated from the supplied prospectus. |
| `README.md` | Setup, usage, examples, trade-offs, and an actual manual-test screenshot. |
| `EVALUATION_REPORT.md` | Reproducible controlled metrics and document-run summary. |
| `manual_test.py` | End-to-end local regression test covering all required PII types. |
| `generic_docx_test.py` | Multi-document regression test covering arbitrary DOCX layouts, tables, headers/footers, and split runs. |
| `web_app.py` and `web/` | Real local browser UI with upload panel, terminal log, workflow nodes, and download link. |
| `examples/` and `assets/` | Test input, redacted test output, JSON report, and README PNG visual evidence. |
| `PII_Redaction_Submission.zip` | Submission-ready archive of the required deliverables. |

## 3. Detection and replacement design

The program uses `python-docx` to read and write the document while retaining paragraph, table, header, and footer structure. Its detector combines structured regular expressions with context rules:

| Category | Detection approach | Replacement behaviour |
| --- | --- | --- |
| Email | Email regex | `contactNNN@example.com` |
| Phone | Phone regex plus phone-label context for bare local numbers | Fake Indian-format number |
| SSN | `###-##-####` pattern | Fake SSN |
| Credit card | 13-19 digit candidate validated with Luhn | Fake Luhn-valid card |
| IPv4 | IPv4 range regex | Reserved documentation IP `203.0.113.x` |
| DOB | Date pattern near birth/DOB labels, including adjacent label/value tables | Fake date |
| Address | Address labels, postal-code/address-line context, and adjacent label/value tables | Fake mailing address |
| Name | Person-label context, honorifics, adjacent label/value tables, and a learned same-document name list | Deterministic fake first/last name |
| Company | Legal-entity suffixes, adjacent label/value tables, plus a learned same-document entity list | `Example Entity NNN Limited` |

The program makes one initial pass to learn high-confidence names and company names. It then uses that list to redact the same values in later mentions, improving recall without broadly treating every capitalised phrase as a person.

It also learns high-confidence values from common table/form layouts where a label and value are separate DOCX paragraphs, for example `Full Name` in one table cell and `Marcus Hill` in the neighbouring cell.

## 4. How to use it

1. Install the dependency:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Redact a document:

   ```powershell
   python redact_pii.py "input.docx" "redacted.docx"
   ```

3. Run the controlled detector metrics:

   ```powershell
   python redact_pii.py --evaluate
   ```

4. Run the local end-to-end test:

   ```powershell
   python manual_test.py
   ```

5. Run the generic multi-document regression suite:

   ```powershell
   python generic_docx_test.py
   ```

6. Run the local web UI:

   ```powershell
   python web_app.py
   ```

   Open `http://127.0.0.1:8000/`, upload a `.docx`, and download the redacted result.

The optional `--mapping mapping.json` argument writes the original-to-fake mapping. This is sensitive operational data and must not be included in a submission or shared with recipients of the redacted file.

## 5. Testing and verification strategy

### Automated checks

- `python -m py_compile redact_pii.py manual_test.py` checks syntax.
- `python redact_pii.py --evaluate` runs the labelled detector suite across every assignment category plus non-PII controls.
- `python manual_test.py` creates a DOCX fixture, redacts it, asserts that all ten original PII examples are absent, and verifies that an ordinary offer-date control remains.
- `python generic_docx_test.py` creates unrelated DOCX files (support ticket, table-based HR form with header/footer PII, and run-split contact note), redacts them, and asserts that seeded originals are removed while control values remain.

### Manual checks

1. Open `examples/manual_test_input.docx` and `examples/manual_test_redacted.docx` side by side.
2. Confirm each labelled PII value has a plausible fake replacement.
3. Confirm the non-PII offer date is unchanged.
4. Confirm the output remains a readable one-page DOCX fixture.
5. Review the screenshot embedded in `README.md`, which is generated from the local redacted test document contents.
6. Use the web UI upload panel to process both the manual fixture and the supplied Red Herring Prospectus, confirming the terminal and workflow steps match the backend response.

### Prospectus-specific verification

The prospectus run preserved 1,006 top-level paragraphs and 76 tables. Structural checks confirmed the detected original PII values were absent from the resulting document XML, except for generic words such as `Bank` and `Limited` which also appear in the intentionally fake company replacements.

## 6. Known trade-offs and future improvements

- Regexes are auditable and portable but may miss unlabelled names, informal company names, or non-standard address formats.
- Context rules favour precision over recall for names and dates. A production deployment should add a labelled document sample and potentially a configured NER model or approved custom dictionaries.
- The source-to-fake mapping is held in memory by default. If written, it needs secure storage and access controls.
- For large production batches, add logging, document-level audit IDs, encryption at rest, unit tests for each new detector, and a reviewer queue for uncertain candidates.
- Consider preserving runs/hyperlinks more granularly if source documents rely heavily on rich inline formatting.

## 7. Submission checklist

- [x] Source code supplied.
- [x] Redacted DOCX generated.
- [x] README includes approach, trade-offs, examples, and screenshot.
- [x] Evaluation report includes accuracy, precision, and recall.
- [x] Local end-to-end test added and run.
- [x] Generic multi-document regression suite added and run.
- [x] Manual screenshot evidence captured from the locally redacted test output.
- [x] Local frontend added and browser-tested with real DOCX uploads.
