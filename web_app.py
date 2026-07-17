"""Local web UI for the PII redaction tool.

Run from the project folder:
    python web_app.py

Then open http://127.0.0.1:8000/ and upload a .docx file.
"""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import cgi
import json
import mimetypes
import re
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from docx import Document

from redact_pii import redact_docx


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_ROOT = ROOT / "web_outputs"
MAX_UPLOAD_BYTES = 40 * 1024 * 1024


def safe_filename(name: str) -> str:
    cleaned = Path(name or "uploaded.docx").name
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", cleaned).strip(" .")
    if not cleaned:
        cleaned = "uploaded.docx"
    if not cleaned.lower().endswith(".docx"):
        cleaned += ".docx"
    return cleaned


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


class RedactionHandler(SimpleHTTPRequestHandler):
    server_version = "PIIRedactionWeb/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in {"/", "/index.html"}:
            self._send_file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path == "/api/health":
            self._send_json({"ok": True, "service": "PII Redaction Tool"})
            return
        if path.startswith("/web/"):
            target = WEB_ROOT / path.removeprefix("/web/")
            self._send_file(target)
            return
        if path.startswith("/outputs/"):
            target = OUTPUT_ROOT / path.removeprefix("/outputs/")
            self._send_file(target, as_attachment=True)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/redact":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            response = self._handle_redaction_upload()
        except Exception as exc:  # noqa: BLE001 - server should report failures as JSON
            self._send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "steps": [
                        {
                            "id": "error",
                            "label": "Request failed",
                            "status": "error",
                            "detail": str(exc),
                            "time": time.strftime("%H:%M:%S"),
                        }
                    ],
                    "terminal": [f"[{time.strftime('%H:%M:%S')}] ERROR: {exc}"],
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        self._send_json(response)

    def _handle_redaction_upload(self) -> dict:
        logger = StepLogger()
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("No upload body was received.")
        if content_length > MAX_UPLOAD_BYTES:
            raise ValueError("Uploaded file is larger than the 40 MB local limit.")

        logger.step("upload", "Upload received", "done", f"Received {content_length:,} bytes from browser.")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": str(content_length),
            },
        )
        file_item = form["document"] if "document" in form else None
        if file_item is None or not getattr(file_item, "filename", ""):
            raise ValueError("Upload must include a .docx file in the 'document' field.")

        filename = safe_filename(file_item.filename)
        if not filename.lower().endswith(".docx"):
            raise ValueError("Only .docx files are supported.")

        job_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        job_dir = OUTPUT_ROOT / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        input_path = job_dir / filename
        output_name = f"{Path(filename).stem} - Redacted.docx"
        output_path = job_dir / output_name

        data = file_item.file.read()
        input_path.write_bytes(data)
        logger.step("save", "File saved locally", "done", str(input_path))

        Document(input_path)
        logger.step("validate", "DOCX validated", "done", "python-docx opened the uploaded file successfully.")

        start = time.perf_counter()
        summary = redact_docx(input_path, output_path)
        elapsed = time.perf_counter() - start
        total_redactions = sum(summary["redactions"].values())
        logger.step(
            "redact",
            "Redaction engine completed",
            "done",
            f"{total_redactions} replacements across {summary['changed_paragraphs']} changed paragraphs in {elapsed:.2f}s.",
        )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError("Redaction finished but no output DOCX was created.")
        logger.step("output", "Output DOCX ready", "done", str(output_path))
        logger.step("download", "Download prepared", "done", f"/outputs/{job_id}/{output_name}")

        return {
            "ok": True,
            "jobId": job_id,
            "inputName": filename,
            "outputName": output_name,
            "downloadUrl": f"/outputs/{job_id}/{output_name}",
            "summary": summary,
            "steps": logger.steps,
            "terminal": logger.terminal,
        }

    def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path: Path, content_type: str | None = None, as_attachment: bool = False) -> None:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        allowed_roots = (WEB_ROOT.resolve(), OUTPUT_ROOT.resolve())
        if not any(resolved == root or root in resolved.parents for root in allowed_roots):
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return
        if not resolved.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        payload = resolved.read_bytes()
        guessed = content_type or mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", guessed)
        self.send_header("Content-Length", str(len(payload)))
        if as_attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{resolved.name}"')
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        print(f"[web] {self.address_string()} - {format % args}")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), RedactionHandler)
    print("PII Redaction Web UI running at http://127.0.0.1:8000/")
    server.serve_forever()


if __name__ == "__main__":
    main()
