"""Crawler behaviour: hosts, robots, non-HTML, and broken links."""

import time
from datetime import date

from fetch import FetchResult, build_user_agent
from runner import run_audit
from website import effective_delay

from tests.fakes import MapFetcher, html_page


def test_user_agent_names_the_project_and_optional_contact(monkeypatch):
    monkeypatch.delenv("AUDIT_CONTACT", raising=False)
    assert "AsbestosWebsiteChecker/1.0" in build_user_agent()
    assert "github.com/daveusk-dot/asbestos-website-checker" in build_user_agent()
    assert "contact:" not in build_user_agent()
    monkeypatch.setenv("AUDIT_CONTACT", "audit@example.com")
    assert "contact: audit@example.com" in build_user_agent()


def test_www_redirect_and_duplicate_links_are_fetched_once():
    home = html_page(
        """
        <a href="http://www.harbour.example/about/">slash</a>
        <a href="https://harbour.example/about?utm_source=news#x">utm</a>
        <a href="https://www.harbour.example/about">www</a>
        <a href="/brochure.pdf">pdf</a>
        <a href="/private.html">secret</a>
        <a href="/download">file</a>
        <a href="https://other.example/missing">ext</a>
        <a href="tel:01632960123">call</a>
        <h1>Surveys</h1>
        """,
        head='<meta name="viewport" content="width=device-width, initial-scale=1">',
    )
    about = html_page("<h1>About</h1><p>01632 960123</p>", title="About Harbour Asbestos Surveys")

    pages = {
        "/": FetchResult(
            url="https://harbour.example/",
            status_code=200,
            text=home,
            headers={"content-type": "text/html"},
            content=home.encode(),
        ),
        "/about": about,
        "/download": (200, "%PDF-1.4 not html", "application/pdf"),
        "/private.html": html_page("<p>ROBOTS-SECRET-PAGE</p>", title="Secret page title here"),
        ("other.example", "/missing"): (404, "gone", "text/html"),
    }
    # MapFetcher looks up (host, path) before path. The redirect result is stored at path /.
    fetcher = MapFetcher(pages, robots="User-agent: *\nDisallow: /private.html\n")
    # Serve the redirected homepage from whichever host is requested.
    original = fetcher.__call__

    def fetch(url, headers=None, timeout=None, read_body=True):
        return original(url, headers=headers, timeout=timeout, read_body=read_body)

    fetcher.__call__ = fetch
    result = run_audit(
        "http://www.harbour.example/",
        max_pages=10,
        delay=0,
        fetcher=fetcher,
        check_external=True,
        today=date(2026, 11, 23),
        psi_api_key="",
    )
    assert result["final_url"] == "https://harbour.example/"
    about_fetches = [url for url in fetcher.urls if urlparse_path(url) == "/about"]
    assert about_fetches == ["https://harbour.example/about"]
    titles = {page["title"] for page in result["pages"]}
    assert "About Harbour Asbestos Surveys" in titles
    assert all("ROBOTS-SECRET" not in page["title"] for page in result["pages"])
    reasons = {item["reason"] for item in result["skipped"]}
    assert "robots.txt" in reasons
    assert "non-html extension" in reasons
    assert "non-html response" in reasons
    broken = [item for item in result["external_links"] if item["classification"] == "broken"]
    assert broken[0]["url"] == "https://other.example/missing"
    assert broken[0]["sources"] == ["https://harbour.example/"]
    assert "github.com/daveusk-dot/asbestos-website-checker" in result["user_agent"]
    assert fetcher.headers["User-Agent"] == result["user_agent"]


def test_empty_and_nested_titles_do_not_crash():
    pages = {
        "/": html_page(
            '<h1>Home</h1><a href="/empty">empty</a><a href="/nested">nested</a>',
            title="Harbour Asbestos Surveys home",
        ),
        "/empty": "<html><head><title></title></head><body><h1>Empty</h1></body></html>",
        "/nested": "<html><head><title>Foo <span>Bar</span></title></head><body><h1>Nested</h1></body></html>",
    }
    result = run_audit(
        "https://harbour.example/",
        delay=0,
        fetcher=MapFetcher(pages),
        check_external=False,
        psi_api_key="",
        today=date(2026, 11, 23),
    )
    by_path = {page["url"].rstrip("/").rsplit("/", 1)[-1]: page for page in result["pages"]}
    assert by_path["empty"]["title"] == ""
    assert "Missing title" in by_path["empty"]["warnings"]
    assert by_path["nested"]["title"] == "Foo Bar"


def test_max_pages_stops_the_crawl():
    home = html_page('<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a><h1>Home</h1>')
    pages = {"/": home, "/a": html_page("<h1>A</h1>", title="Page A of the asbestos site"), "/b": html_page("<h1>B</h1>", title="Page B of the asbestos site"), "/c": html_page("<h1>C</h1>", title="Page C of the asbestos site")}
    fetcher = MapFetcher(pages)
    result = run_audit(
        "https://harbour.example/",
        max_pages=2,
        delay=0,
        fetcher=fetcher,
        check_external=False,
        psi_api_key="",
        today=date(2026, 11, 23),
    )
    assert result["pages_checked"] == 2
    assert not any(url.endswith("/c") for url in fetcher.urls)


def test_crawl_delay_from_robots_is_capped(monkeypatch):
    slept = []
    monkeypatch.setattr(time, "sleep", lambda seconds: slept.append(seconds))
    fetcher = MapFetcher(
        {"/": html_page("<h1>Home</h1><a href='/next'>next</a>")},
        robots="User-agent: *\nCrawl-delay: 9\nDisallow:\n",
    )
    run_audit(
        "https://harbour.example/",
        max_pages=1,
        delay=0.5,
        fetcher=fetcher,
        check_external=False,
        psi_api_key="",
        today=date(2026, 11, 23),
    )
    assert slept == [5.0]
    assert effective_delay(0.5, None) == 0.5
    assert effective_delay(0, 0) == 0


def test_internal_404_records_the_linking_page():
    pages = {"/": html_page('<h1>Home</h1><a href="/missing">gone</a>')}
    result = run_audit(
        "https://harbour.example/",
        delay=0,
        fetcher=MapFetcher(pages),
        check_external=False,
        psi_api_key="",
        today=date(2026, 11, 23),
    )
    assert result["errors"][0]["url"] == "https://harbour.example/missing"
    assert result["errors"][0]["sources"] == ["https://harbour.example/"]
    assert any(item["id"] == "broken_internal" for item in result["penalties"])


def urlparse_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path or "/"
