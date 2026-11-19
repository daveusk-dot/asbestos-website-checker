"""Tests for the append-only suppression list and pre-send check."""

import subprocess
import sys
from pathlib import Path

import pytest

from compliance.suppression import (
    HEADER_LINE,
    PreSendDecision,
    SuppressionError,
    add,
    is_suppressed,
    pre_send_check,
)

ROOT = Path(__file__).resolve().parents[1]
LIVE_LIST = ROOT / "data" / "suppression_list.csv"


def _empty_list(directory: Path) -> Path:
    path = directory / "suppression_list.csv"
    path.write_text(HEADER_LINE, encoding="utf-8")
    return path


def test_live_list_is_header_only():
    text = LIVE_LIST.read_text(encoding="utf-8")
    assert text == HEADER_LINE


def test_add_appends_and_never_drops_the_previous_row(tmp_path):
    path = _empty_list(tmp_path)
    first = add(
        email="Person@Firm.example",
        reason="opt_out",
        source="email_reply",
        date_added="2026-11-01",
        path=path,
    )
    second = add(
        email="person@firm.example",
        reason="opt_out",
        source="opt_out_link",
        date_added="2026-11-02",
        path=path,
    )
    text = path.read_text(encoding="utf-8")
    assert text.startswith(HEADER_LINE)
    assert text.count("person@firm.example") == 2
    assert first["date_added"] == "2026-11-01"
    assert second["date_added"] == "2026-11-02"
    assert "2026-11-01" in text
    assert "2026-11-02" in text


def test_is_suppressed_is_case_insensitive(tmp_path):
    path = _empty_list(tmp_path)
    add(email="Owner@Firm.example", reason="opt_out", source="manual", path=path)
    assert is_suppressed("owner@firm.example", path=path) is True
    assert is_suppressed("other@firm.example", path=path) is False


def test_email_row_does_not_suppress_the_whole_domain(tmp_path):
    path = _empty_list(tmp_path)
    add(
        email="one@firm.example",
        domain="firm.example",
        reason="opt_out",
        source="email_reply",
        path=path,
    )
    assert is_suppressed("one@firm.example", path=path) is True
    assert is_suppressed("colleague@firm.example", path=path) is False


def test_blank_email_suppresses_the_domain(tmp_path):
    path = _empty_list(tmp_path)
    row = add(domain="blocked.example", reason="complaint", source="phone", path=path)
    assert row["email"] == ""
    assert is_suppressed("anyone@blocked.example", path=path) is True
    assert is_suppressed("anyone@other.example", path=path) is False


def test_mismatched_domain_is_refused_and_file_unchanged(tmp_path):
    path = _empty_list(tmp_path)
    before = path.read_text(encoding="utf-8")
    with pytest.raises(SuppressionError):
        add(
            email="one@firm.example",
            domain="other.example",
            reason="opt_out",
            source="manual",
            path=path,
        )
    assert path.read_text(encoding="utf-8") == before


def test_bad_header_is_not_rewritten(tmp_path):
    path = tmp_path / "suppression_list.csv"
    original = "email,reason\nold@example.com,opt_out\n"
    path.write_text(original, encoding="utf-8")
    with pytest.raises(SuppressionError):
        add(email="new@example.com", reason="opt_out", source="manual", path=path)
    assert path.read_text(encoding="utf-8") == original


def test_missing_file_fails_closed(tmp_path):
    path = tmp_path / "missing.csv"
    with pytest.raises(SuppressionError):
        is_suppressed("owner@firm.example", path=path)
    with pytest.raises(SuppressionError):
        add(email="owner@firm.example", reason="opt_out", source="manual", path=path)
    assert not path.exists()


def test_formula_like_reason_is_neutralised(tmp_path):
    path = _empty_list(tmp_path)
    row = add(
        email="owner@firm.example",
        reason="=HYPERLINK(\"http://example.com\")",
        source="manual",
        path=path,
    )
    assert row["reason"].startswith("'=")
    stored = path.read_text(encoding="utf-8")
    assert "'=HYPERLINK" in stored


def test_pre_send_allows_only_limited_company_and_llp(tmp_path):
    path = _empty_list(tmp_path)
    for status in ("limited_company", "LLP", "limited company", "limited-company"):
        decision = pre_send_check("owner@firm.example", status, path=path)
        assert decision.allowed is True
        assert decision.reasons == []

    for status in ("sole_trader", "sole trader", "ordinary_partnership", "unknown", "", None, "plc"):
        decision = pre_send_check("owner@firm.example", status, path=path)
        assert decision.allowed is False
        assert decision.reasons


def test_pre_send_rejects_suppressed_llp_and_reports_bad_status_too(tmp_path):
    path = _empty_list(tmp_path)
    add(email="owner@firm.example", reason="opt_out", source="email_reply", path=path)
    blocked = pre_send_check("Owner@Firm.example", "llp", path=path)
    assert blocked.allowed is False
    assert any("suppression" in reason for reason in blocked.reasons)

    both = pre_send_check("Owner@Firm.example", "sole_trader", path=path)
    assert both.allowed is False
    assert len(both.reasons) == 2
    assert isinstance(both, PreSendDecision)
    assert both.to_dict()["allowed"] is False


def test_pre_send_rejects_placeholder_email(tmp_path):
    path = _empty_list(tmp_path)
    decision = pre_send_check("{{CONTACT_EMAIL}}", "llp", path=path)
    assert decision.allowed is False
    assert any("placeholder" in reason for reason in decision.reasons)


def test_module_has_no_delete_or_send():
    import compliance.suppression as suppression

    for name in ("delete", "remove", "unsuppress", "send", "send_email", "smtp"):
        assert not hasattr(suppression, name)
    source = Path(suppression.__file__).read_text(encoding="utf-8").lower()
    assert "smtplib" not in source
    assert "import requests" not in source


def test_suppression_does_not_import_the_checker():
    for name in ("checker", "website", "page"):
        sys.modules.pop(name, None)
    import importlib

    import compliance.suppression as suppression

    importlib.reload(suppression)
    assert "checker" not in sys.modules
    assert "website" not in sys.modules
    assert "page" not in sys.modules


def test_cli_add_check_and_reject(tmp_path):
    path = _empty_list(tmp_path)
    base = [
        sys.executable,
        "-m",
        "compliance.suppression",
        "--path",
        str(path),
    ]
    added = subprocess.run(
        base
        + [
            "add",
            "--email",
            "Person@Firm.example",
            "--reason",
            "opt_out",
            "--source",
            "email_reply",
            "--date",
            "2026-11-19",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert added.returncode == 0, added.stderr

    suppressed = subprocess.run(
        base + ["is-suppressed", "--email", "person@firm.example"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert suppressed.returncode == 1
    assert "suppressed=yes" in suppressed.stdout

    clear = subprocess.run(
        base + ["is-suppressed", "--email", "other@firm.example"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert clear.returncode == 0
    assert "suppressed=no" in clear.stdout

    allowed = subprocess.run(
        base
        + [
            "pre-send-check",
            "--email",
            "other@firm.example",
            "--legal-status",
            "llp",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert allowed.returncode == 0
    assert "allowed=yes" in allowed.stdout

    refused = subprocess.run(
        base
        + [
            "pre-send-check",
            "--email",
            "other@firm.example",
            "--legal-status",
            "ordinary_partnership",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 1
    assert "allowed=no" in refused.stdout

    missing = subprocess.run(
        [
            sys.executable,
            "-m",
            "compliance.suppression",
            "--path",
            str(tmp_path / "absent.csv"),
            "pre-send-check",
            "--email",
            "other@firm.example",
            "--legal-status",
            "llp",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert missing.returncode == 2
    assert "error:" in missing.stderr
