"""Dry run against the fictional Harbour and Wren fixture site."""

import json
import threading
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from checker import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "harbour"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def test_local_fixture_site_produces_a_client_report(tmp_path, monkeypatch):
    monkeypatch.delenv("PSI_API_KEY", raising=False)
    handler = partial(QuietHandler, directory=str(FIXTURE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        code = main(
            [
                f"http://127.0.0.1:{port}/",
                "--max-pages",
                "15",
                "--delay",
                "0",
                "--skip-external",
                "--output",
                str(tmp_path),
                "--firm-name",
                "Harbour and Wren Asbestos Surveys",
            ]
        )
    finally:
        server.shutdown()
        server.server_close()
    assert code == 0
    markdown_paths = list(tmp_path.glob("*.md"))
    json_paths = list(tmp_path.glob("*.json"))
    assert len(markdown_paths) == 1
    assert len(json_paths) == 1
    report = markdown_paths[0].read_text(encoding="utf-8")
    payload = json.loads(json_paths[0].read_text(encoding="utf-8"))
    assert payload["pages_checked"] == 6
    assert payload["score"] == 82
    assert "ROBOTS-SECRET" not in json.dumps(payload)
    assert "lorem ipsum" not in json.dumps(payload).lower()
    titles = {page["title"] for page in payload["pages"]}
    assert "Old survey notes" in titles
    assert "" in titles
    assert any("Missing title" in page["warnings"] for page in payload["pages"])
    assert any(item["reason"] == "non-html extension" for item in payload["skipped"])
    assert any(item["reason"] == "robots.txt" for item in payload["skipped"])
    ids = {finding["id"] for finding in payload["findings"]}
    assert "https" in ids
    assert "professional_indemnity" in ids
    assert "accreditation_on_service_pages" in ids
    assert "insurance_on_service_pages" in ids
    assert "copyright" in ids
    assert "vat" in ids
    assert "cookie" in ids
    for heading in ("## Overall", "## Key findings", "## Quick wins", "## Score"):
        assert heading in report
    assert "**Firm:** Harbour and Wren Asbestos Surveys" in report
    assert "**Score:** 82/100" in report
    assert "manual review" in report
    assert "23 November 2026" in report or date.today().strftime("%B %Y") in report
    assert payload["signals"]["ukas_numbers"] == ["4321"]
    assert "0121 496 0123" in payload["signals"]["phones"]
    assert "020 7946 0958" not in payload["signals"]["phones"]
