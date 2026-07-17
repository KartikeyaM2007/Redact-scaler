from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "SUBMISSION.docx"


def main() -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def h(text: str, level: int = 1) -> None:
        doc.add_heading(text, level=level)

    def p(text: str) -> None:
        doc.add_paragraph(text)

    def bullet(text: str) -> None:
        doc.add_paragraph(text, style="List Bullet")

    h("PII Redaction Tool — my submission notes")
    p("Kartikeya Mishra")
    p("GitHub: https://github.com/KartikeyaM2007/Redact-scaler")
    p("Try Rules online: https://huggingface.co/spaces/Kartikeym2007/Redact")
    p(
        "I'm submitting this for the Scaler AI Labs PII redaction task. "
        "Below is how I solved it — not a generic tutorial rewrite."
    )

    h("The job, in my words", 2)
    p(
        "I needed a script that reads a Word file full of personal data "
        "(they gave a Red Herring Prospectus; the same code also works on ticket-style docs) "
        "and writes a second .docx where real PII is swapped for fake but believable values. "
        "Masking with **** wasn't the ask — they wanted stand-ins like a fake name/email "
        "so the doc still looks readable."
    )
    p("I cover at least:")
    for item in [
        "names",
        "emails",
        "phones",
        "companies",
        "addresses",
        "SSNs",
        "cards (I check Luhn so random digit noise doesn't get wiped)",
        "DOBs",
        "IPs",
    ]:
        bullet(item)
    p("Core file: redact_pii.py")
    p("My redacted prospectus: Red Herring Prospectus - Redacted.docx")
    p("Optional UI when I'm testing modes: web_app.py")

    h("How detection works (two modes)", 2)
    p("I didn't bet everything on one approach.")

    h("Rules", 3)
    p(
        "Regexes plus labels I care about (Contact Person, DOB, Registered Office, "
        "Ltd/LLC-style company endings, adjacent table cells that look like label → value). "
        "This is what I trust for emails, phones, SSN patterns, cards, IPs, labelled dates. "
        "When something gets replaced, I can usually explain why."
    )

    h("Hybrid (ML / NER)", 3)
    p(
        "Keep those rules, then run spaCy's en_core_web_sm on top. I added this because "
        "plain rules ignore names/companies sitting in normal sentences with no Name: prefix. "
        "My check file has Alice Johnson, Robert Chen, and Microsoft in prose. Rules only "
        "clean the email/phone. Hybrid also hits the three unlabelled ones. That's what "
        "ml_ner_test.py is for — so nobody thinks the UI toggle is fake."
    )
    p(
        "Same fake for the same original value inside one run (hash-based mapping). "
        "I don't ship the mapping file; that would leak the originals."
    )

    table = doc.add_table(rows=3, cols=2)
    table.style = "Table Grid"
    table.cell(0, 0).text = "Mode"
    table.cell(0, 1).text = "On my ML fixture"
    table.cell(1, 0).text = "Rules"
    table.cell(1, 1).text = "email + phone (2)"
    table.cell(2, 0).text = "Hybrid"
    table.cell(2, 1).text = "email + phone + 2 names + Microsoft (5)"

    h("Screens from my local UI", 3)
    p("Rules run (structured fields go; loose prose names stay):")
    doc.add_picture(str(ASSETS / "frontend-rules-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    p("Hybrid run (spaCy picks up the loose names/org too):")
    doc.add_picture(str(ASSETS / "frontend-ml-ner-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    h("Live demo vs local (don't get confused)", 2)
    p(
        "The Hugging Face link is a static Space. Browser only. No Python, so no spaCy there. "
        "I tried free Gradio/Docker on HF — that needs PRO now. I also tried Render; "
        "build/RAM issues on the big prospectus weren't worth fighting for a free host."
    )
    p("So the live page shows Rules, and ML is intentionally off. I'm not labelling it as \"full ML online\" when it isn't.")
    doc.add_picture(str(ASSETS / "hf-space-ml-disabled.png"), width=Inches(4.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("To actually flip Rules ↔ ML: pip install -r requirements.txt then python web_app.py")
    p('Or CLI: python redact_pii.py --mode hybrid in.docx out.docx')

    h("Libraries I used", 2)
    bullet("python-docx — read/write the Word structure")
    bullet("regex / context rules — structured PII")
    bullet("spaCy + en_core_web_sm — extra PERSON/ORG recall in hybrid")
    p("That's it for the engine. No giant LLM API in the loop.")

    h("Numbers I can defend", 2)
    h("Small labelled suite (python redact_pii.py --evaluate)", 3)
    p(
        "I wrote 14 fixed cases: every required type shows up, plus stuff that should not "
        "get nuked (plain offer dates, CIN-looking IDs, order numbers, bland corporate phrasing)."
    )
    t3 = doc.add_table(rows=8, cols=2)
    t3.style = "Table Grid"
    for i, (a, b) in enumerate(
        [
            ("Metric", "Result"),
            ("TP", "10"),
            ("FP", "0"),
            ("FN", "0"),
            ("TN", "4"),
            ("Accuracy", "100%"),
            ("Precision", "100%"),
            ("Recall", "100%"),
        ]
    ):
        t3.cell(i, 0).text = a
        t3.cell(i, 1).text = b
    p(
        'Important: this is my unit check, not "I hand-labelled the whole prospectus." '
        "Don't read it as perfect real-world performance."
    )

    h("Prospectus", 3)
    p(
        "On the assignment file (Rules), last run I logged: 229 paragraphs touched, "
        "347 replacements, 174 unique originals. Mix was mostly company/email/name/address/phone. "
        "That particular doc didn't throw SSN/card/DOB/IP at me; those still pass in the unit suite."
    )

    h("Extra checks", 3)
    p(
        "generic_docx_test.py — three homemade layouts (ticket, HR table, split runs). "
        "Seeded PII gone, control ticket-ish IDs kept."
    )
    p("ml_ner_test.py — proves hybrid ≠ rules on unlabelled prose.")

    h("What still hurts / what I'd do next", 2)
    p(
        "Rules miss bare names. Hybrid helps, but en_core_web_sm is general English — "
        "legal prospectus wording can still dodge it, and if I crank NER too hard I'll "
        "start eating random Title Case junk. Addresses across weird line breaks are still "
        "annoying. Free cloud for spaCy didn't work out for me, so local is the real ML path."
    )
    p(
        "If this were production, I'd sample real pages, have someone label them, then tune — "
        "maybe a domain NER later. Right now it's a solid assignment tool, not a compliance product."
    )

    h("What to open when grading", 2)
    bullet("Code: repo above (redact_pii.py)")
    bullet("Output: Red Herring Prospectus - Redacted.docx")
    bullet("This write-up")
    bullet("EVALUATION_REPORT.md if you want the shorter metrics sheet")
    p("Rerun: python redact_pii.py --evaluate / manual_test.py / generic_docx_test.py / ml_ner_test.py")
    p(
        "I built this for the Scaler brief: fake replacements, the nine PII buckets, "
        "measurable precision/recall on my suite, and an honest split between the static "
        "demo and the local spaCy switch."
    )

    doc.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
