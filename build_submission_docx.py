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

    h("PII Redaction Tool — how I built this (and what actually works)")
    p("Author: Kartikeya Mishra")
    p("Repo: https://github.com/KartikeyaM2007/Redact-scaler")
    p("Live demo (Rules only): https://huggingface.co/spaces/Kartikeym2007/Redact")
    p(
        "This is my write-up for the Scaler PII Redaction assignment. "
        "I'm keeping it straight: what the tool does, how Rules vs ML/NER differ, "
        "why the live Space can't flip to ML, and what the numbers actually mean."
    )

    h("What the tool does", 2)
    p(
        "You give it a .docx. It finds PII and replaces each value with a fake but "
        "realistic stand-in (same fake every time that value shows up again in the "
        "same run). Output is another .docx you can open in Word."
    )
    p("Minimum categories covered:")
    for item in [
        "full names",
        "emails",
        "phones",
        "company names",
        "addresses",
        "SSNs",
        "credit cards (Luhn check)",
        "dates of birth",
        "IP addresses",
    ]:
        bullet(item)
    p("Main script: redact_pii.py")
    p("Redacted assignment output: Red Herring Prospectus - Redacted.docx")
    p("Local UI: web_app.py + web/")

    h("Rules vs ML / NER (the important bit)", 2)
    p("I didn't force everything through one fancy model. There are two modes on purpose.")

    h("1) Rules mode", 3)
    p(
        'Regex + a bit of context ("Contact Person: …", "DOB: …", table label/value '
        "pairs, company suffixes like Ltd / LLC, etc.)."
    )
    p(
        "This is the reliable baseline for structured stuff: emails, phones, SSNs, "
        "cards, labelled DOBs, IPs. It's deterministic and easy to debug. If something "
        "weird gets redacted, I can usually point at the pattern."
    )

    h("2) Hybrid ML / NER mode", 3)
    p("Same rules plus spaCy en_core_web_sm.")
    p(
        "Why bother? Rules miss people and companies that show up as normal prose with "
        'no label. Example fixture: "Alice Johnson" / "Robert Chen" / "Microsoft" with '
        'no "Name:" in front. Rules leave them. Hybrid catches them.'
    )
    p("That's not marketing fluff — ml_ner_test.py checks it:")

    table = doc.add_table(rows=3, cols=2)
    table.style = "Table Grid"
    table.cell(0, 0).text = "Mode"
    table.cell(0, 1).text = "What got redacted"
    table.cell(1, 0).text = "Rules"
    table.cell(1, 1).text = "email + phone only (2)"
    table.cell(2, 0).text = "Hybrid"
    table.cell(2, 1).text = "email + phone + 2 names + Microsoft (5)"

    h("Local UI screenshots", 3)
    p("Rules — structured contact fields go; unlabelled prose names stay:")
    doc.add_picture(str(ASSETS / "frontend-rules-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    p("ML / NER — same run, but spaCy also hits the unlabelled people/org:")
    doc.add_picture(str(ASSETS / "frontend-ml-ner-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("If you only look at the live Hugging Face link and wonder why ML is greyed out, next section is for you.")

    h("Why the live Hugging Face demo has ML disabled", 2)
    p(
        "Short version: the free Space is static (HTML/JS in the browser). spaCy is "
        "Python. Free Hugging Face Gradio/Docker hosting wants PRO now, and the free "
        "PaaS attempts (Render) choked on Python version / RAM for a fat prospectus + spaCy."
    )
    p("So I stopped pretending and left the live demo honest:")
    doc.add_picture(str(ASSETS / "hf-space-ml-disabled.png"), width=Inches(4.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    bullet("Live Space = browser Rules demo (good enough to try a DOCX online)")
    bullet("Local app / CLI = real Rules and spaCy ML/NER")
    p("I'm not going to call the static Space \"full ML\" when it isn't. Local is where the NER switch actually runs.")
    p("python -m pip install -r requirements.txt")
    p("python web_app.py")
    p("# open http://127.0.0.1:8000/ and pick Rules or ML / NER")
    p('CLI hybrid: python redact_pii.py --mode hybrid "input.docx" "redacted.docx"')

    h("Approach / libraries", 2)
    t2 = doc.add_table(rows=5, cols=3)
    t2.style = "Table Grid"
    rows = [
        ("Piece", "Choice", "Why"),
        ("DOCX I/O", "python-docx", "Keeps paragraphs/tables/headers usable"),
        ("Structured PII", "regex + context labels", "Predictable for emails, phones, SSN, card, IP, labelled DOB"),
        ("Extra names/orgs", "spaCy en_core_web_sm", "Extra recall in unlabelled prose"),
        ("UI", "tiny local HTTP UI", "Switch modes, preview, download"),
    ]
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            t2.cell(i, j).text = val
    p('Replacements are hashed/stable per source value so "Rashi Patil" doesn\'t become three different fakes in one file.')

    h("Evaluation (accuracy / precision / recall)", 2)
    h("Controlled labelled set (python redact_pii.py --evaluate)", 3)
    p(
        "14 cases: every required PII type once (or more for names), plus negatives "
        "like offer dates, CIN-style IDs, order numbers, generic business phrasing."
    )
    t3 = doc.add_table(rows=8, cols=2)
    t3.style = "Table Grid"
    metrics = [
        ("Metric", "Result"),
        ("TP", "10"),
        ("FP", "0"),
        ("FN", "0"),
        ("TN", "4"),
        ("Accuracy", "100%"),
        ("Precision", "100%"),
        ("Recall", "100%"),
    ]
    for i, (a, b) in enumerate(metrics):
        t3.cell(i, 0).text = a
        t3.cell(i, 1).text = b
    p(
        'Be clear with graders: this is the unit suite, not "I labelled every paragraph '
        "of the prospectus by hand.\" It's there to prove each category fires and ticket-ish noise doesn't."
    )

    h("Prospectus run (assignment DOCX)", 3)
    p("Latest local Rules run on the Red Herring Prospectus:")
    bullet("229 paragraphs changed")
    bullet("347 redactionsions")
    bullet("174 unique source values")
    p(
        "Breakdown I saw: addresses 48, companies 169, emails 50, names 62, phones 18. "
        "No SSN / Luhn card / labelled DOB / IPv4 showed up in that particular doc — "
        "those still pass in the controlled suite."
    )

    h("Generic regression (generic_docx_test.py)", 3)
    p(
        "Three made-up DOCX layouts (support ticket, HR table + header/footer, run-split text). "
        "Seeded PII gone, control IDs kept. So it's not a one-document hack."
    )

    h("ML switch proof (ml_ner_test.py)", 3)
    p("Already covered above — hybrid adds the three unlabelled entities Rules skipped.")

    h("Trade-offs (being frank)", 2)
    bullet("Rules win on structured PII and explainability. They lose when someone writes a name with no label.")
    bullet(
        "Hybrid improves that recall, but pretrained NER is general English — prospectus "
        "legalese and odd org styles can still slip, and over-eager NER can invent false "
        "names if you loosen it too much. I kept it conservative."
    )
    bullet("Addresses are messy. Multi-line / weird formatting is still the soft spot.")
    bullet(
        "Live static demo ≠ full stack. If you need to see ML live, run it locally. "
        "I tried free cloud for spaCy; it wasn't worth the broken deploys."
    )
    p(
        "For a production follow-up I'd want a human-labelled sample from real docs, "
        "then tune patterns / maybe a domain NER. Not claiming this is bank-grade redaction."
    )

    h("What's in the repo (submit these)", 2)
    bullet("Source: redact_pii.py (+ web_app.py / web/ if you care about the UI)")
    bullet("Output: Red Herring Prospectus - Redacted.docx")
    bullet("This document + README.md")
    bullet("EVALUATION_REPORT.md for the formal metrics sheet")
    p('Links should be public / "anyone with the link". Repo is public. Live Space link is above.')

    h("Quick rerun checklist", 2)
    p("python redact_pii.py --evaluate")
    p("python manual_test.py")
    p("python generic_docx_test.py")
    p("python ml_ner_test.py")
    p('python redact_pii.py "Red Herring Prospectus.docx" "Red Herring Prospectus - Redacted.docx"')
    p(
        "That's the whole story: Rules for the solid baseline, spaCy when prose names/orgs "
        "matter, and an honest live demo that doesn't fake ML when the host can't run it."
    )

    doc.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
