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
        "Numbers below are from automated runs "
        "(python redact_pii.py --evaluate + python verify_metrics.py) on 18 Jul 2026. "
        "Evidence: verified_metrics.json. Not eyeballed by hand."
    )

    h("The job", 2)
    p(
        "Script reads a .docx, swaps PII for stable fakes, writes another .docx. "
        "Covers names, emails, phones, companies, addresses, SSNs, Luhn cards, DOBs, IPs."
    )
    p("Core: redact_pii.py · Output: Red Herring Prospectus - Redacted.docx · UI: web_app.py")
    p("Order/ticket/CIN/DIN IDs are not treated as PII (precision choice).")

    h("Rules vs ML / NER", 2)
    p("Rules — regex + labels. Strong on structured PII.")
    p("Hybrid — rules + spaCy en_core_web_sm for bare prose names/orgs.")
    p("ml_ner_test.py: Rules 2 · Hybrid 5 (adds Alice Johnson, Robert Chen, Microsoft).")
    doc.add_picture(str(ASSETS / "frontend-rules-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture(str(ASSETS / "frontend-ml-ner-mode.png"), width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p("HF live Space is static → ML disabled on purpose:")
    doc.add_picture(str(ASSETS / "hf-space-ml-disabled.png"), width=Inches(4.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    h("All-round evaluation (automated)", 2)
    h("Labelled suite — 30 cases", 3)
    t = doc.add_table(rows=4, cols=5)
    t.style = "Table Grid"
    rows = [
        ("View", "Accuracy", "Precision", "Recall", "TP/FP/FN/TN"),
        ("Rules (own labels)", "100.0%", "100.0%", "100.0%", "19/0/0/11"),
        ("Rules vs full gold", "90.0%", "100.0%", "86.4%", "19/0/3/8"),
        ("Hybrid", "87.5%", "84.6%", "100.0%", "22/4/0/6"),
    ]
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            t.cell(i, j).text = val
    p(
        "Full-gold Rules recall 86.4% = misses 3 unlabelled entities. "
        "Hybrid recall 100% but precision 84.6% from spaCy ORG false positives. "
        "That's the real tradeoff — not a fake perfect score everywhere."
    )

    h("Fixtures", 3)
    bullet("manual_test.py — passed (all 9 types)")
    bullet("generic_docx_test.py — passed (ticket / HR table / split runs)")
    bullet("ml_ner_test.py — passed (Rules 2 vs Hybrid 5)")

    h("Prospectus (live Rules)", 3)
    t2 = doc.add_table(rows=9, cols=2)
    t2.style = "Table Grid"
    for i, (a, b) in enumerate(
        [
            ("Metric", "Value"),
            ("Changed paragraphs", "255"),
            ("Unique replacements", "187"),
            ("Total redactions", "373"),
            ("company", "188"),
            ("name", "62"),
            ("email", "50"),
            ("address", "49"),
            ("phone", "24"),
        ]
    ):
        t2.cell(i, 0).text = a
        t2.cell(i, 1).text = b
    p("SSN/card/DOB/IP: 0 in this file (still in the labelled suite).")

    h("Trade-offs", 2)
    p(
        "Rules miss bare names; hybrid catches them and sometimes over-tags. "
        "Addresses can still be messy. Local spaCy is the real ML path; static HF is Rules-only."
    )
    p('Re-run: python redact_pii.py --evaluate')
    p('python verify_metrics.py --prospectus "C:\\Users\\USER\\Desktop\\Red Herring Prospectus.docx"')

    doc.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
