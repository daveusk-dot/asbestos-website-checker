"""Batch mode writes reports and an updated tracker copy, not the source file."""

from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from batch import run_batch
from fetch import FetchResult
from runner import run_audit

from tests.fakes import html_page

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 23)


def _fetcher(url, headers=None, timeout=None, read_body=True):
    parsed = urlparse(url)
    if (parsed.path or "/") == "/robots.txt":
        text = "User-agent: *\nDisallow:\n"
        return FetchResult(url=url, status_code=200, text=text, headers={"content-type": "text/plain"}, content=text.encode())
    title = f"{(parsed.hostname or 'firm').split('.')[0].title()} Asbestos Surveys in Birmingham"
    body = html_page(f"<h1>Surveys</h1><p>0121 496 0123. Birmingham B1 1AA.</p>", title=title)
    return FetchResult(url=url, status_code=200, text=body, headers={"content-type": "text/html"}, content=body.encode())


def test_batch_fills_scores_without_touching_the_source_or_the_repo_tracker(tmp_path):
    live = (ROOT / "data" / "audit_test_asbestos_20.csv").read_bytes()
    source = tmp_path / "tracker.csv"
    source.write_text(
        "test_slot,firm_name,website,trade,audit_run_date,audit_score,notes\n"
        "1,Alpha Surveys,https://alpha.example/,asbestos_surveying,,,\n"
        "2,Beta Surveys,https://beta.example/,asbestos_surveying,,,\n"
        ",,,asbestos_surveying,,,\n"
        "4,Skipped,https://skip.example/,no_such_trade,,,\n",
        encoding="utf-8",
    )
    original = source.read_text(encoding="utf-8")
    outcome = run_batch(
        source,
        tmp_path / "out",
        run_audit=run_audit,
        delay=0,
        check_external=False,
        psi_api_key="",
        today=TODAY,
        fetcher=_fetcher,
    )
    assert source.read_text(encoding="utf-8") == original
    assert (ROOT / "data" / "audit_test_asbestos_20.csv").read_bytes() == live
    updated = (tmp_path / "out" / "tracker.updated.csv").read_text(encoding="utf-8")
    lines = updated.strip().splitlines()
    assert lines[1].split(",")[4] == "2026-11-23"
    assert lines[1].split(",")[5].isdigit()
    assert lines[2].split(",")[4] == "2026-11-23"
    assert lines[3].split(",")[4] == ""
    assert lines[3].split(",")[5] == ""
    assert lines[4].split(",")[5] == ""
    assert outcome["audited"] == 2
    assert outcome["skipped_blank"] == 1
    assert outcome["failures"]
    alpha = next((tmp_path / "out").glob("01-alpha-surveys-*.md"))
    report = alpha.read_text(encoding="utf-8")
    assert "Alpha Surveys" in report
    assert "## Overall" in report
    assert "manual review" in report
