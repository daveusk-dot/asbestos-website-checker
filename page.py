import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from niche import Niche


def normalise_host(netloc):
    """Treat www.example.com and example.com as the same site."""
    host = netloc.lower()
    return host[4:] if host.startswith("www.") else host


# UK phone numbers: 0800 123 4567, 01902 123456, 0121 123 4567, +44 (0)121 123 4567 ...
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+44[\s-]?\(?0?\)?[\s-]?|0)\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}(?!\d)"
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
POSTCODE_RE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b")

LOCAL_SCHEMA_TYPES = ("LocalBusiness", "Organization", "ProfessionalService", "HomeAndConstructionBusiness")


def _has_word(text, phrase):
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


class Page:
    def __init__(self, url, base_domain, niche=None):
        self.url = url
        self.base_domain = normalise_host(base_domain)
        self.niche = niche or Niche()
        # list of {"code", "message"} plus optional "headline"/"advice" for niche-specific checks
        self.issues = []
        self.links = []
        self.title = ""
        self.meta_description = ""
        self.text = ""
        self.word_count = 0
        self.has_phone = False
        self.has_email = False
        self.has_postcode = False
        self.has_local_schema = False

    @property
    def warnings(self):
        """Plain-text warnings (kept for backwards compatibility)."""
        return [i["message"] for i in self.issues]

    def _warn(self, code, message, headline=None, advice=None):
        issue = {"code": code, "message": message}
        if headline:
            issue["headline"] = headline
        if advice:
            issue["advice"] = advice
        self.issues.append(issue)

    def analyze(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # Collect data we need before stripping non-visible content
        json_ld_blocks = [s.get_text() for s in soup.find_all("script", type="application/ld+json")]
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        self.title = soup.title.get_text(strip=True) if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        self.meta_description = (meta_desc.get("content") or "").strip() if meta_desc else ""

        raw_text = soup.get_text(separator=" ", strip=True)
        self.text = raw_text.lower()
        match_text = self.text.replace("-", " ")
        self.word_count = len(raw_text.split())

        # --- Links ---------------------------------------------------------
        hrefs = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            hrefs.append((href, a.get_text(" ", strip=True).lower()))
            full = urljoin(self.url, href)
            parsed = urlparse(full)
            if normalise_host(parsed.netloc) == self.base_domain and parsed.scheme in ("http", "https"):
                clean = full.split("#")[0]
                if clean not in self.links:
                    self.links.append(clean)

        th = self.niche.thresholds

        # --- Title / meta description / headings ----------------------------
        if not self.title:
            self._warn("title_missing", "Missing title")
        elif len(self.title) < th.title_min or len(self.title) > th.title_max:
            self._warn("title_length", f"Title length issue ({len(self.title)} chars): {self.title}")

        if not self.meta_description:
            self._warn("meta_description_missing", "Missing meta description")
        elif len(self.meta_description) < th.description_min or len(self.meta_description) > th.description_max:
            self._warn(
                "meta_description_length",
                f"Meta description length issue ({len(self.meta_description)} chars, "
                f"aim for {th.description_min}-{th.description_max})",
            )

        h1s = soup.find_all("h1")
        if len(h1s) == 0:
            self._warn("h1_missing", "Missing H1 heading")
        elif len(h1s) > 1:
            self._warn("h1_multiple", f"Multiple H1 headings ({len(h1s)})")

        # --- Technical basics ---------------------------------------------
        if not soup.find("meta", attrs={"name": "viewport"}):
            self._warn("viewport_missing", "Missing viewport meta tag (mobile rendering risk)")
        if not soup.find("link", attrs={"rel": "canonical"}):
            self._warn("canonical_missing", "Missing canonical tag")

        imgs = soup.find_all("img")
        missing_alt = [i for i in imgs if i.get("alt") is None]
        if missing_alt:
            self._warn("images_no_alt", f"{len(missing_alt)} of {len(imgs)} images have no alt attribute")

        if self.word_count < th.thin_content_words:
            self._warn("thin_content", f"Thin content ({self.word_count} words)")

        # --- Contact signals ---------------------------------------------
        # Phone/email links live in href attributes, not in the visible text.
        self.has_phone = any(h.lower().startswith("tel:") for h, _ in hrefs) or bool(PHONE_RE.search(raw_text))
        self.has_email = any(h.lower().startswith("mailto:") for h, _ in hrefs) or bool(EMAIL_RE.search(raw_text))
        has_contact_link = any("contact" in h.lower() or "contact" in label for h, label in hrefs)
        self.has_postcode = bool(POSTCODE_RE.search(raw_text))

        if not (self.has_phone or self.has_email):
            if has_contact_link or "get in touch" in self.text:
                self._warn("no_direct_contact", "No phone number or email shown (only a link to a contact page)")
            else:
                self._warn("no_contact", "No obvious contact details found")

        # --- Niche-specific checks (all driven by niches/<name>.yaml) --------
        tm = self.niche.trust_marks
        if tm:
            has_strong = any(_has_word(match_text, t) for t in tm.strong)
            has_any = has_strong or any(_has_word(match_text, t) for t in tm.weak)
            if not has_any:
                self._warn(
                    "no_accreditation",
                    f"No {tm.label} or trust mark mentioned",
                    headline=f"No {tm.label} or trust marks shown",
                    advice=tm.advice_missing,
                )
            elif not has_strong and tm.strong:
                self._warn(
                    "weak_accreditation",
                    f"{tm.label.capitalize()} mentioned but wording is weak",
                    headline=f"{tm.label.capitalize()} wording is weak",
                    advice=tm.advice_weak,
                )

        for rm in self.niche.required_mentions:
            if not any(_has_word(match_text, t) for t in rm.terms):
                self._warn(
                    f"no_{rm.id}",
                    f"No mention of: {rm.label}",
                    headline=f"{rm.label} not mentioned",
                    advice=rm.advice,
                )

        for c in self.niche.conflicts:
            if any(t in match_text for t in c.a) and any(t in match_text for t in c.b):
                self._warn(f"conflict_{c.id}", c.message, headline=c.label, advice=c.advice)

        # --- Structured data -----------------------------------------------
        for block in json_ld_blocks:
            try:
                data = json.loads(block)
            except ValueError:
                continue
            if any(t in json.dumps(data) for t in LOCAL_SCHEMA_TYPES):
                self.has_local_schema = True
                break

        # --- Contact page form ----------------------------------------------
        if "contact" in urlparse(self.url).path.lower():
            forms = soup.find_all("form")
            if not forms:
                self._warn("contact_no_form", "Contact page has no form")
            for form in forms:
                action = (form.get("action") or "").strip()
                if not action or action == "#":
                    self._warn("form_no_action", "Contact form has no clear action/destination")
                inputs = form.find_all(["input", "textarea"])
                wanted = ["name", "email", "message", "phone"]
                found = [
                    f for f in wanted
                    if any(f in (i.get("name") or "").lower() or f in (i.get("placeholder") or "").lower()
                           for i in inputs)
                ]
                if len(found) < 2:
                    self._warn("form_missing_fields", "Contact form missing key fields (name/email/message/phone)")

    def as_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "meta_description": self.meta_description,
            "word_count": self.word_count,
            "warnings": self.warnings,
            "issues": self.issues,
            "link_count": len(self.links),
            "signals": {
                "phone": self.has_phone,
                "email": self.has_email,
                "postcode": self.has_postcode,
                "local_business_schema": self.has_local_schema,
            },
        }
