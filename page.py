"""Extract signals from one HTML page.

Accreditation, insurance, and contact wording are not judged here. Those
are site-level checks. This module only records what the page contains,
plus the technical warnings that really do belong to a single page.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from normalize import (
    email_from_mailto,
    emails_in_text,
    host_key,
    normalize_link,
    phone_from_tel,
    phones_in_text,
    postcodes_in_text,
    same_site,
)

COPYRIGHT_YEAR = re.compile(
    r"(?:©|\(c\)|copyright)\s*(?:(?:19|20)\d{2}\s*[-–—]\s*)?((?:19|20)\d{2})",
    re.IGNORECASE,
)
COPYRIGHT_NAME = re.compile(
    r"(?:©|\(c\)|copyright)\s+(?:(?:19|20)\d{2}\s*[-–—]\s*)?(?:(?:19|20)\d{2}\s+)?(.+)",
    re.IGNORECASE,
)
CONTACT_PATH = ("contact", "enquiry", "enquir", "get-in-touch", "get_in_touch")
TITLE_MIN = 15
TITLE_MAX = 60


@dataclass
class Page:
    url: str
    title: str = ""
    text: str = ""
    raw_text: str = ""
    meta_description: str = ""
    canonical: str | None = None
    has_viewport: bool = False
    noindex: bool = False
    h1s: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    postcodes: list[str] = field(default_factory=list)
    json_ld: list[dict] = field(default_factory=list)
    json_ld_errors: int = 0
    names: list[str] = field(default_factory=list)
    copyright_years: list[int] = field(default_factory=list)
    mixed_content: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_contact_page: bool = False

    def as_dict(self) -> dict:
        from normalize import format_phone

        return {
            "url": self.url,
            "title": self.title,
            "warnings": list(self.warnings),
            "link_count": len(self.internal_links),
            "phones": [format_phone(phone) for phone in self.phones],
            "emails": list(self.emails),
            "postcodes": list(self.postcodes),
            "h1": list(self.h1s),
            "noindex": self.noindex,
            "meta_description": self.meta_description,
        }


def extract_title(soup: BeautifulSoup) -> str:
    """Title text without crashing when the tag is empty or has child tags.

    html.parser keeps literal ``<span>`` characters inside ``<title>``.
    ``.string`` is None for an empty title and for a title with several
    children, and calling ``.strip()`` on it raises AttributeError.
    """
    if soup.title is None:
        return ""
    text = soup.title.get_text(" ", strip=True)
    if "<" in text and ">" in text:
        # html.parser leaves literal tags inside <title>. Parse them out.
        # An empty result means the title had tags and no text.
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    text = text.lower().replace("’", "'").replace("`", "'")
    text = text.replace("'", "")
    return re.sub(r"\s+", " ", text).strip()


def _meta_content(soup: BeautifulSoup, name: str) -> str:
    wanted = name.lower()
    for meta in soup.find_all("meta"):
        key = (meta.get("name") or meta.get("property") or "")
        if isinstance(key, list):
            key = " ".join(key)
        if str(key).lower() == wanted:
            return (meta.get("content") or "").strip()
    return ""


def _iter_jsonld(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld(item)
        return
    if isinstance(data, dict):
        graph = data.get("@graph")
        if isinstance(graph, (list, dict)):
            yield from _iter_jsonld(graph)
        if "@type" in data or "name" in data or "telephone" in data:
            yield data


def _jsonld_nodes(soup: BeautifulSoup) -> tuple[list[dict], int]:
    nodes: list[dict] = []
    errors = 0
    for script in soup.find_all("script"):
        kind = script.get("type") or ""
        if isinstance(kind, list):
            kind = " ".join(kind)
        if "ld+json" not in str(kind).lower():
            continue
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            errors += 1
            continue
        nodes.extend(_iter_jsonld(data))
    return nodes, errors


def _copyright_name(raw_text: str) -> str | None:
    match = COPYRIGHT_NAME.search(raw_text or "")
    if not match:
        return None
    raw = match.group(1).strip()
    raw = re.split(r"[|·•\n]", raw)[0]
    raw = re.sub(r"\ball rights reserved\b.*", "", raw, flags=re.IGNORECASE)
    raw = raw.strip(" .-")
    if not (3 <= len(raw) <= 80):
        return None
    if not re.search(r"[A-Za-z]", raw):
        return None
    return raw


def _add_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _form_warnings(soup: BeautifulSoup, url: str) -> tuple[bool, list[str]]:
    path = urlparse(url).path.lower()
    if not any(token in path for token in CONTACT_PATH):
        return False, []
    forms = soup.find_all("form")
    if not forms:
        return True, ["Contact page has no form"]
    for form in forms:
        action = (form.get("action") or "").strip()
        inputs = []
        for control in form.find_all(["input", "textarea", "select"]):
            kind = (control.get("type") or "").lower()
            if kind in {"hidden", "submit", "button", "image", "reset"}:
                continue
            inputs.append(control)
        found = []
        for field_name in ("name", "email", "message", "phone"):
            for control in inputs:
                haystack = " ".join(
                    [
                        control.get("name") or "",
                        control.get("id") or "",
                        control.get("placeholder") or "",
                        control.get("aria-label") or "",
                    ]
                ).lower()
                if field_name in haystack:
                    found.append(field_name)
                    break
        if action and action != "#" and len(found) >= 2:
            return True, []
    warnings = []
    first = forms[0]
    action = (first.get("action") or "").strip()
    if not action or action == "#":
        warnings.append("Contact form has no clear action/destination")
    warnings.append("Contact form missing key fields (name/email/message/phone)")
    return True, warnings


def _mixed_content(soup: BeautifulSoup, page_url: str) -> list[str]:
    if not page_url.startswith("https"):
        return []
    found: list[str] = []
    for tag in soup.find_all(["img", "script", "iframe", "source", "video", "audio", "embed", "link"]):
        if tag.name == "link":
            rel = tag.get("rel") or []
            rel_text = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()
            if not any(token in rel_text for token in ("stylesheet", "icon", "preload")):
                continue
        values = []
        for attr in ("src", "href"):
            if tag.get(attr):
                values.append(tag.get(attr))
        srcset = tag.get("srcset") or ""
        for part in srcset.split(","):
            url = part.strip().split(" ")[0]
            if url:
                values.append(url)
        for value in values:
            if isinstance(value, str) and value.startswith("http://") and value not in found:
                found.append(value)
    return found


def parse_page(url: str, html: str, headers: dict | None = None) -> Page:
    headers = {key.lower(): value for key, value in (headers or {}).items()}
    soup = BeautifulSoup(html or "", "html.parser")
    page = Page(url=url)
    page.title = extract_title(soup)
    page.meta_description = _meta_content(soup, "description")
    canonical = soup.find("link", rel="canonical")
    page.canonical = (canonical.get("href") or "").strip() if canonical and canonical.get("href") else None
    page.has_viewport = bool(_meta_content(soup, "viewport"))
    robots = _meta_content(soup, "robots") + " " + _meta_content(soup, "googlebot")
    if "noindex" in robots.lower() or "noindex" in headers.get("x-robots-tag", "").lower():
        page.noindex = True
    page.json_ld, page.json_ld_errors = _jsonld_nodes(soup)
    page.mixed_content = _mixed_content(soup, url)
    page.is_contact_page, form_warnings = _form_warnings(soup, url)
    page.warnings.extend(form_warnings)

    site_key = host_key(urlparse(url).netloc)
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        lowered = href.strip().lower()
        if lowered.startswith("tel:"):
            _add_unique(page.phones, phone_from_tel(href))
            continue
        if lowered.startswith("mailto:"):
            _add_unique(page.emails, email_from_mailto(href))
            continue
        absolute = normalize_link(href, url)
        if not absolute:
            continue
        if same_site(absolute, site_key):
            _add_unique(page.internal_links, absolute)
        else:
            _add_unique(page.external_links, absolute)

    for image in soup.find_all("img"):
        page.images.append(
            {
                "src": image.get("src") or "",
                "alt_present": image.has_attr("alt"),
            }
        )

    og_name = _meta_content(soup, "og:site_name")
    if og_name:
        page.names.append(og_name)

    for node in page.json_ld:
        if isinstance(node.get("name"), str) and node["name"].strip():
            _add_unique(page.names, node["name"].strip())
        telephone = node.get("telephone") or node.get("phone")
        if isinstance(telephone, list):
            telephone = " ".join(str(item) for item in telephone)
        if isinstance(telephone, str):
            for number in phones_in_text(telephone):
                _add_unique(page.phones, number)
            direct = phone_from_tel(telephone) or normalize_phone_direct(telephone)
            _add_unique(page.phones, direct)
        emails = node.get("email")
        if isinstance(emails, str):
            emails = [emails]
        if isinstance(emails, list):
            for email in emails:
                if not isinstance(email, str):
                    continue
                _add_unique(page.emails, email_from_mailto("mailto:" + email))
                for found in emails_in_text(email):
                    _add_unique(page.emails, found)
        address = node.get("address")
        if isinstance(address, dict) and address.get("postalCode"):
            for code in postcodes_in_text(str(address.get("postalCode"))):
                _add_unique(page.postcodes, code)
        elif isinstance(address, str):
            for code in postcodes_in_text(address):
                _add_unique(page.postcodes, code)

    for tag in soup.find_all(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    page.h1s = [
        re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
        for heading in soup.find_all("h1")
    ]
    page.h1s = [heading for heading in page.h1s if heading]
    page.raw_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    page.text = fold(page.raw_text)
    copy_name = _copyright_name(page.raw_text)
    if copy_name:
        _add_unique(page.names, copy_name)
    for year in COPYRIGHT_YEAR.findall(page.raw_text):
        value = int(year)
        if value not in page.copyright_years:
            page.copyright_years.append(value)
    for number in phones_in_text(page.raw_text):
        _add_unique(page.phones, number)
    for email in emails_in_text(page.raw_text):
        _add_unique(page.emails, email)
    for code in postcodes_in_text(page.raw_text):
        _add_unique(page.postcodes, code)

    _technical_warnings(page)
    return page


def normalize_phone_direct(value: str) -> str | None:
    from normalize import normalize_phone

    return normalize_phone(value)


def _technical_warnings(page: Page) -> None:
    if not page.title:
        page.warnings.append("Missing title")
    elif len(page.title) < TITLE_MIN or len(page.title) > TITLE_MAX:
        shown = page.title if len(page.title) <= 80 else page.title[:77] + "..."
        page.warnings.append(f"Title length issue ({len(page.title)} chars): {shown}")
    if not page.h1s:
        page.warnings.append("Missing H1 heading")
    elif len(page.h1s) > 1:
        page.warnings.append(f"Multiple H1 headings ({len(page.h1s)})")
    if not page.has_viewport:
        page.warnings.append("Missing viewport meta tag (mobile rendering risk)")
    if not page.canonical:
        page.warnings.append("Missing canonical tag")
    if not page.meta_description:
        page.warnings.append("Missing meta description")
    if page.noindex:
        page.warnings.append("Page is marked noindex")
