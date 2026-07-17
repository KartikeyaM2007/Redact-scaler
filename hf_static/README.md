---
title: PII Redaction Workflow
sdk: static
app_file: index.html
license: mit
---

# PII Redaction Workflow

Static Hugging Face Space for browser-side DOCX PII redaction. Upload any `.docx`, run the workflow, compare uploaded and redacted previews, inspect the **Changed Snippets** before/after evidence panel, and download the generated redacted DOCX. The browser-side detector supports common prose labels and table-style label/value layouts such as `Full Name | Marcus Hill` or `DOB | 7 Jan 1992`.

Note: the real **ML / NER** switch runs in the local Python backend using spaCy `en_core_web_sm`. This free Hugging Face Static Space cannot execute Python spaCy, so it remains a private browser-side rules demo.
