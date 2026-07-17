# PII Redaction Tool — my submission notes

Kartikeya Mishra  
GitHub: https://github.com/KartikeyaM2007/Redact-scaler  
Try Rules online: https://huggingface.co/spaces/Kartikeym2007/Redact  

I’m submitting this for the Scaler AI Labs PII redaction task. Below is how *I* solved it — not a generic tutorial rewrite.

---

## The job, in my words

I needed a script that reads a Word file full of personal data (they gave a Red Herring Prospectus; the same code also works on ticket-style docs) and writes a second `.docx` where real PII is swapped for fake but believable values. Masking with `****` wasn’t the ask — they wanted stand-ins like a fake name/email so the doc still looks readable.

I cover at least:

- names  
- emails  
- phones  
- companies  
- addresses  
- SSNs  
- cards (I check Luhn so random digit noise doesn’t get wiped)  
- DOBs  
- IPs  

Core file: `redact_pii.py`  
My redacted prospectus: `Red Herring Prospectus - Redacted.docx`  
Optional UI when I’m testing modes: `web_app.py`

---

## How detection works (two modes)

I didn’t bet everything on one approach.

**Rules** — regexes plus labels I care about (`Contact Person`, `DOB`, `Registered Office`, Ltd/LLC-style company endings, adjacent table cells that look like label → value). This is what I trust for emails, phones, SSN patterns, cards, IPs, labelled dates. When something gets replaced, I can usually explain why.

**Hybrid (ML / NER)** — keep those rules, then run spaCy’s `en_core_web_sm` on top. I added this because plain rules ignore names/companies sitting in normal sentences with no “Name:” prefix. My check file has Alice Johnson, Robert Chen, and Microsoft in prose. Rules only clean the email/phone. Hybrid also hits the three unlabelled ones. That’s what `ml_ner_test.py` is for — so nobody thinks the UI toggle is fake.

Same fake for the same original value inside one run (hash-based mapping). I don’t ship the mapping file; that would leak the originals.

### Screens from my local UI

Rules run (structured fields go; loose prose names stay):

![rules](assets/frontend-rules-mode.png)

Hybrid run (spaCy picks up the loose names/org too):

![ml](assets/frontend-ml-ner-mode.png)

---

## Live demo vs local (don’t get confused)

The Hugging Face link is a **static** Space. Browser only. No Python, so no spaCy there. I tried free Gradio/Docker on HF — that needs PRO now. I also tried Render; build/RAM issues on the big prospectus weren’t worth fighting for a free host.

So the live page shows Rules, and ML is intentionally off. I’m not labelling it as “full ML online” when it isn’t.

![hf note](assets/hf-space-ml-disabled.png)

To actually flip Rules ↔ ML:

```text
pip install -r requirements.txt
python web_app.py
```

Or CLI: `python redact_pii.py --mode hybrid in.docx out.docx`

---

## Libraries I used

- `python-docx` — read/write the Word structure  
- regex / context rules — structured PII  
- spaCy + `en_core_web_sm` — extra PERSON/ORG recall in hybrid  

That’s it for the engine. No giant LLM API in the loop.

---

## Numbers I can defend

### Small labelled suite (`python redact_pii.py --evaluate`)

I wrote 14 fixed cases: every required type shows up, plus stuff that should *not* get nuked (plain offer dates, CIN-looking IDs, order numbers, bland corporate phrasing).

| | |
| --- | ---: |
| TP | 10 |
| FP | 0 |
| FN | 0 |
| TN | 4 |
| Accuracy | 100% |
| Precision | 100% |
| Recall | 100% |

Important: this is my unit check, not “I hand-labelled the whole prospectus.” Don’t read it as perfect real-world performance.

### Prospectus

On the assignment file (Rules), last run I logged: 229 paragraphs touched, 347 replacements, 174 unique originals. Mix was mostly company/email/name/address/phone. That particular PDF-turned-doc didn’t throw SSN/card/DOB/IP at me; those still pass in the unit suite.

### Extra checks

`generic_docx_test.py` — three homemade layouts (ticket, HR table, split runs). Seeded PII gone, control ticket-ish IDs kept.  
`ml_ner_test.py` — proves hybrid ≠ rules on unlabelled prose.

---

## What still hurts / what I’d do next

Rules miss bare names. Hybrid helps, but `en_core_web_sm` is general English — legal prospectus wording can still dodge it, and if I crank NER too hard I’ll start eating random Title Case junk. Addresses across weird line breaks are still annoying. Free cloud for spaCy didn’t work out for me, so local is the real ML path.

If this were production, I’d sample real pages, have someone label them, then tune — maybe a domain NER later. Right now it’s a solid assignment tool, not a compliance product.

---

## What to open when grading

1. Code: repo above (`redact_pii.py`)  
2. Output: `Red Herring Prospectus - Redacted.docx`  
3. This write-up  
4. `EVALUATION_REPORT.md` if you want the shorter metrics sheet  

Rerun yourself if you want:

```text
python redact_pii.py --evaluate
python manual_test.py
python generic_docx_test.py
python ml_ner_test.py
```

I built this for the Scaler brief: fake replacements, the nine PII buckets, measurable precision/recall on my suite, and an honest split between the static demo and the local spaCy switch.
