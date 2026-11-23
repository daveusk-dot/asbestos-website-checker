"""URL, phone, email, and postcode normalisation.

www and non-www are the same site. Fragments, trailing slashes, and
tracking query parameters are ignored when deciding whether a URL has
already been seen. Phone handling is aimed at UK numbers rather than a
short list of area codes.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_name",
    "fbclid",
    "gclid",
    "gclsrc",
    "dclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "yclid",
    "igshid",
    "_ga",
    "_gl",
    "_hsenc",
    "_hsmi",
    "mkt_tok",
}

NON_HTML_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".mjs",
    ".map",
    ".zip",
    ".rar",
    ".7z",
    ".gz",
    ".mp4",
    ".mp3",
    ".wav",
    ".webm",
    ".mov",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".csv",
    ".xml",
    ".json",
    ".txt",
    ".rtf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

# National numbers are usually 10 or 11 digits once the leading 0 is included.
# The pattern is intentionally a candidate finder; normalize_phone() decides.
PHONE_CANDIDATE = re.compile(
    r"""
    (?<!\w)
    (?:
        (?:\+|00)\s*44[\s().-]*(?:\(0\)[\s().-]*)?[1-9](?:[\s().-]*\d){8,12}
        |
        \(0\d{2,5}\)(?:[\s().-]*\d){5,10}
        |
        0[1-9](?:[\s().-]*\d){8,12}
    )
    (?!\w)
    """,
    re.VERBOSE,
)

EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Z0-9][A-Z0-9._%+\-]{0,63}@"
    r"[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?)+"
    r"(?![\w-])",
    re.IGNORECASE,
)

POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",
    re.IGNORECASE,
)

# Template addresses that show up on unfinished sites. Reserved .example
# addresses are allowed so fixture sites can carry a made-up inbox.
PLACEHOLDER_EMAILS = {
    "info@website.com",
    "email@example.com",
    "user@domain.com",
    "name@email.com",
    "test@test.com",
}
PLACEHOLDER_EMAIL_DOMAINS = {
    "website.com",
    "domain.com",
    "email.com",
    "yourdomain.com",
    "yoursite.com",
    "company.com",
    "example.com",
    "example.org",
    "example.net",
}

FAKE_PHONES = {
    "01234567890",
    "0123456789",
    "07123456789",
    "07000000000",
    "0800000000",
    "08000000000",
    "00000000000",
    "01111111111",
}


def ensure_scheme(url: str) -> str:
    value = (url or "").strip()
    if not value:
        raise ValueError("URL is empty.")
    if not re.match(r"https?://", value, re.IGNORECASE):
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Only http and https URLs can be audited (got {parsed.scheme}).")
    if not parsed.hostname or " " in parsed.netloc:
        raise ValueError(f"URL has no host: {url}")
    return value


def hostname_and_port(netloc: str) -> tuple[str, int | None]:
    parsed = urlparse("//" + (netloc or ""))
    host = (parsed.hostname or "").lower().rstrip(".")
    return host, parsed.port


def host_key(netloc: str) -> str:
    """Identity of a site. The www prefix is ignored; unusual ports are not."""
    host, port = hostname_and_port(netloc)
    if host.startswith("www."):
        host = host[4:]
    if port and port not in (80, 443):
        return f"{host}:{port}"
    return host


def _clean_path(path: str) -> str:
    path = re.sub(r"/{2,}", "/", path or "/")
    if not path.startswith("/"):
        path = "/" + path
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path


def _clean_query(query: str) -> str:
    pairs = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    pairs.sort()
    return urlencode(pairs)


def dedup_key(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    return (host_key(parsed.netloc), _clean_path(parsed.path), _clean_query(parsed.query))


def canonical_origin(url: str) -> tuple[str, str]:
    """Scheme and netloc to reuse after the first response, www included."""
    parsed = urlparse(url)
    host, port = hostname_and_port(parsed.netloc)
    if port and not (
        (parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host
    return parsed.scheme or "https", netloc


def rewrite_url(url: str, *, scheme: str, netloc: str) -> str:
    parsed = urlparse(url)
    return urlunparse((scheme, netloc, _clean_path(parsed.path), "", _clean_query(parsed.query), ""))


def strip_fragment(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment=""))


def normalize_link(href: str, base: str) -> str | None:
    if not href:
        return None
    raw = href.strip()
    lowered = raw.lower()
    if lowered.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
        return None
    absolute = urljoin(base, raw)
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc, _clean_path(parsed.path), "", _clean_query(parsed.query), "")
    )


def is_non_html_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in NON_HTML_EXTENSIONS)


def same_site(url: str, canonical_host: str) -> bool:
    return host_key(urlparse(url).netloc) == canonical_host


def normalize_phone(raw: str) -> str | None:
    """Return an 11-digit national UK number, or a 10-digit 0800/0808 number."""
    if not raw:
        return None
    text = unquote(raw).strip()
    text = text.split("?", 1)[0].split(";", 1)[0]
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    international = text.lstrip().startswith("+") or text.lstrip().startswith("00")
    if digits.startswith("00"):
        digits = digits[2:]
        international = True
    if digits.startswith("44") and (international or len(digits) >= 12):
        rest = digits[2:]
        digits = rest if rest.startswith("0") else "0" + rest
    if not digits.startswith("0"):
        return None
    if digits[1] not in "123578":
        return None
    if len(digits) == 10 and not digits.startswith(("0800", "0808")):
        return None
    if len(digits) not in (10, 11):
        return None
    if digits in FAKE_PHONES or len(set(digits)) == 1:
        return None
    return digits


def phones_in_text(text: str) -> list[str]:
    found: list[str] = []
    for match in PHONE_CANDIDATE.finditer(text or ""):
        number = normalize_phone(match.group(0))
        if number and number not in found:
            found.append(number)
    return found


def phone_from_tel(href: str) -> str | None:
    if not href:
        return None
    value = href.strip()
    if value.lower().startswith("tel:"):
        value = value[4:]
    return normalize_phone(value)


def format_phone(digits: str) -> str:
    if len(digits) == 10 and digits.startswith("0800"):
        return f"{digits[:4]} {digits[4:]}"
    if len(digits) != 11:
        return digits
    if digits.startswith("02"):
        return f"{digits[:3]} {digits[3:7]} {digits[7:]}"
    if digits.startswith(("07", "08", "03", "05")):
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    if digits.startswith("01") and (digits[2] == "1" or digits[3] == "1"):
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    if digits.startswith("01"):
        return f"{digits[:5]} {digits[5:]}"
    return digits


def usable_email(email: str) -> bool:
    if not email or email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    if not local or "." not in domain or ".." in email:
        return False
    if email in PLACEHOLDER_EMAILS or domain in PLACEHOLDER_EMAIL_DOMAINS:
        return False
    if domain.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")):
        return False
    return True


def emails_in_text(text: str) -> list[str]:
    found: list[str] = []
    for match in EMAIL_RE.finditer(text or ""):
        email = match.group(0).strip(".").lower()
        if usable_email(email) and email not in found:
            found.append(email)
    return found


def email_from_mailto(href: str) -> str | None:
    if not href or not href.lower().startswith("mailto:"):
        return None
    value = unquote(href[7:]).split("?", 1)[0].strip().lower()
    if usable_email(value):
        return value
    return None


def format_postcode(value: str) -> str | None:
    compact = re.sub(r"\s+", "", value or "").upper()
    if not 5 <= len(compact) <= 7:
        return None
    return f"{compact[:-3]} {compact[-3:]}"


def postcodes_in_text(text: str) -> list[str]:
    found: list[str] = []
    for match in POSTCODE_RE.finditer(text or ""):
        code = format_postcode(match.group(1))
        if code and code not in found:
            found.append(code)
    return found


def normalize_name(name: str) -> str:
    value = (name or "").lower().replace("&", " and ").replace("’", "'")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\b(ltd|limited|llp|plc|uk|the|co|company)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def names_compatible(left: str, right: str) -> bool:
    a = normalize_name(left).split()
    b = normalize_name(right).split()
    if not a or not b:
        return True
    if len(a) <= len(b) and b[: len(a)] == a:
        return True
    if len(b) <= len(a) and a[: len(b)] == b:
        return True
    return False


def names_conflict(names: list[str]) -> bool:
    """True when two extracted names do not look like the same business."""
    kept: list[str] = []
    for name in names:
        core = normalize_name(name)
        if len(core) < 4:
            continue
        if any(names_compatible(core, existing) for existing in kept):
            continue
        kept.append(core)
    return len(kept) > 1
