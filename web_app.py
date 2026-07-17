"""Web UI for the PII redaction tool.

Local:
    python web_app.py

Render / production:
    gunicorn --bind 0.0.0.0:$PORT --timeout 600 --workers 1 web_app:app
"""

from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

from docx import Document
from flask import Flask, jsonify, request, send_from_directory

from redact_pii import VALID_MODES, iter_paragraphs, redact_docx

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_ROOT = ROOT / "web_outputs"
MAX_UPLOAD_BYTES = 40 * 1024 * 1024
PREVIEW_LINE_LIMIT = 48

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    cleaned = Path(name or "uploaded.docx").name
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", cleaned).strip(" .")
    if not cleaned:
        cleaned = "uploaded.docx"
    if not cleaned.lower().endswith(".docx"):
        cleaned += ".docx"
    return cleaned


def docx_preview(path: Path, limit: int = PREVIEW_LINE_LIMIT) -> dict:
    document = Document(path)
    lines: list[str] = []
    total_non_empty = 0
    for paragraph in iter_paragraphs(document):
        text = paragraph.text.strip()
        if text:
            total_non_empty += 1
            if len(lines) < limit:
                lines.append(text)
    return {
        "lines": lines,
        "totalLines": total_non_empty,
        "truncated": total_non_empty > len(lines),
    }


class StepLogger:
    def __init__(self) -> None:
        self.steps: list[dict] = []
        self.terminal: list[str] = []

    def step(self, step_id: str, label: str, status: str, detail: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.steps.append(
            {
                "id": step_id,
                "label": label,
                "status": status,
                "detail": detail,
                "time": timestamp,
            }
        )
        self.terminal.append(f"[{timestamp}] {label}: {detail}")


def _error_payload(message: str) -> dict:
    return {
        "ok": False,
        "error": message,
        "steps": [
            {
                "id": "error",
                "label": "Request failed",
                "status": "error",
                "detail": message,
                "time": time.strftime("%H:%M:%S"),
            }
        ],
        "terminal": [f"[{time.strftime('%H:%M:%S')}] ERROR: {message}"],
    }


@app.get("/")
def index():
    return send_from_directory(WEB_ROOT, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "PII Redaction Tool"})


@app.get("/web/<path:filename>")
def web_static(filename: str):
    return send_from_directory(WEB_ROOT, filename)


@app.get("/outputs/<job_id>/<path:filename>")
def download_output(job_id: str, filename: str):
    folder = (OUTPUT_ROOT / job_id).resolve()
    if OUTPUT_ROOT.resolve() not in folder.parents and folder != OUTPUT_ROOT.resolve():
        return jsonify(_error_payload("Forbidden")), 403
    return send_from_directory(folder, filename, as_attachment=True)


@app.post("/api/redact")
def redact_upload():
    logger = StepLogger()
    try:
        upload = request.files.get("document")
        if upload is None or not upload.filename:
            raise ValueError("Upload must include a .docx file in the 'document' field.")

        mode = (request.form.get("mode") or "rules").strip()
        if mode not in VALID_MODES:
            raise ValueError(f"Unsupported redaction mode {mode!r}. Choose rules or hybrid.")

        filename = safe_filename(upload.filename)
        if not filename.lower().endswith(".docx"):
            raise ValueError("Only .docx files are supported.")

        data = upload.read()
        if not data:
            raise ValueError("Uploaded file is empty.")
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValueError("Uploaded file is larger than the 40 MB limit.")

        logger.step("upload", "Upload received", "done", f"Received {len(data):,} bytes from browser.")

        job_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        job_dir = OUTPUT_ROOT / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        input_path = job_dir / filename
        output_name = f"{Path(filename).stem} - Redacted.docx"
        output_path = job_dir / output_name

        input_path.write_bytes(data)
        logger.step("save", "File saved locally", "done", str(input_path))

        Document(input_path)
        logger.step("validate", "DOCX validated", "done", "python-docx opened the uploaded file successfully.")
        input_preview = docx_preview(input_path)

        start = time.perf_counter()
        summary = redact_docx(input_path, output_path, mode=mode)
        elapsed = time.perf_counter() - start
        total_redactions = sum(summary["redactions"].values())
        mode_label = "Hybrid rules + spaCy NER" if mode == "hybrid" else "Rules/context"
        logger.step(
            "redact",
            "Redaction engine completed",
            "done",
            f"{mode_label}: {total_redactions} replacements across {summary['changed_paragraphs']} changed paragraphs in {elapsed:.2f}s.",
        )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError("Redaction finished but no output DOCX was created.")
        logger.step("output", "Output DOCX ready", "done", str(output_path))
        logger.step("download", "Download prepared", "done", f"/outputs/{job_id}/{output_name}")
        output_preview = docx_preview(output_path)

        return jsonify(
            {
                "ok": True,
                "jobId": job_id,
                "inputName": filename,
                "outputName": output_name,
                "outputPath": str(output_path),
                "downloadUrl": f"/outputs/{job_id}/{output_name}",
                "summary": summary,
                "uploadedPreview": input_preview,
                "resultPreview": output_preview,
                "steps": logger.steps,
                "terminal": logger.terminal,
            }
        )
    except MemoryError:
        payload = _error_payload(
            "Ran out of memory while redacting. On free hosting, use Rules mode for large DOCX files, "
            "or try ML / NER on a smaller document."
        )
        return jsonify(payload), 507
    except Exception as exc:  # noqa: BLE001 - return JSON errors to the browser
        return jsonify(_error_payload(str(exc))), 400


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"PII Redaction Web UI running at http://{host}:{port}/")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
