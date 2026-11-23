"""URL, phone, email, and postcode normalisation."""

from normalize import (
    dedup_key,
    emails_in_text,
    host_key,
    names_conflict,
    normalize_phone,
    phone_from_tel,
    phones_in_text,
    postcodes_in_text,
)


def test_uk_numbers_in_text_and_tel_links():
    samples = {
        "0121 496 0123": "01214960123",
        "(0121) 496 0123": "01214960123",
        "+44 121 496 0123": "01214960123",
        "+44 (0)121 496 0123": "01214960123",
        "0044 121 496 0123": "01214960123",
        "020 7946 0958": "02079460958",
        "01632 960123": "01632960123",
        "0800 048 1234": "08000481234",
        "0800 123456": "0800123456",
        "0330 123 4567": "03301234567",
        "07700 900123": "07700900123",
    }
    for raw, expected in samples.items():
        assert phones_in_text(raw) == [expected], raw
        assert normalize_phone(raw) == expected
    assert phone_from_tel("tel:+44-121-496-0123") == "01214960123"
    assert phone_from_tel("tel:01632960123") == "01632960123"


def test_phone_scan_ignores_company_numbers_years_and_ukas_ids():
    text = "Company number 08451234. UKAS 4321. Copyright 2023. Postcode B1 1AA."
    assert phones_in_text(text) == []


def test_placeholder_emails_are_dropped_and_real_ones_kept():
    text = "Write to surveys@harbour-wren.example or info@website.com."
    assert emails_in_text(text) == ["surveys@harbour-wren.example"]


def test_postcodes_are_normalised():
    assert postcodes_in_text("14 Canal Street, Birmingham B1 1AA and sw1a1aa") == ["B1 1AA", "SW1A 1AA"]


def test_www_tracking_slash_and_fragment_share_a_key():
    bare = dedup_key("https://example.com/about")
    assert dedup_key("http://www.Example.com/about/") == bare
    assert dedup_key("https://example.com/about?utm_source=news&fbclid=1#top") == bare
    assert dedup_key("https://example.com/about?b=2&a=1") == dedup_key("https://example.com/about?a=1&b=2")
    assert dedup_key("https://example.com/about?id=2") != bare
    assert host_key("www.Example.com") == host_key("example.com")
    assert host_key("www.Example.com:443") == "example.com"
    assert host_key("surveys.example.com") != host_key("example.com")


def test_ltd_suffix_is_not_a_different_business_name():
    assert names_conflict(["Harbour & Wren Asbestos Surveys", "Harbour & Wren Asbestos Surveys Ltd"]) is False
    assert names_conflict(["North Shore Surveys", "Canal Street Testing Ltd"]) is True
