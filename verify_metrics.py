"""Recompute evaluation numbers from live runs. No hard-coded claim numbers.

Usage:
    python verify_metrics.py
    python verify_metrics.py --prospectus "path\\to\\original.docx"
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from docx import Document

from redact_pii import evaluate, iter_paragraphs, redact_docx

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "verified_metrics.json"


def run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def controlled_suite() -> dict:
    result = evaluate()
    return {
        "source": "python redact_pii.py --evaluate (live)",
        "cases": result["cases"],
        "tp": result["tp"],
        "fp": result["fp"],
        "fn": result["fn"],
        "tn": result["tn"],
        "accuracy": round(result["accuracy"] * 100, 1),
        "precision": round(result["precision"] * 100, 1),
        "recall": round(result["recall"] * 100, 1),
        "per_type": result["per_type"],
    }


def fixture_checks() -> dict:
    return {
        "manual_test": run_json([sys.executable, "manual_test.py"]),
        "generic_docx_test": run_json([sys.executable, "generic_docx_test.py"]),
        "ml_ner_test": run_json([sys.executable, "ml_ner_test.py"]),
    }


def analyze_redacted_output(path: Path) -> dict:
    """Count synthetic markers still present in the submitted redacted DOCX."""
    doc = Document(path)
    texts = [p.text for p in iter_paragraphs(doc) if p.text.strip()]
    blob = "\n".join(texts)
    patterns = {
        "example_com_emails": len(re.findall(r"\b[\w.+-]+@example\.com\b", blob, re.I)),
        "example_entity_company": len(re.findall(r"Example Entity \d+ Limited", blob)),
        "example_avenue_address": len(re.findall(r"Example Avenue, Sample City", blob)),
        "synthetic_phone_91": len(re.findall(r"\+91\s+\d{5}\s+\d{5}", blob)),
        "synthetic_ssn_900": len(re.findall(r"\b900-01-\d{4}\b", blob)),
        "synthetic_card_4111": len(re.findall(r"\b4111\s+1111\s+1111\s+\d{4}\b", blob)),
        "synthetic_ip_203": len(re.findall(r"\b203\.0\.113\.\d{1,3}\b", blob)),
    }
    return {
        "file": str(path),
        "non_empty_paragraphs": len(texts),
        "synthetic_marker_counts": patterns,
        "note": (
            "These are markers from our fake-replacement style in the submitted "
            "redacted file. They verify the output was produced by this tool; "
            "they are not the original prospectus redaction summary."
        ),
    }


def prospectus_live_run(source: Path) -> dict:
    out = ROOT / "examples" / "prospectus_live_redacted.docx"
    summary = redact_docx(source, out, mode="rules")
    counts = summary["redactions"]
    return {
        "source": str(source),
        "output": str(out),
        "mode": summary["mode"],
        "changed_paragraphs": summary["changed_paragraphs"],
        "unique_replacements": summary["unique_replacements"],
        "total_redactions": sum(counts.values()),
        "redactions_by_type": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prospectus",
        type=Path,
        help="Optional path to the ORIGINAL Red Herring Prospectus .docx to re-run and count.",
    )
    args = parser.parse_args()

    report: dict = {
        "controlled_suite": controlled_suite(),
        "fixtures": fixture_checks(),
    }

    redacted = ROOT / "Red Herring Prospectus - Redacted.docx"
    if redacted.exists():
        report["submitted_redacted_output"] = analyze_redacted_output(redacted)

    if args.prospectus:
        if not args.prospectus.exists():
            raise SystemExit(f"Prospectus not found: {args.prospectus}")
        report["prospectus_live_run"] = prospectus_live_run(args.prospectus)
    else:
        report["prospectus_live_run"] = {
            "available": False,
            "reason": (
                "Original prospectus .docx was not provided to this script. "
                "Pass --prospectus PATH to recompute live redaction counts."
            ),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
