"""Site-level checks and the 100-point score.

Page objects already hold titles, phones, links, and the other raw
signals. Accreditation, insurance, NAP, and the legal items are decided
once for the site, then again for key service paths when those exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlparse

from normalize import format_phone, names_conflict
from page import TITLE_MAX, TITLE_MIN, Page, fold
from trade import TradeProfile
from website import CrawlResult

# (category, id, label, maximum). The maximums add up to 100.
RUBRIC = [
    ("Accreditation and trade bodies", "ukas", "UKAS mentioned", 5),
    ("Accreditation and trade bodies", "ukas_number", "UKAS accreditation number", 4),
    ("Accreditation and trade bodies", "iso", "ISO/IEC 17020 or 17025", 4),
    ("Accreditation and trade bodies", "trade_body", "Trade body (ATaC, ARCA, or BOHS)", 5),
    ("Accreditation and trade bodies", "hse", "HSE licence, or removal not offered", 4),
    ("Accreditation and trade bodies", "general_scheme", "CHAS, SafeContractor, Constructionline, or TrustMark", 2),
    ("Insurance", "public_liability", "Public liability mentioned", 5),
    ("Insurance", "professional_indemnity", "Professional indemnity mentioned", 4),
    ("Insurance", "employers_liability", "Employer's liability mentioned", 2),
    ("Insurance", "insurance_amount", "An insurance amount is stated", 1),
    ("Legal and contact", "company_number", "Company number", 4),
    ("Legal and contact", "registered_office", "Registered office", 3),
    ("Legal and contact", "vat", "VAT number", 2),
    ("Legal and contact", "privacy", "Privacy policy", 3),
    ("Legal and contact", "cookie", "Cookie notice", 2),
    ("Legal and contact", "phone", "UK phone number", 3),
    ("Legal and contact", "email", "Email address", 1),
    ("NAP and schema", "name", "Business name consistent", 3),
    ("NAP and schema", "phones_consistent", "Phone numbers consistent", 4),
    ("NAP and schema", "postcodes_consistent", "Postcodes consistent", 4),
    ("NAP and schema", "schema", "LocalBusiness-type JSON-LD", 2),
    ("NAP and schema", "schema_fields", "JSON-LD name, address, telephone, and areaServed", 1),
    ("Technical", "https", "HTTPS", 8),
    ("Technical", "mixed_content", "No mixed content", 2),
    ("Technical", "meta_description", "Homepage meta description", 2),
    ("Technical", "image_alt", "Image alt text", 2),
    ("Technical", "viewport", "Viewport", 1),
    ("Technical", "canonical", "Canonical", 1),
    ("Technical", "title", "Homepage title length", 1),
    ("Technical", "h1", "Single H1 on the homepage", 1),
    ("Technical", "noindex", "Homepage is not noindex", 1),
    ("Content", "placeholder", "No template or placeholder text", 4),
    ("Content", "holding", "Not a holding page", 3),
    ("Content", "copyright", "Copyright year is current", 1),
    ("Content", "terminology", "Current survey terminology", 3),
    ("Content", "outdated", "Outdated terminology is not used alone", 1),
    ("Content", "testimonials", "Testimonials or reviews", 1),
]

CATEGORY_ORDER = [
    "Accreditation and trade bodies",
    "Insurance",
    "Legal and contact",
    "NAP and schema",
    "Technical",
    "Content",
]

ISO_NUMBERS = {"17020", "17025", "9001", "14001", "45001"}
LOCAL_TYPES = {
    "localbusiness",
    "professionalservice",
    "homeandconstructionbusiness",
    "generalcontractor",
    "organization",
    "organisation",
}
INSURANCE_PHRASES = (
    "public liability",
    "professional indemnity",
    "employers liability",
    "pi cover",
    "pl cover",
    "pi insurance",
    "pl insurance",
)
HOLDING_PHRASES = (
    "under construction",
    "coming soon",
    "website coming soon",
    "this site is being built",
    "this website is parked",
    "domain is parked",
    "domain parked",
)
PLACEHOLDERS = (
    (r"\blorem ipsum\b", "lorem ipsum"),
    (r"\bdolor sit amet\b", "dolor sit amet"),
    (r"\bmy company\b", "My Company"),
    (r"\byour company name\b", "your company name"),
    (r"\bcompany name here\b", "company name here"),
    (r"info@website\.com", "info@website.com"),
    (r"\bemail@example\.com\b", "email@example.com"),
    (r"\buser@domain\.com\b", "user@domain.com"),
    (r"\[your name\]", "[your name]"),
    (r"\[company name\]", "[company name]"),
)
COMPANY_CONTEXT = re.compile(
    r"(?:company|registration|registered)\s+(?:number|no|num)"
    r"|companies house"
    r"|registered in (?:england|scotland|wales|northern ireland)"
)
COMPANY_NUMBER = re.compile(r"\b([a-z]{2}\s?\d{6}|\d{8}|\d{4}\s\d{4})\b", re.IGNORECASE)
VAT_RE = re.compile(r"\bgb\s?(\d{9}|\d{3}\s?\d{4}\s?\d{2})\b", re.IGNORECASE)
SKIP_SERVICE_NAMES = ("privacy", "cookie", "contact", "terms", "legal", "index", "home", "default")


@dataclass
class Assessment:
    start_url: str
    final_url: str
    audited_on: date
    trade_id: str
    trade_label: str
    firm_name: str | None
    pages: list[Page]
    score: int
    items: list[dict]
    findings: list[dict]
    penalties: list[dict]
    notes: list[str]
    signals: dict
    errors: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    external_links: list[dict] = field(default_factory=list)
    pages_checked: int = 0

    @property
    def homepage(self) -> Page | None:
        return self.pages[0] if self.pages else None


def text_has(text: str, phrase: str) -> bool:
    folded = fold(text or "")
    needle = fold(phrase or "")
    if not needle:
        return False
    if re.fullmatch(r"[a-z0-9]+", needle):
        return re.search(rf"\b{re.escape(needle)}\b", folded) is not None
    return needle in folded


def any_phrase(text: str, phrases: list[str] | tuple[str, ...]) -> bool:
    return any(text_has(text, phrase) for phrase in phrases)


def combined_text(pages: list[Page]) -> str:
    return "\n".join(page.text for page in pages)


def assess(crawl: CrawlResult, trade: TradeProfile, today: date, firm_name: str | None = None) -> Assessment:
    assessment = Assessment(
        start_url=crawl.start_url,
        final_url=crawl.final_url,
        audited_on=today,
        trade_id=trade.id,
        trade_label=trade.label,
        firm_name=firm_name,
        pages=list(crawl.pages),
        score=0,
        items=[],
        findings=[],
        penalties=[],
        notes=list(crawl.notes),
        signals={},
        errors=list(crawl.errors),
        skipped=list(crawl.skipped),
        external_links=list(crawl.external_links),
        pages_checked=len(crawl.pages),
    )
    if not crawl.pages:
        _zero_for_unreachable(assessment)
        return assessment

    pages = crawl.pages
    homepage = crawl.homepage or pages[0]
    whole = combined_text(pages)
    services = _service_pages(pages, trade)
    _content_and_https(assessment, pages, homepage, today)
    _contact(assessment, pages)
    _accreditation(assessment, trade, pages, services, whole)
    _insurance(assessment, pages, services, whole)
    _conflict(assessment, trade, pages)
    _legal(assessment, pages, whole)
    _nap(assessment, pages)
    _schema(assessment, pages)
    _terminology(assessment, trade, pages, whole)
    _testimonials(assessment, pages)
    _technical(assessment, pages, homepage)
    _links(assessment)
    _finish(assessment)
    return assessment


def _zero_for_unreachable(assessment: Assessment) -> None:
    for category, item_id, label, maximum in RUBRIC:
        assessment.items.append(
            {
                "category": category,
                "id": item_id,
                "label": label,
                "maximum": maximum,
                "awarded": 0,
                "reason": "The homepage was not fetched.",
            }
        )
    assessment.findings.append(
        {
            "id": "homepage_unreachable",
            "severity": "high",
            "title": "The homepage could not be fetched",
            "detail": "The crawl did not return an HTML page, so the rest of the check did not run.",
            "quick_win": "Confirm the URL opens in a browser, and that robots.txt is not blocking the audit.",
            "pages": [assessment.start_url],
        }
    )
    assessment.score = 0
    assessment.signals = {
        "phones": [],
        "emails": [],
        "postcodes": [],
        "names": [],
        "ukas_numbers": [],
        "company_numbers": [],
        "vat_numbers": [],
        "https": False,
    }


def _add(assessment: Assessment, item_id: str, awarded: int, reason: str) -> None:
    for category, rubric_id, label, maximum in RUBRIC:
        if rubric_id == item_id:
            assessment.items.append(
                {
                    "category": category,
                    "id": item_id,
                    "label": label,
                    "maximum": maximum,
                    "awarded": max(0, min(maximum, int(awarded))),
                    "reason": reason,
                }
            )
            return
    raise KeyError(item_id)


def _finding(
    assessment: Assessment,
    item_id: str,
    severity: str,
    title: str,
    detail: str,
    quick_win: str = "",
    pages: list[str] | None = None,
) -> None:
    if any(item["id"] == item_id for item in assessment.findings):
        return
    assessment.findings.append(
        {
            "id": item_id,
            "severity": severity,
            "title": title,
            "detail": detail,
            "quick_win": quick_win,
            "pages": pages or [],
        }
    )


def _content_and_https(assessment: Assessment, pages: list[Page], homepage: Page, today: date) -> None:
    https = homepage.url.startswith("https")
    assessment.signals["https"] = https
    if https:
        _add(assessment, "https", 8, "The site was fetched over HTTPS.")
    else:
        _add(assessment, "https", 0, "The site was fetched over HTTP.")
        _finding(
            assessment,
            "https",
            "high",
            "The site is not served over HTTPS",
            "The pages we fetched used HTTP. Browsers mark that as not secure, and contact forms should not be submitted on it.",
            "Serve the site over HTTPS and redirect HTTP to HTTPS.",
            [homepage.url],
        )
    mixed = [url for page in pages for url in page.mixed_content]
    if not https:
        _add(assessment, "mixed_content", 2, "Mixed content is only scored on HTTPS sites.")
    elif mixed:
        _add(assessment, "mixed_content", 0, f"{len(mixed)} insecure resource(s) on HTTPS pages.")
        _finding(
            assessment,
            "mixed_content",
            "medium",
            "HTTPS pages load something over HTTP",
            "Browsers can block images or scripts that are still requested over HTTP. "
            + ", ".join(mixed[:3]),
            "Change those image, script, and stylesheet URLs to HTTPS.",
        )
    else:
        _add(assessment, "mixed_content", 2, "No mixed content on the HTTPS pages.")

    hits: list[tuple[str, str]] = []
    for page in pages:
        for pattern, label in PLACEHOLDERS:
            if re.search(pattern, page.text, re.IGNORECASE) or re.search(pattern, page.raw_text, re.IGNORECASE):
                hits.append((label, page.url))
    if hits:
        shown = ", ".join(sorted({label for label, _url in hits}))
        _add(assessment, "placeholder", 0, f"Placeholder text found: {shown}.")
        _finding(
            assessment,
            "placeholder",
            "high",
            "The site still has template or placeholder text",
            f"Seen: {shown}.",
            "Replace leftover template text (such as “My Company”, info@website.com, or lorem ipsum) with the firm’s own details.",
            [url for _label, url in hits[:5]],
        )
    else:
        _add(assessment, "placeholder", 4, "No template or placeholder text was found.")

    if _is_holding(homepage):
        _add(assessment, "holding", 0, "The homepage looks like a holding page.")
        _finding(
            assessment,
            "holding",
            "high",
            "The homepage looks unfinished or parked",
            "The title, heading, or a short page mentions that the site is under construction, coming soon, or parked.",
            "Replace the holding page with the real service, contact, and trust information.",
            [homepage.url],
        )
    else:
        _add(assessment, "holding", 3, "The homepage is not a holding page.")

    years = [year for page in pages for year in page.copyright_years]
    if not years:
        _add(assessment, "copyright", 1, "No copyright year was found.")
    else:
        latest = max(years)
        if latest >= today.year - 1:
            _add(assessment, "copyright", 1, f"The latest copyright year is {latest}.")
        else:
            _add(assessment, "copyright", 0, f"The latest copyright year is {latest}.")
            _finding(
                assessment,
                "copyright",
                "low",
                f"The copyright year is {latest}",
                f"The newest year on the pages is {latest}. A year that far behind makes the site look unmaintained.",
                f"Update the footer copyright to {today.year}.",
            )


def _is_holding(page: Page) -> bool:
    heading = fold(page.title + " " + " ".join(page.h1s))
    if any(phrase in heading for phrase in HOLDING_PHRASES):
        return True
    return len(page.text) < 700 and any(phrase in page.text for phrase in HOLDING_PHRASES)


def _contact(assessment: Assessment, pages: list[Page]) -> None:
    phones = _unique(phone for page in pages for phone in page.phones)
    emails = _unique(email for page in pages for email in page.emails)
    assessment.signals["phones"] = [format_phone(phone) for phone in phones]
    assessment.signals["emails"] = emails
    if phones:
        _add(assessment, "phone", 3, "At least one UK phone number was found.")
    else:
        _add(assessment, "phone", 0, "No UK phone number was found.")
        _finding(
            assessment,
            "phone",
            "high",
            "No UK phone number was found",
            "The check looked at tel: links and at UK-format numbers in the page text. A “Contact” item in the menu is not treated as a phone number.",
            "Put a clickable tel: link, or the phone number in the header or footer of every page.",
        )
    if emails:
        _add(assessment, "email", 1, "An email address was found.")
    else:
        _add(assessment, "email", 0, "No usable email address was found.")
        _finding(
            assessment,
            "email",
            "medium",
            "No email address was found",
            "mailto: links and addresses in the text were checked. Template addresses such as info@website.com do not count.",
            "Add a real work email, ideally as a mailto: link on the contact page.",
        )
    contact_urls = [page.url for page in pages if page.is_contact_page or "contact" in urlparse(page.url).path.lower()]
    if not contact_urls:
        _finding(
            assessment,
            "contact_page",
            "low",
            "No contact page was found",
            "None of the crawled URLs look like a contact page. The word “contact” in a menu is not enough on its own.",
            "Add a contact page with the phone number, email address, and a short form.",
        )


def _accreditation(
    assessment: Assessment,
    trade: TradeProfile,
    pages: list[Page],
    services: list[Page],
    whole: str,
) -> None:
    if not trade.ukas_terms:
        _add(assessment, "ukas", 5, "Not used for this trade.")
        _add(assessment, "ukas_number", 4, "Not used for this trade.")
        numbers: list[str] = []
        mentioned = False
    else:
        mentioned = any_phrase(whole, trade.ukas_terms)
        numbers = find_ukas_numbers(whole) if mentioned else []
        if mentioned:
            _add(assessment, "ukas", 5, "UKAS is mentioned on the site.")
        else:
            _add(assessment, "ukas", 0, "UKAS is not mentioned.")
            _finding(
                assessment,
                "ukas",
                "high",
                "UKAS is not mentioned",
                "None of the crawled pages mention UKAS. For an asbestos surveyor this is one of the first things a client looks for.",
                "If the firm holds UKAS accreditation, name it and put the accreditation number next to it.",
            )
        if numbers:
            _add(assessment, "ukas_number", 4, "A UKAS number was found near the UKAS wording: " + ", ".join(numbers) + ".")
        elif mentioned:
            _add(assessment, "ukas_number", 0, "UKAS is mentioned but no accreditation number was found nearby.")
            _finding(
                assessment,
                "ukas_number",
                "medium",
                "UKAS is mentioned without an accreditation number",
                "A 4 or 5 digit number next to the UKAS wording lets a client look the firm up. Years and ISO standard numbers are ignored.",
                "Add the UKAS accreditation number beside the UKAS wording, for example “UKAS accredited, no. 1234”.",
            )
        else:
            _add(assessment, "ukas_number", 0, "UKAS is not mentioned, so no accreditation number was found.")
    assessment.signals["ukas"] = mentioned
    assessment.signals["ukas_numbers"] = numbers

    if not trade.standards:
        _add(assessment, "iso", 4, "Not used for this trade.")
        found_standards: list[str] = []
    else:
        found_standards = [term for term in trade.standards if text_has(whole, term)]
        if found_standards:
            _add(assessment, "iso", 4, "Found: " + ", ".join(found_standards[:4]) + ".")
        else:
            _add(assessment, "iso", 0, "ISO/IEC 17020 and 17025 were not mentioned.")
            _finding(
                assessment,
                "iso",
                "medium",
                "ISO/IEC 17020 or 17025 is not mentioned",
                "Neither inspection (17020) nor laboratory (17025) wording was found.",
                "If the UKAS schedule covers 17020 or 17025, say so next to the UKAS line.",
            )
    assessment.signals["standards"] = found_standards

    found_bodies: list[str] = []
    if not trade.trade_bodies:
        _add(assessment, "trade_body", 5, "Not used for this trade.")
    else:
        for body in trade.trade_bodies:
            patterns = [str(item).lower() for item in body.get("patterns") or []]
            if patterns and any_phrase(whole, patterns):
                found_bodies.append(str(body.get("label") or body.get("id") or "body"))
        if found_bodies:
            _add(assessment, "trade_body", 5, "Found: " + ", ".join(found_bodies) + ".")
        else:
            _add(assessment, "trade_body", 0, "ATaC, ARCA, and BOHS were not mentioned.")
            _finding(
                assessment,
                "trade_body",
                "medium",
                "No trade body is mentioned",
                "ATaC, ARCA, and BOHS (including P402) were not found.",
                "Name the memberships the firm actually holds, and say P402 where a surveyor holds it.",
            )
        if text_has(whole, "bohs") and not text_has(whole, "p402"):
            _finding(
                assessment,
                "bohs_p402",
                "low",
                "BOHS is mentioned without P402",
                "The pages say BOHS but do not mention the P402 qualification.",
                "If surveyors hold P402, put that next to the BOHS line.",
            )
    assessment.signals["trade_bodies"] = found_bodies

    removal = False
    if trade.removal_terms:
        removal = any(any_phrase(page.text, trade.removal_terms) for page in pages)
    hse = bool(trade.hse_terms) and any_phrase(whole, trade.hse_terms)
    if not trade.hse_terms:
        _add(assessment, "hse", 4, "Not used for this trade.")
    elif hse:
        _add(assessment, "hse", 4, "An HSE asbestos licence is mentioned.")
    elif not removal:
        _add(assessment, "hse", 4, "No removal service is described, so an HSE removal licence is not expected.")
    else:
        _add(assessment, "hse", 0, "Removal is described and no HSE licence is mentioned.")
        _finding(
            assessment,
            "hse",
            "high",
            "Removal is described without an HSE licence",
            "The site talks about asbestos removal but does not mention an HSE asbestos licence. This check cannot tell whether a licence is held.",
            "If removal is offered, state the HSE licence. If it is not offered, remove the removal wording.",
        )

    if not trade.schemes_configured:
        _add(assessment, "general_scheme", 2, "Not used for this trade.")
        schemes: list[str] = []
    else:
        schemes = [term for term in trade.general_schemes if text_has(whole, term)]
        if schemes:
            _add(assessment, "general_scheme", 2, "Found: " + ", ".join(schemes) + ".")
        else:
            _add(assessment, "general_scheme", 0, "CHAS, SafeContractor, Constructionline, and TrustMark were not mentioned.")
            _finding(
                assessment,
                "general_scheme",
                "low",
                "No general pre-qualification scheme is mentioned",
                "CHAS, SafeContractor, Constructionline, and TrustMark were not found. These are optional, but commercial clients often look for one.",
                "If the firm is on one of those schemes, add the logo or the name in the footer.",
            )
    assessment.signals["general_schemes"] = schemes

    if services and _site_has_accreditation(whole, trade) and not any(_page_has_accreditation(page, trade) for page in services):
        paths = ", ".join(urlparse(page.url).path or "/" for page in services[:5])
        _finding(
            assessment,
            "accreditation_on_service_pages",
            "medium",
            "Accreditation is not mentioned on the service pages",
            f"UKAS or a trade body appears somewhere on the site, but not on: {paths}.",
            "Repeat the UKAS line, and any ATaC, ARCA, or BOHS line, on the main service pages.",
            [page.url for page in services[:5]],
        )


def _site_has_accreditation(text: str, trade: TradeProfile) -> bool:
    if trade.ukas_terms and any_phrase(text, trade.ukas_terms):
        return True
    if trade.standards and any_phrase(text, trade.standards):
        return True
    for body in trade.trade_bodies:
        patterns = [str(item) for item in body.get("patterns") or []]
        if patterns and any_phrase(text, patterns):
            return True
    return False


def _page_has_accreditation(page: Page, trade: TradeProfile) -> bool:
    return _site_has_accreditation(page.text, trade)


def _insurance(assessment: Assessment, pages: list[Page], services: list[Page], whole: str) -> None:
    public = text_has(whole, "public liability") or text_has(whole, "pl insurance") or text_has(whole, "pl cover")
    indemnity = text_has(whole, "professional indemnity") or text_has(whole, "pi insurance") or text_has(whole, "pi cover")
    employers = text_has(whole, "employers liability")
    amount = _insurance_amount(whole)
    assessment.signals["insurance"] = {
        "public_liability": public,
        "professional_indemnity": indemnity,
        "employers_liability": employers,
        "amount": amount,
    }
    if public:
        _add(assessment, "public_liability", 5, "Public liability is mentioned.")
    else:
        _add(assessment, "public_liability", 0, "Public liability is not mentioned.")
        _finding(
            assessment,
            "public_liability",
            "high",
            "Public liability insurance is not mentioned",
            "None of the crawled pages mention public liability cover.",
            "Add a short line such as “Public liability insurance is in place” on the homepage and the service pages.",
        )
    if indemnity:
        _add(assessment, "professional_indemnity", 4, "Professional indemnity is mentioned.")
    else:
        _add(assessment, "professional_indemnity", 0, "Professional indemnity is not mentioned.")
        _finding(
            assessment,
            "professional_indemnity",
            "medium",
            "Professional indemnity is not mentioned",
            "Surveying clients often expect to see professional indemnity as well as public liability.",
            "Name professional indemnity cover next to the other insurance, and include the limit if you publish it.",
        )
    if employers:
        _add(assessment, "employers_liability", 2, "Employer's liability is mentioned.")
    else:
        _add(assessment, "employers_liability", 0, "Employer's liability is not mentioned.")
        _finding(
            assessment,
            "employers_liability",
            "low",
            "Employer's liability is not mentioned",
            "Employer's liability was not found. A limited company with staff is normally required to hold it.",
            "If the policy is in place, add “Employer's liability insurance is in place” near the other cover.",
        )
    if amount:
        _add(assessment, "insurance_amount", 1, "A figure was found next to an insurance phrase.")
    else:
        _add(assessment, "insurance_amount", 0, "No £ amount or “million” figure was found next to the insurance wording.")
        if public or indemnity or employers:
            _finding(
                assessment,
                "insurance_amount",
                "low",
                "No insurance amount is stated",
                "Cover is mentioned, but no £ figure or “million” was found next to it.",
                "Add the limit you are willing to publish, for example “public liability of £5 million”.",
            )

    site_has = public or indemnity or employers
    if services and site_has and not any(any_phrase(page.text, INSURANCE_PHRASES) for page in services):
        paths = ", ".join(urlparse(page.url).path or "/" for page in services[:5])
        _finding(
            assessment,
            "insurance_on_service_pages",
            "medium",
            "Insurance is not mentioned on the service pages",
            f"Insurance appears somewhere on the site, but not on: {paths}.",
            "Add the public liability line to the service pages, not only the homepage or the footer of one page.",
            [page.url for page in services[:5]],
        )


def _conflict(assessment: Assessment, trade: TradeProfile, pages: list[Page]) -> None:
    if not trade.removal_terms or not trade.survey_only_terms:
        return
    conflict_pages = []
    for page in pages:
        if any_phrase(page.text, trade.removal_terms) and any_phrase(page.text, trade.survey_only_terms):
            conflict_pages.append(page)
            if "Possible conflicting service wording (removal vs survey only)" not in page.warnings:
                page.warnings.append("Possible conflicting service wording (removal vs survey only)")
    if not conflict_pages:
        return
    assessment.penalties.append(
        {
            "id": "conflict",
            "points": 5,
            "detail": "A page describes both asbestos removal and a survey-only service.",
        }
    )
    paths = ", ".join(urlparse(page.url).path or "/" for page in conflict_pages[:5])
    _finding(
        assessment,
        "conflict",
        "high",
        "Removal and survey-only wording appear on the same page",
        f"This can confuse a client about what is being offered. Pages: {paths}.",
        "Make each page say clearly whether removal is offered or the firm carries out surveys only.",
        [page.url for page in conflict_pages[:5]],
    )


def _legal(assessment: Assessment, pages: list[Page], whole: str) -> None:
    numbers = find_company_numbers(whole)
    vats = find_vat_numbers(whole)
    assessment.signals["company_numbers"] = numbers
    assessment.signals["vat_numbers"] = vats
    if numbers:
        _add(assessment, "company_number", 4, "Company number found: " + ", ".join(numbers) + ".")
    else:
        _add(assessment, "company_number", 0, "No company number was found.")
        _finding(
            assessment,
            "company_number",
            "medium",
            "No company number is shown",
            "A UK limited company is expected to show its registered name and company number. This check only reads the site; it does not look the firm up at Companies House.",
            "If the firm is a limited company, add the company number in the footer.",
        )
    office_pages = [page for page in pages if "registered office" in page.text and page.postcodes]
    if office_pages:
        _add(assessment, "registered_office", 3, "A registered office is shown with a postcode.")
    else:
        _add(assessment, "registered_office", 0, "No registered office with a postcode was found.")
        _finding(
            assessment,
            "registered_office",
            "medium",
            "No registered office is shown",
            "The words “registered office” were not found next to a UK postcode. This applies to limited companies.",
            "Add the registered office, including the postcode, in the footer.",
        )
    if vats:
        _add(assessment, "vat", 2, "VAT number found: " + ", ".join(vats) + ".")
    else:
        _add(assessment, "vat", 0, "No VAT number was found.")
        _finding(
            assessment,
            "vat",
            "low",
            "No VAT number is shown",
            "A GB VAT number was not found. Firms over the threshold normally show it on invoices and often on the site.",
            "If the firm is VAT registered, add the VAT number near the company number.",
        )
    if _has_privacy(pages):
        _add(assessment, "privacy", 3, "A privacy policy link or page was found.")
    else:
        _add(assessment, "privacy", 0, "No privacy policy was found.")
        _finding(
            assessment,
            "privacy",
            "medium",
            "No privacy policy was found",
            "No privacy page or privacy-policy link was found in the crawl.",
            "Publish a privacy notice and link it from the footer.",
        )
    if _has_cookie(pages):
        _add(assessment, "cookie", 2, "A cookie notice was found.")
    else:
        _add(assessment, "cookie", 0, "No cookie notice was found.")
        _finding(
            assessment,
            "cookie",
            "low",
            "No cookie notice was found",
            "No cookie policy, cookie notice, or “we use cookies” line was found.",
            "Add a short cookie notice, or a link to a cookie page, if the site sets non-essential cookies.",
        )


def _nap(assessment: Assessment, pages: list[Page]) -> None:
    names = _unique(name for page in pages for name in page.names)
    assessment.signals["names"] = names
    if not names:
        _add(assessment, "name", 0, "No business name was extracted.")
        _finding(
            assessment,
            "nap_name",
            "low",
            "No consistent business name was extracted",
            "The check looks at JSON-LD, the Open Graph site name, and the copyright line. Page titles are not used, because they vary.",
            "Put the trading name in the structured data and in the copyright line.",
        )
    elif names_conflict(names):
        _add(assessment, "name", 0, "The extracted names do not look like one business.")
        _finding(
            assessment,
            "nap_name",
            "medium",
            "The business name is not consistent",
            "Names seen: " + "; ".join(names[:4]) + ".",
            "Use one trading name in the footer, the structured data, and the page titles.",
            [],
        )
    else:
        _add(assessment, "name", 3, "The extracted names look like one business.")

    phone_sets = [set(page.phones) for page in pages if page.phones]
    if not phone_sets:
        _add(assessment, "phones_consistent", 0, "No phone number was found to compare.")
    elif len(phone_sets) == 1 or set.intersection(*phone_sets):
        _add(assessment, "phones_consistent", 4, "Phone numbers agree across the pages that show one.")
    else:
        _add(assessment, "phones_consistent", 0, "Pages show phone numbers that do not overlap.")
        rendered = []
        for page in pages:
            if page.phones:
                rendered.append(f"{urlparse(page.url).path or '/'}: " + ", ".join(format_phone(p) for p in page.phones))
        _finding(
            assessment,
            "nap_phone",
            "high",
            "Phone numbers do not match across the site",
            "Pages that show a number do not share one. " + "; ".join(rendered[:4]) + ".",
            "Use one main number across the site, or label any extra number as a separate office.",
            [page.url for page in pages if page.phones][:5],
        )

    postcode_sets = [set(page.postcodes) for page in pages if page.postcodes]
    all_codes = _unique(code for page in pages for code in page.postcodes)
    assessment.signals["postcodes"] = all_codes
    if not postcode_sets:
        _add(assessment, "postcodes_consistent", 0, "No UK postcode was found.")
        _finding(
            assessment,
            "postcode",
            "medium",
            "No UK postcode was found",
            "An address with a postcode is part of the name, address, and phone details a client expects.",
            "Add the office address, including the postcode, on the contact page and in the footer.",
        )
    elif len(postcode_sets) == 1 or set.intersection(*postcode_sets):
        _add(assessment, "postcodes_consistent", 4, "Postcodes agree across the pages that show one.")
        if len(all_codes) > 1:
            assessment.notes.append(
                "Postcodes seen: " + ", ".join(all_codes) + ". They overlap across pages, so this was not scored as a mismatch."
            )
    else:
        _add(assessment, "postcodes_consistent", 0, "Pages show postcodes that do not overlap.")
        _finding(
            assessment,
            "nap_postcode",
            "high",
            "Addresses do not match across the site",
            "Postcodes seen: " + ", ".join(all_codes) + ". Pages that show an address do not share one.",
            "Use one office address, or label each extra postcode as a branch.",
            [page.url for page in pages if page.postcodes][:5],
        )


def _schema(assessment: Assessment, pages: list[Page]) -> None:
    parse_errors = sum(page.json_ld_errors for page in pages)
    if parse_errors:
        assessment.notes.append(
            f"{parse_errors} JSON-LD block{'s' if parse_errors != 1 else ''} could not be parsed."
        )
    node = _best_local_node(pages)
    if node is None:
        _add(assessment, "schema", 0, "No LocalBusiness-type JSON-LD was found.")
        _add(assessment, "schema_fields", 0, "No LocalBusiness JSON-LD, so the fields could not be checked.")
        _finding(
            assessment,
            "schema",
            "medium",
            "No LocalBusiness structured data was found",
            "No JSON-LD of type LocalBusiness, ProfessionalService, or a similar local type was found.",
            "Add JSON-LD with the name, address, telephone, and areaServed. ProfessionalService is a good fit for a surveyor.",
        )
        return
    types = _node_types(node)
    only_org = types and all(item in {"organization", "organisation"} for item in types)
    reason = "JSON-LD type: " + ", ".join(types or ["unknown"]) + "."
    if only_org:
        reason += " Organization was accepted because it includes an address or telephone. LocalBusiness or ProfessionalService is a closer type."
        assessment.notes.append(
            "Structured data uses Organization. LocalBusiness or ProfessionalService would describe a local surveyor more closely."
        )
    _add(assessment, "schema", 2, reason)
    missing = []
    if not _field_name(node):
        missing.append("name")
    if not _field_address(node):
        missing.append("address")
    if not _field_phone(node):
        missing.append("telephone")
    if not _field_area(node):
        missing.append("areaServed")
    if missing:
        _add(assessment, "schema_fields", 0, "Missing: " + ", ".join(missing) + ".")
        _finding(
            assessment,
            "schema_fields",
            "low",
            "Structured data is missing some local-business fields",
            "Missing: " + ", ".join(missing) + ".",
            "Complete the JSON-LD so name, address, telephone, and areaServed are all filled in.",
        )
    else:
        _add(assessment, "schema_fields", 1, "name, address, telephone, and areaServed are present.")


def _terminology(assessment: Assessment, trade: TradeProfile, pages: list[Page], whole: str) -> None:
    if not trade.current_terms:
        _add(assessment, "terminology", 3, "Not used for this trade.")
        current = False
    else:
        current = any_phrase(whole, trade.current_terms)
        if current:
            _add(assessment, "terminology", 3, "Current survey terminology was found.")
        else:
            _add(assessment, "terminology", 0, "HSG264, management, and refurbishment/demolition wording was not found.")
            _finding(
                assessment,
                "terminology",
                "medium",
                "Current asbestos survey terms were not found",
                "The pages do not mention HSG264, a management survey, or a refurbishment and demolition survey.",
                "Describe the work with the current names: management survey, and refurbishment and demolition survey (HSG264).",
            )
    assessment.signals["current_terminology"] = current

    if not trade.outdated_patterns:
        _add(assessment, "outdated", 1, "Not used for this trade.")
        return
    outdated_pages = []
    for page in pages:
        if any(re.search(pattern, page.text, re.IGNORECASE) for pattern in trade.outdated_patterns):
            outdated_pages.append(page)
    if not outdated_pages:
        _add(assessment, "outdated", 1, "Type 2 / Type 3 wording was not found.")
    elif current:
        _add(assessment, "outdated", 1, "Older Type 2 / Type 3 wording is present, alongside current terms.")
        _finding(
            assessment,
            "outdated_alongside",
            "low",
            "Type 2 and Type 3 wording is still used",
            "Those names were replaced by the management survey and the refurbishment and demolition survey. The current names are also on the site.",
            "Retire Type 2 and Type 3, or add a note that they are the old names for the HSG264 surveys.",
            [page.url for page in outdated_pages[:5]],
        )
    else:
        _add(assessment, "outdated", 0, "Type 2 / Type 3 wording is used without the current terms.")
        _finding(
            assessment,
            "outdated",
            "medium",
            "The site uses outdated Type 2 or Type 3 survey names",
            "Type 2 and Type 3 were replaced by the management survey and the refurbishment and demolition survey in HSG264. The current names were not found.",
            "Replace Type 2 and Type 3 with management survey and refurbishment and demolition survey.",
            [page.url for page in outdated_pages[:5]],
        )


def _testimonials(assessment: Assessment, pages: list[Page]) -> None:
    phrases = (
        "testimonial",
        "what our clients say",
        "what our customers say",
        "trustpilot",
        "google review",
    )
    found = False
    for page in pages:
        if any(phrase in page.text for phrase in phrases):
            found = True
            break
        for node in page.json_ld:
            keys = {str(key).lower() for key in node}
            if "review" in keys or "aggregaterating" in keys:
                found = True
                break
        if found:
            break
    if found:
        _add(assessment, "testimonials", 1, "A testimonial or review was found.")
    else:
        _add(assessment, "testimonials", 0, "No testimonials or reviews were found.")
        _finding(
            assessment,
            "testimonials",
            "low",
            "No testimonials or reviews were found",
            "A short client comment, or a link to an independent review, is a useful trust signal. This check cannot tell whether a review is genuine.",
            "Add one or two real client comments, or a link to the review profile you actually use.",
        )


def _technical(assessment: Assessment, pages: list[Page], homepage: Page) -> None:
    description = homepage.meta_description.strip()
    length = len(description)
    if 50 <= length <= 160:
        _add(assessment, "meta_description", 2, f"Homepage meta description is {length} characters.")
    elif description:
        _add(assessment, "meta_description", 1, f"Homepage meta description is {length} characters (aim for 50–160).")
        _finding(
            assessment,
            "meta_description",
            "low",
            "The homepage meta description is an awkward length",
            f"It is {length} characters. A length of about 50–160 characters is the usual range.",
            "Rewrite the homepage meta description so it is one clear sentence of about 50–160 characters.",
            [homepage.url],
        )
    else:
        _add(assessment, "meta_description", 0, "The homepage has no meta description.")
        _finding(
            assessment,
            "meta_description",
            "low",
            "The homepage has no meta description",
            "Search results will then invent a snippet from the page text.",
            "Add a meta description of about 50–160 characters on the homepage.",
            [homepage.url],
        )

    total, missing = _alt_stats(pages)
    if total == 0:
        _add(assessment, "image_alt", 2, "No images to check.")
    else:
        present = total - len(missing)
        ratio = present / total
        if ratio >= 0.9:
            _add(assessment, "image_alt", 2, f"{present} of {total} images have an alt attribute.")
        elif ratio >= 0.5:
            _add(assessment, "image_alt", 1, f"{present} of {total} images have an alt attribute.")
            _finding(
                assessment,
                "image_alt",
                "low",
                "Some images have no alt text",
                _alt_detail(missing),
                "Add a short alt description to each informative image. Decorative images can use an empty alt.",
            )
        else:
            _add(assessment, "image_alt", 0, f"{present} of {total} images have an alt attribute.")
            _finding(
                assessment,
                "image_alt",
                "low",
                "Most images have no alt text",
                _alt_detail(missing),
                "Add a short alt description to each informative image. Decorative images can use an empty alt.",
            )

    if homepage.has_viewport:
        _add(assessment, "viewport", 1, "The homepage has a viewport tag.")
    else:
        _add(assessment, "viewport", 0, "The homepage has no viewport tag.")
        _finding(
            assessment,
            "viewport",
            "low",
            "The homepage has no viewport tag",
            "Without it, phones may show a zoomed-out desktop layout.",
            "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.",
            [homepage.url],
        )
    if homepage.canonical:
        _add(assessment, "canonical", 1, "The homepage has a canonical link.")
    else:
        _add(assessment, "canonical", 0, "The homepage has no canonical link.")
        _finding(
            assessment,
            "canonical",
            "low",
            "The homepage has no canonical link",
            "A canonical link tells search engines which URL is the main one when www, trailing slashes, or parameters vary.",
            "Add a canonical link on the homepage pointing at the preferred URL.",
            [homepage.url],
        )
    title_len = len(homepage.title)
    if TITLE_MIN <= title_len <= TITLE_MAX:
        _add(assessment, "title", 1, f"Homepage title is {title_len} characters.")
    else:
        _add(assessment, "title", 0, f"Homepage title is {title_len} characters.")
        _finding(
            assessment,
            "title",
            "low",
            "The homepage title length is outside the usual range",
            f"The title is {title_len} characters. This check looks for {TITLE_MIN}–{TITLE_MAX}.",
            "Rewrite the homepage title so it names the service and the area in about 15–60 characters.",
            [homepage.url],
        )
    if len(homepage.h1s) == 1:
        _add(assessment, "h1", 1, "The homepage has one H1.")
    else:
        _add(assessment, "h1", 0, f"The homepage has {len(homepage.h1s)} H1 headings.")
        _finding(
            assessment,
            "h1",
            "low",
            "The homepage H1 heading needs a look",
            "The homepage has no H1." if not homepage.h1s else f"The homepage has {len(homepage.h1s)} H1 headings.",
            "Use one H1 that says what the firm does.",
            [homepage.url],
        )
    if homepage.noindex:
        _add(assessment, "noindex", 0, "The homepage is marked noindex.")
        _finding(
            assessment,
            "noindex",
            "high",
            "The homepage is marked noindex",
            "A noindex robots tag asks search engines not to list the page.",
            "Remove noindex from the homepage unless the site is deliberately hidden.",
            [homepage.url],
        )
    else:
        _add(assessment, "noindex", 1, "The homepage is not marked noindex.")


def _links(assessment: Assessment) -> None:
    broken = []
    for error in assessment.errors:
        if error.get("kind") == "offsite":
            assessment.notes.append(error.get("error") or "A link redirected off-site.")
            continue
        status = error.get("status") or 0
        if status == 0 or status >= 400 or error.get("kind") in {"fetch", "parse"}:
            broken.append(error)
    if broken:
        points = min(6, 2 * len(broken))
        assessment.penalties.append(
            {
                "id": "broken_internal",
                "points": points,
                "detail": f"{len(broken)} internal page(s) could not be opened.",
            }
        )
        detail_bits = []
        for error in broken[:4]:
            sources = error.get("sources") or []
            source = f", linked from {sources[0]}" if sources else ""
            detail_bits.append(f"{error.get('url')} ({error.get('error') or error.get('status')}{source})")
        _finding(
            assessment,
            "broken_internal",
            "medium",
            "A broken internal link was found" if len(broken) == 1 else f"{len(broken)} broken internal links were found",
            "; ".join(detail_bits),
            "Fix or remove the links that do not open.",
            [error.get("url") for error in broken[:5] if error.get("url")],
        )

    external_broken = [
        item for item in assessment.external_links if item.get("classification") == "broken" and item.get("url")
    ]
    if external_broken:
        points = min(3, len(external_broken))
        assessment.penalties.append(
            {
                "id": "broken_external",
                "points": points,
                "detail": f"{len(external_broken)} external link(s) could not be opened.",
            }
        )
        bits = []
        for item in external_broken[:4]:
            sources = item.get("sources") or []
            source = f", linked from {sources[0]}" if sources else ""
            status = item.get("error") or item.get("status")
            bits.append(f"{item['url']} ({status}{source})")
        _finding(
            assessment,
            "broken_external",
            "low",
            "An external link could not be opened" if len(external_broken) == 1 else f"{len(external_broken)} external links could not be opened",
            "; ".join(bits),
            "Update or remove external links that return an error.",
            [item["url"] for item in external_broken[:5]],
        )
    uncertain = [item for item in assessment.external_links if item.get("classification") == "uncertain"]
    if uncertain:
        assessment.notes.append(
            f"{len(uncertain)} external link(s) returned 401, 403, or 429 and were not counted as broken."
        )
    skipped = [item for item in assessment.external_links if item.get("classification") == "skipped" and item.get("url")]
    if skipped:
        assessment.notes.append("External links were not requested on this run.")
    not_checked = [item for item in assessment.external_links if item.get("classification") == "not_checked"]
    for item in not_checked:
        if item.get("note"):
            assessment.notes.append(item["note"])


def _finish(assessment: Assessment) -> None:
    ids = [item["id"] for item in assessment.items]
    missing = [item_id for _category, item_id, _label, _maximum in RUBRIC if item_id not in ids]
    if missing:
        raise RuntimeError("Score items were not set: " + ", ".join(missing))
    if len(ids) != len(set(ids)):
        raise RuntimeError("A score item was recorded twice.")
    order = {item_id: index for index, (_category, item_id, _label, _maximum) in enumerate(RUBRIC)}
    assessment.items.sort(key=lambda item: order[item["id"]])
    base = sum(item["awarded"] for item in assessment.items)
    penalty = sum(item["points"] for item in assessment.penalties)
    assessment.score = max(0, min(100, base - penalty))
    rank = {"high": 0, "medium": 1, "low": 2}
    assessment.findings.sort(key=lambda item: rank.get(item["severity"], 9))


def _service_pages(pages: list[Page], trade: TradeProfile) -> list[Page]:
    found = []
    for page in pages:
        path = urlparse(page.url).path.lower()
        name = path.rstrip("/").rsplit("/", 1)[-1]
        name = re.sub(r"\.(html?|php|aspx)$", "", name)
        if not name or any(skip in name for skip in SKIP_SERVICE_NAMES):
            continue
        if any(pattern in name for pattern in trade.key_page_patterns):
            found.append(page)
    return found


def _has_privacy(pages: list[Page]) -> bool:
    for page in pages:
        if "privacy" in urlparse(page.url).path.lower():
            return True
        if "privacy policy" in page.text or "privacy notice" in page.text:
            return True
        for link in page.internal_links + page.external_links:
            if "privacy" in link.lower():
                return True
    return False


def _has_cookie(pages: list[Page]) -> bool:
    for page in pages:
        if "cookie" in urlparse(page.url).path.lower():
            return True
        if any(phrase in page.text for phrase in ("cookie policy", "cookie notice", "we use cookies", "cookie consent")):
            return True
        for link in page.internal_links + page.external_links:
            if "cookie" in link.lower():
                return True
    return False


def _alt_stats(pages: list[Page]) -> tuple[int, list[dict]]:
    total = 0
    missing = []
    for page in pages:
        for image in page.images:
            total += 1
            if not image.get("alt_present"):
                missing.append({"page": page.url, "src": image.get("src") or "(no src)"})
    return total, missing


def _alt_detail(missing: list[dict]) -> str:
    bits = []
    for image in missing[:5]:
        path = urlparse(image["page"]).path or "/"
        bits.append(f"{image['src']} on {path}")
    extra = len(missing) - len(bits)
    text = "; ".join(bits)
    if extra > 0:
        text += f"; and {extra} more"
    return text


def _unique(values) -> list[str]:
    found = []
    for value in values:
        if value and value not in found:
            found.append(value)
    return found


def find_ukas_numbers(text: str) -> list[str]:
    """A UKAS number sits just after 'UKAS', or immediately before it.

    The window is short so a company number earlier in the same sentence
    is not picked up. Years and ISO standard numbers are ignored.
    """
    found: list[str] = []
    labelled_re = re.compile(r"(?:accreditation\s+)?(?:number|no|num)\s*[:#]?\s*(\d{3,6})")
    for match in re.finditer(r"ukas", text or ""):
        after = text[match.end() : match.end() + 50]
        before = text[max(0, match.start() - 16) : match.start()]
        labelled = labelled_re.findall(after)
        bare_after = re.findall(r"\b(\d{4,5})\b", after)
        bare_before = re.findall(r"(\d{4,5})\s*$", before)
        candidates = labelled or bare_after or bare_before
        for number in candidates:
            if number in ISO_NUMBERS or 1990 <= int(number) <= 2035:
                continue
            if number not in found:
                found.append(number)
    return found


def find_company_numbers(text: str) -> list[str]:
    found: list[str] = []
    for match in COMPANY_CONTEXT.finditer(text or ""):
        window = text[max(0, match.start() - 16) : match.end() + 48]
        for number in COMPANY_NUMBER.findall(window):
            cleaned = re.sub(r"\s+", "", number).upper()
            if cleaned not in found:
                found.append(cleaned)
    return found


def find_vat_numbers(text: str) -> list[str]:
    found: list[str] = []
    for match in VAT_RE.finditer(text or ""):
        digits = re.sub(r"\s+", "", match.group(1))
        value = "GB" + digits
        if value not in found:
            found.append(value)
    return found


def _insurance_amount(text: str) -> bool:
    pattern = re.compile(
        r"public liability|professional indemnity|employers liability|pi cover|pl cover|pi insurance|pl insurance"
    )
    amount = re.compile(r"£\s?\d|\b\d+(?:\.\d+)?\s*million\b")
    for match in pattern.finditer(text or ""):
        window = text[max(0, match.start() - 50) : match.end() + 70]
        if amount.search(window):
            return True
    return False


def _node_types(node: dict) -> list[str]:
    raw = node.get("@type") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(item).lower() for item in raw]


def _is_strong_local(node: dict) -> bool:
    for name in _node_types(node):
        if name in {"organization", "organisation"}:
            continue
        if name in LOCAL_TYPES or name.endswith("business"):
            return True
    return False


def _best_local_node(pages: list[Page]) -> dict | None:
    strong = []
    weak = []
    for page in pages:
        for node in page.json_ld:
            if not isinstance(node, dict) or node.get("_parse_error"):
                continue
            if _is_strong_local(node):
                strong.append(node)
            elif any(name in {"organization", "organisation"} for name in _node_types(node)):
                if _field_address(node) or _field_phone(node):
                    weak.append(node)
    if strong:
        return strong[0]
    return weak[0] if weak else None


def _field_name(node: dict) -> bool:
    return bool(str(node.get("name") or "").strip())


def _field_phone(node: dict) -> bool:
    phone = node.get("telephone") or node.get("phone") or ""
    if isinstance(phone, list):
        phone = " ".join(str(item) for item in phone)
    return bool(str(phone).strip())


def _field_address(node: dict) -> bool:
    address = node.get("address")
    if isinstance(address, str):
        return bool(address.strip())
    if isinstance(address, dict):
        return bool(address.get("streetAddress") or address.get("postalCode") or address.get("addressLocality"))
    return False


def _field_area(node: dict) -> bool:
    area = node.get("areaServed")
    if isinstance(area, list):
        return len(area) > 0
    if isinstance(area, dict):
        return bool(area)
    return bool(str(area or "").strip())
