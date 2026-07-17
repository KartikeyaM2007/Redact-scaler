---
title: PII Redaction Workflow
sdk: docker
app_port: 7860
license: mit
---

# PII Redaction Tool

`redact_pii.py` reads a DOCX, detects common personally identifiable information, and writes a DOCX with consistent fake replacements. It uses standard-library regular expressions plus context rules for names, dates of birth and addresses; `python-docx` preserves the source document's paragraph, table, header and footer structure.

## Local manual-test example

The project includes a one-page DOCX fixture that exercises every PII type required by the assignment. The screenshot below is generated from the actual locally produced **redacted** test DOCX so the example reflects the redactor output exactly.

![Redacted local manual-test output](assets/manual-test-redacted.png)

The test fixture starts with values such as `Rashi Patil`, `rashi.patil@example.com`, `+91 98765 43210`, `Acme Financial Services Limited`, an address, SSN, Luhn-valid card number, DOB and IP address. The output replaces all of them with deterministic fake values while leaving the ordinary offer-date control unchanged.

## Run

```powershell
python redact_pii.py "C:\path\to\Red Herring Prospectus.docx" ".\Red Herring Prospectus - Redacted.docx"
python redact_pii.py --mode hybrid "input.docx" "redacted-with-ner.docx"
python redact_pii.py --evaluate
python manual_test.py
python generic_docx_test.py
python ml_ner_test.py
```

## Web UI

The project now includes a real local browser UI with a DOCX upload panel, terminal log, n8n-style workflow nodes, and a redaction-engine switch. It calls the same `redact_docx` backend used by the command-line script.

```powershell
python web_app.py
```

Then open `http://127.0.0.1:8000/`, choose **Rules** or **ML / NER**, upload a `.docx`, click **Run redaction**, and download the generated redacted DOCX. The workflow and terminal are populated from the actual backend response.

## Hugging Face Space

The public demo is deployed here:

- https://huggingface.co/spaces/Kartikeym2007/Redact
- Direct app URL: https://kartikeym2007-redact.static.hf.space/index.html

The Hugging Face version lives in `hf_static/`. It is a browser-side static Space: it previews the uploaded DOCX, redacts DOCX XML in the browser, shows the redacted result preview, lists exact **Changed Snippets** with before/after evidence, and generates a downloadable redacted DOCX without sending the file to a Python server. For long prospectus files, the top of the preview can still look unchanged if the first page contains only title/legal text; the changed-snippet panel and summary counts show the actual redactions found later in the document. Because this is a free static Space, it cannot run the Python spaCy model; use the local backend UI for the real ML / NER switch.

The script detects email addresses, phones, names in identifying contexts (or with a title), organisation names with legal suffixes, mailing addresses, SSNs, Luhn-valid credit cards, DOB-labelled dates and IPv4 addresses. It also learns common label/value layouts such as `Full Name | Marcus Hill` or `Birth Date | 7 Jan 1992`, which appear frequently in arbitrary Word tables and ticket exports. In `--mode hybrid`, it adds a pretrained spaCy NER layer (`en_core_web_sm`) to catch additional unlabelled PERSON and ORG entities. Each unique source value receives the same fake replacement throughout one run.

## Trade-offs

Regex/context rules are transparent and easy to extend, but they cannot match every free-form name or address. The optional hybrid mode improves recall with spaCy NER for unlabelled people and organisations, while keeping regex rules for structured identifiers. I did not train a custom NER model because that would require labelled PII examples; the included pretrained model is reproducible and practical for the assignment. The script does not write the source-to-fake mapping unless `--mapping` is explicitly specified; that mapping is sensitive and should never be submitted with the redacted output.

## Evaluation

The included deterministic test suite covers every required PII type and several non-PII controls. Run `--evaluate` to reproduce its accuracy, precision and recall. The accompanying report distinguishes these controlled metrics from document-wide performance, which requires a manually labelled gold set.

`manual_test.py` is an end-to-end regression test: it generates a DOCX fixture, runs the actual redactor, checks that every seeded original PII value has been removed, and confirms a non-PII date remains. It writes its evidence to `examples/manual_test_report.json`.

`generic_docx_test.py` adds a broader regression suite so the solution is not tuned to the supplied prospectus. It generates multiple unrelated DOCX files, including a support ticket, a table-based HR form with header/footer PII, and a run-split contact note, then verifies seeded originals are removed and control values remain. It writes evidence to `examples/generic_regression/generic_docx_report.json`.

`ml_ner_test.py` verifies the ML / NER switch. It generates a DOCX with unlabelled prose entities (`Alice Johnson`, `Robert Chen`, `Microsoft`) and proves rules-only mode leaves those ambiguous entities alone while hybrid mode redacts them with spaCy NER. It writes evidence to `examples/ml_ner/ml_ner_report.json`.

For the complete project overview, use case, test procedure, architecture, and future improvements, see [plan.md](plan.md).
