"""Locks the compliance templates: stop rules, footer, and placeholders."""

import csv
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
RAW_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _reserved_example(address: str) -> bool:
    domain = address.rsplit("@", 1)[1].lower()
    return domain == "example" or domain.endswith(".example") or domain in {
        "example.com",
        "example.org",
        "example.net",
    }

REQUIRED_IN_EVERY_EMAIL = [
    "{{SENDER_NAME}}",
    "{{SENDER_ROLE}}",
    "{{BUSINESS_NAME}}",
    "{{POSTAL_ADDRESS}}",
    "{{SENDER_EMAIL}}",
    "{{COMPANY_NUMBER_LINE}}",
    "{{SOURCE_DIRECTORY}}",
    "{{SOURCE_DATE}}",
    "{{FIRM_NAME}}",
    "{{PRIVACY_NOTICE_URL}}",
    "{{OPT_OUT_URL}}",
    "unsubscribe",
    "manual review",
    "Where we obtained your details:",
]


def _footer() -> str:
    text = (ROOT / "compliance" / "email_footer.md").read_text(encoding="utf-8")
    match = re.search(r"```\n(.*?)```", text, re.S)
    assert match, "email footer block missing"
    return match.group(1).strip("\n")


def _template_files():
    roots = [
        ROOT / "outreach",
        ROOT / "drips",
        ROOT / "pricing",
        ROOT / "data",
        ROOT / "compliance",
        ROOT / "README.md",
    ]
    files = []
    for entry in roots:
        if entry.is_file():
            files.append(entry)
        else:
            files.extend(path for path in entry.rglob("*") if path.is_file())
    return files


def test_documented_placeholders_match_the_templates():
    documented = set(TOKEN.findall((ROOT / "compliance" / "PLACEHOLDERS.md").read_text(encoding="utf-8")))
    used = set()
    for path in _template_files():
        if path.name == "PLACEHOLDERS.md":
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".csv"}:
            continue
        used.update(TOKEN.findall(path.read_text(encoding="utf-8")))
    assert used == documented
    assert "PLACEHOLDER" not in documented


def test_drip_sequences_stop_on_reply_and_opt_out():
    footer = _footer()
    for path in (ROOT / "drips").glob("*/sequence.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        markdown = path.with_name("sequence.md").read_text(encoding="utf-8")
        assert data["sends_automatically"] is False
        assert data["stop_on"] == ["reply", "opt_out"]
        assert data["on_opt_out"] == "append_to_suppression_list"
        assert data["allowed_legal_status"] == ["limited_company", "llp"]
        assert "sole_trader" in data["excluded_legal_status"]
        assert "ordinary_partnership" in data["excluded_legal_status"]
        assert "unknown" in data["excluded_legal_status"]
        offsets = [email["day_offset"] for email in data["emails"]]
        assert offsets == sorted(set(offsets))
        assert 3 <= len(data["emails"]) <= 5
        assert any(email["requires_audit_finding"] for email in data["emails"])
        for email in data["emails"]:
            assert email["subject"] in markdown
            for paragraph in email["body"].strip().split("\n\n"):
                assert paragraph.strip() in markdown
            for token in REQUIRED_IN_EVERY_EMAIL:
                assert token in email["body"]
            assert footer in email["body"]


def test_asbestos_outreach_templates_carry_the_footer_and_stop_rules():
    footer = _footer()
    sequence = yaml.safe_load(
        (ROOT / "outreach" / "asbestos" / "sequence.yaml").read_text(encoding="utf-8")
    )
    assert sequence["sends_automatically"] is False
    assert sequence["stop_on"] == ["reply", "opt_out"]
    assert sequence["on_opt_out"] == "append_to_suppression_list"
    assert sequence["requires_real_finding_before_start"] is True
    assert [email["day_offset"] for email in sequence["emails"]] == [0, 5, 12]
    for email in sequence["emails"]:
        body_file = ROOT / "outreach" / "asbestos" / email["body_file"]
        text = body_file.read_text(encoding="utf-8")
        assert email["subject"] in text
        assert footer in text
        for token in REQUIRED_IN_EVERY_EMAIL:
            assert token in text
        assert "automated check" in text


def test_no_live_email_addresses_in_templates():
    for path in _template_files():
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".csv"}:
            continue
            matches = RAW_EMAIL.findall(path.read_text(encoding="utf-8"))
            unexpected = [item for item in matches if not _reserved_example(item)]
            assert unexpected == [], (path, unexpected)


def test_trackers_contain_no_firms():
    firm_list = (ROOT / "data" / "firm_list_template.csv").read_text(encoding="utf-8").strip()
    assert firm_list == (
        "firm_name,website,trade,companies_house_number,legal_status,"
        "legal_status_checked_date,contact_name,contact_role,contact_email,"
        "email_source,accreditation,source_directory,eligible_for_cold_email"
    )
    with (ROOT / "data" / "audit_test_asbestos_20.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    for index, row in enumerate(rows, start=1):
        assert row["test_slot"] == str(index)
        assert row["trade"] == "asbestos_surveying"
        assert row["firm_name"] == ""
        assert row["contact_email"] == ""
        assert row["website"] == ""
