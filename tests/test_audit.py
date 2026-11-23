"""Site-level checks, the score, and the markdown summary."""

import json
from datetime import date
from pathlib import Path

import pytest

from audit import RUBRIC
from page import parse_page
from runner import run_audit
from trade import TradeError, load_trade

from tests.fakes import MapFetcher, html_page

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 23)
DESCRIPTION = (
    "UKAS accredited asbestos management surveys for commercial properties "
    "across Birmingham and the West Midlands."
)
JSON_LD = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ProfessionalService",
 "name":"Harbour Asbestos Surveys","telephone":"+441214960123",
 "address":{"@type":"PostalAddress","streetAddress":"14 Canal Street",
            "addressLocality":"Birmingham","postalCode":"B1 1AA","addressCountry":"GB"},
 "areaServed":"West Midlands"}
</script>
"""
HEAD = (
    f'<meta name="description" content="{DESCRIPTION}">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<link rel="canonical" href="https://harbour.example/">'
    + JSON_LD
)


def _audit(pages, **kwargs):
    fetcher = kwargs.pop("fetcher", None) or MapFetcher(pages)
    return run_audit(
        kwargs.pop("url", "https://harbour.example/"),
        max_pages=kwargs.pop("max_pages", 10),
        delay=0,
        fetcher=fetcher,
        check_external=kwargs.pop("check_external", False),
        today=TODAY,
        psi_api_key=kwargs.pop("psi_api_key", ""),
        **kwargs,
    )


def _expect(result, score):
    if result["score"] == score:
        return
    lost = [
        f"{item['id']} {item['awarded']}/{item['maximum']} {item['reason']}"
        for item in result["score_breakdown"]
        if item["awarded"] != item["maximum"]
    ]
    findings = [f"{item['severity']} {item['id']}" for item in result["findings"]]
    pytest.fail(
        f"score {result['score']} != {score}\n"
        + "\n".join(lost)
        + "\nfindings: "
        + ", ".join(findings)
        + "\npenalties: "
        + str(result["penalties"])
    )


def _complete_pages():
    home = html_page(
        """
        <nav><a href="/contact">Contact</a> <a href="/privacy">Privacy</a></nav>
        <h1>Asbestos surveys for commercial buildings</h1>
        <p>Harbour Asbestos Surveys carries out HSG264 management surveys and refurbishment and demolition surveys.</p>
        <p>UKAS accredited, accreditation number 4321. ISO/IEC 17020 inspection body. ATaC member. Surveyors hold BOHS P402.</p>
        <p>Public liability insurance of £5 million. Professional indemnity insurance is in place. Employer's liability insurance is in place.</p>
        <p>Registered office: 14 Canal Street, Birmingham B1 1AA. Company number 08451234. VAT number GB123456789.</p>
        <p>Call <a href="tel:+441214960123">0121 496 0123</a> or email <a href="mailto:surveys@harbour-wren.example">surveys@harbour-wren.example</a>.</p>
        <p>A recent testimonial: clear reports and sensible advice. Read the privacy notice. We use cookies.</p>
        <p>CHAS member.</p>
        <img src="/logo.png" alt="Harbour logo">
        <footer>© 2026 Harbour Asbestos Surveys Ltd</footer>
        """,
        title="Harbour Asbestos Surveys in Birmingham",
        head=HEAD,
    )
    contact = html_page(
        """
        <h1>Contact the office</h1>
        <form action="/contact" method="post">
          <input name="name"><input name="email"><textarea name="message"></textarea>
        </form>
        <p>14 Canal Street, Birmingham B1 1AA. <a href="tel:01214960123">0121 496 0123</a></p>
        <footer>© 2026 Harbour Asbestos Surveys Ltd</footer>
        """,
        title="Contact Harbour Asbestos Surveys",
        head='<meta name="viewport" content="width=device-width, initial-scale=1">',
    )
    privacy = html_page(
        "<h1>Privacy notice</h1><p>This privacy notice explains how enquiry details are used to reply.</p>",
        title="Privacy notice for Harbour Asbestos Surveys",
        head='<meta name="viewport" content="width=device-width, initial-scale=1">',
    )
    return {"/": home, "/contact": contact, "/privacy": privacy}


def test_rubric_adds_up_to_100_and_is_documented():
    assert sum(item[3] for item in RUBRIC) == 100
    assert len({item[1] for item in RUBRIC}) == len(RUBRIC)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for _category, _item_id, label, maximum in RUBRIC:
        assert f"| {label} | {maximum} |" in readme


def test_complete_site_scores_100_and_the_report_matches_the_sample_shape():
    result = _audit(_complete_pages())
    _expect(result, 100)
    assert result["findings"] == []
    report = result["markdown"]
    assert report.startswith("# Quick Website Audit Summary")
    assert "## Overall" in report
    assert "## Key findings" in report
    assert "## Quick wins" in report
    assert "**Score:** 100/100" in report
    assert "**Date:** 23 November 2026" in report
    assert "manual review" in report
    assert "does not confirm" in report
    assert "Pagespeed was not" not in report
    assert "PSI_API_KEY is not set" in report


def test_missing_professional_indemnity_costs_four_points():
    pages = _complete_pages()
    pages["/"] = pages["/"].replace("Professional indemnity insurance is in place. ", "")
    result = _audit(pages)
    _expect(result, 96)
    finding = next(item for item in result["findings"] if item["id"] == "professional_indemnity")
    assert "Professional indemnity" in finding["title"]
    assert finding["quick_win"]


def test_accreditation_and_insurance_are_not_repeated_on_every_page():
    pages = {
        "/": html_page(
            "<h1>Surveys</h1><p>We write reports for commercial clients.</p><a href='/services'>Services</a>",
            title="Harbour Asbestos Surveys in Birmingham",
        ),
        "/services": html_page(
            "<h1>Services</h1><p>Management surveys for commercial buildings.</p>",
            title="Asbestos survey services for commercial buildings",
        ),
    }
    result = _audit(pages)
    for page in result["pages"]:
        blob = " ".join(page["warnings"]).lower()
        assert "accreditation" not in blob
        assert "insurance" not in blob
        assert "public liability" not in blob
    ids = [finding["id"] for finding in result["findings"]]
    assert ids.count("ukas") == 1
    assert ids.count("public_liability") == 1


def test_service_pages_are_called_out_when_trust_signals_are_elsewhere():
    pages = _complete_pages()
    pages["/"] = pages["/"].replace(
        '<a href="/contact">',
        '<a href="/services">Services</a> <a href="/contact">',
    )
    pages["/services"] = html_page(
        "<h1>Survey services</h1><p>HSG264 management surveys for commercial buildings. 0121 496 0123. Birmingham B1 1AA.</p>",
        title="Asbestos survey services in Birmingham",
    )
    result = _audit(pages)
    ids = {finding["id"] for finding in result["findings"]}
    assert "accreditation_on_service_pages" in ids
    assert "insurance_on_service_pages" in ids
    ukas = next(item for item in result["score_breakdown"] if item["id"] == "ukas")
    assert ukas["awarded"] == ukas["maximum"]


def test_nav_contact_word_is_not_a_phone_but_tel_and_mailto_are():
    weak = {
        "/": html_page(
            "<nav>Contact</nav><h1>Asbestos surveys for commercial clients</h1><p>We write reports.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        )
    }
    weak_result = _audit(weak)
    assert any(finding["id"] == "phone" for finding in weak_result["findings"])
    assert weak_result["signals"]["phones"] == []

    strong = {
        "/": html_page(
            '<h1>Asbestos surveys for commercial clients</h1>'
            '<a href="tel:01632960123">Ring</a> <a href="mailto:office@harbour.example">Write</a>',
            title="Harbour Asbestos Surveys in Birmingham",
        )
    }
    strong_result = _audit(strong)
    assert strong_result["signals"]["phones"] == ["01632 960123"]
    assert strong_result["signals"]["emails"] == ["office@harbour.example"]
    assert not any(finding["id"] == "phone" for finding in strong_result["findings"])


def test_phone_and_postcode_mismatches_and_formatting_aliases():
    mismatch = {
        "/": html_page(
            "<h1>Home</h1><p>0121 496 0123. Birmingham B1 1AA.</p><a href='/office'>Office</a>",
            title="Harbour Asbestos Surveys in Birmingham",
        ),
        "/office": html_page(
            "<h1>Office</h1><p>020 7946 0958. Manchester M1 1AE.</p>",
            title="Harbour Asbestos Surveys Manchester office",
        ),
    }
    result = _audit(mismatch)
    ids = {finding["id"] for finding in result["findings"]}
    assert "nap_phone" in ids
    assert "nap_postcode" in ids
    phones = next(item for item in result["score_breakdown"] if item["id"] == "phones_consistent")
    assert phones["awarded"] == 0

    same = {
        "/": html_page(
            "<h1>Home</h1><p>0121 496 0123. Birmingham B1 1AA.</p><a href='/office'>Office</a>",
            title="Harbour Asbestos Surveys in Birmingham",
        ),
        "/office": html_page(
            "<h1>Office</h1><p>+44 (0)121 496 0123. Birmingham B11AA.</p>",
            title="Harbour Asbestos Surveys office line",
        ),
    }
    same_result = _audit(same)
    assert not any(finding["id"] in {"nap_phone", "nap_postcode"} for finding in same_result["findings"])


def test_outdated_survey_names_and_placeholders():
    old = {
        "/": html_page(
            "<h1>Surveys</h1><p>Book a type 2 survey or a type 3 survey.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        )
    }
    old_result = _audit(old)
    ids = {finding["id"] for finding in old_result["findings"]}
    assert "terminology" in ids
    assert "outdated" in ids

    both = {
        "/": html_page(
            "<h1>Surveys</h1><p>A type 2 survey is now an HSG264 management survey.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        )
    }
    both_result = _audit(both)
    both_ids = {finding["id"] for finding in both_result["findings"]}
    assert "outdated_alongside" in both_ids
    assert "terminology" not in both_ids
    terminology = next(item for item in both_result["score_breakdown"] if item["id"] == "terminology")
    assert terminology["awarded"] == terminology["maximum"]

    placeholder = {
        "/": html_page(
            "<h1>Welcome to My Company</h1><p>lorem ipsum dolor sit amet. Email info@website.com.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        )
    }
    placeholder_result = _audit(placeholder)
    assert any(finding["id"] == "placeholder" for finding in placeholder_result["findings"])
    assert placeholder_result["signals"]["emails"] == []


def test_company_number_needs_context_and_ukas_number_ignores_iso_and_years():
    page = parse_page(
        "https://harbour.example/",
        html_page(
            "<h1>Surveys</h1><p>Call 0121 496 0123. UKAS accredited. ISO/IEC 17020. UKAS number 2024.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        ),
    )
    from audit import find_company_numbers, find_ukas_numbers

    assert find_company_numbers(page.text) == []
    assert find_ukas_numbers(page.text) == []
    numbered = parse_page(
        "https://harbour.example/",
        html_page(
            "<p>Company number SC123456. Company number 0845 1234. VAT GB123 4567 89. "
            "UKAS accreditation number 4321.</p>",
            title="Harbour Asbestos Surveys in Birmingham",
        ),
    )
    assert "SC123456" in find_company_numbers(numbered.text)
    assert "08451234" in find_company_numbers(numbered.text)
    assert find_ukas_numbers(numbered.text) == ["4321"]


def test_schema_https_noindex_and_holding_page():
    missing_area = html_page(
        "<h1>Surveys</h1>",
        title="Harbour Asbestos Surveys in Birmingham",
        head="""
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"LocalBusiness","name":"Harbour Asbestos Surveys",
         "telephone":"01214960123","address":{"@type":"PostalAddress","postalCode":"B1 1AA"}}
        </script>
        """,
    )
    result = _audit({"/": missing_area})
    fields = next(item for item in result["score_breakdown"] if item["id"] == "schema_fields")
    assert fields["awarded"] == 0
    assert any(finding["id"] == "schema_fields" for finding in result["findings"])

    insecure = _audit({"/": html_page("<h1>Surveys</h1>", title="Harbour Asbestos Surveys in Birmingham")}, url="http://harbour.example/")
    https = next(item for item in insecure["score_breakdown"] if item["id"] == "https")
    assert https["awarded"] == 0
    mixed = next(item for item in insecure["score_breakdown"] if item["id"] == "mixed_content")
    assert mixed["awarded"] == mixed["maximum"]

    mixed_page = html_page(
        '<h1>Surveys</h1><img src="http://cdn.example/logo.png" alt="logo">',
        title="Harbour Asbestos Surveys in Birmingham",
    )
    mixed_result = _audit({"/": mixed_page})
    assert any(finding["id"] == "mixed_content" for finding in mixed_result["findings"])

    hidden = html_page(
        "<h1>Surveys</h1>",
        title="Harbour Asbestos Surveys in Birmingham",
        head='<meta name="robots" content="noindex, nofollow">',
    )
    hidden_result = _audit({"/": hidden})
    assert any(finding["id"] == "noindex" for finding in hidden_result["findings"])

    parked = html_page("<h1>Coming soon</h1><p>This website is under construction.</p>", title="Coming soon")
    parked_result = _audit({"/": parked})
    assert any(finding["id"] == "holding" for finding in parked_result["findings"])


def test_pagespeed_is_optional_and_not_part_of_the_score():
    pages = _complete_pages()
    skipped = _audit(pages, psi_api_key="")
    assert skipped["pagespeed"]["skipped"] is True
    with_key_pages = dict(pages)
    payload = json.dumps({"lighthouseResult": {"categories": {"performance": {"score": 0.42}}}})
    fetcher = MapFetcher({**with_key_pages, "pagespeed": payload})
    scored = _audit(with_key_pages, fetcher=fetcher, psi_api_key="test-key")
    assert scored["pagespeed"]["mobile_score"] == 42
    assert scored["score"] == skipped["score"]
    assert "42/100" in scored["markdown"]


def test_other_trade_with_empty_lists_is_not_penalised_for_asbestos_phrases(tmp_path, monkeypatch):
    profile = {
        "id": "gas",
        "label": "Gas",
        "key_page_patterns": ["service"],
        "accreditation": {
            "ukas_terms": [],
            "trade_bodies": [],
            "hse_terms": [],
            "standards": [],
            "general_schemes": [],
        },
        "terminology": {"current": [], "outdated_patterns": []},
        "service_conflict": {"removal": [], "survey_only": []},
    }
    (tmp_path / "gas.json").write_text(json.dumps(profile), encoding="utf-8")
    monkeypatch.setattr("runner.load_trade", lambda trade_id: load_trade(trade_id, directory=tmp_path))
    result = _audit(
        {"/": html_page("<h1>Boiler service</h1><p>We fix boilers.</p>", title="Boiler service in Birmingham today")},
        trade="gas",
    )
    items = {item["id"]: item for item in result["score_breakdown"]}
    for item_id in ("ukas", "ukas_number", "iso", "trade_body", "hse", "general_scheme", "terminology", "outdated"):
        assert items[item_id]["awarded"] == items[item_id]["maximum"]
        assert items[item_id]["reason"] == "Not used for this trade."
    with pytest.raises(TradeError):
        load_trade("not-a-trade")
    with pytest.raises(TradeError):
        load_trade("no_such_trade")


def test_unreachable_homepage_scores_zero():
    result = _audit({"/gone": html_page("<h1>Elsewhere</h1>")}, url="https://harbour.example/")
    _expect(result, 0)
    assert result["findings"][0]["id"] == "homepage_unreachable"
    assert len(result["score_breakdown"]) == len(RUBRIC)
