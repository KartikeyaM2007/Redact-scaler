# Evaluation Report

Kartikeya Mishra — Scaler PII Redaction assignment

## What I measured

I evaluate two layers:

1. **Rules** in `redact_pii.py` — regex + context for structured / labelled PII, with stable fake replacements.  
2. **Hybrid** — same rules plus spaCy `en_core_web_sm` when I turn on `--mode hybrid` (or ML / NER in the local UI).

I’m not pretending the unit scores below equal “perfect on every page of the prospectus.” They’re for a fixed labelled suite I control.

## Controlled suite (`python redact_pii.py --evaluate`)

Fourteen cases I wrote myself: positives for each required PII type, and four negatives (offer date, CIN-style id, order id, generic lead-manager phrasing).

| Metric | Value |
| --- | ---: |
| TP | 10 |
| FP | 0 |
| FN | 0 |
| TN | 4 |
| Accuracy | 100% |
| Precision | 100% |
| Recall | 100% |

## Prospectus

Rules pass over the Red Herring Prospectus produced (latest log): 229 changed paragraphs, 347 replacements, 174 unique source strings. Counts were dominated by company / email / name / address / phone. That file didn’t surface SSN, Luhn card, labelled DOB, or IPv4 for me; those categories still clear the controlled suite.

## Other proofs I keep in the repo

- `generic_docx_test.py` — ticket, HR table+header/footer, run-split contact note. Seeded PII removed; control IDs kept.  
- `ml_ner_test.py` — Rules: 2 hits (email+phone). Hybrid: 5 (adds Alice Johnson, Robert Chen, Microsoft). Control ticket id stays.

## Honest limits

Structured patterns are strong when format matches. Bare names and weird addresses are where recall drops if you stay rules-only; hybrid helps but can still miss domain legalese, and loosening NER too much would trash precision. Next step for real production would be a human-labelled sample from actual docs, then retune — not just ship the stock spaCy model and call it done.
