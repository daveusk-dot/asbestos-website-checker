from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests

class Page:
    def __init__(self, url, base_domain):
        self.url = url
        self.base_domain = base_domain
        self.warnings = []
        self.links = []
        self.title = ""
        self.text = ""

    def analyze(self, html):
        soup = BeautifulSoup(html, "html.parser")
        self.title = soup.title.string.strip() if soup.title else ""
        self.text = soup.get_text(separator=" ", strip=True).lower()

        # Basic checks
        if not self.title:
            self.warnings.append("Missing title")
        elif len(self.title) < 10 or len(self.title) > 70:
            self.warnings.append(f"Title length issue ({len(self.title)} chars): {self.title}")

        # Extract internal links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(self.url, href)
            parsed = urlparse(full)
            if parsed.netloc == self.base_domain and parsed.scheme in ("http", "https"):
                clean = full.split("#")[0]
                if clean not in self.links:
                    self.links.append(clean)

        # Niche checks (asbestos example)
        if "asbestos removal" in self.text and ("survey only" in self.text or "surveys only" in self.text):
            self.warnings.append("Possible conflicting service wording (removal vs survey only)")

        # Contact signals
        has_phone = any(x in self.text for x in ["tel:", "phone", "call us", "mobile", "0800", "0121", "01902"])
        has_email = "email" in self.text or "@" in self.text
        has_contact_page = "contact" in self.text or "get in touch" in self.text
        if not (has_phone or has_email or has_contact_page):
            self.warnings.append("No obvious contact details found")

        # More specific accreditation wording
        strong_accreds = ["ukas accredited", "ukas laboratory", "arca member", "bohs certified", "licensed asbestos"]
        weak_accreds = ["ukas", "arca", "bohs", "iosh", "chas", "safecontractor"]
        has_strong = any(a in self.text for a in strong_accreds)
        has_weak = any(a in self.text for a in weak_accreds)
        if not has_weak:
            self.warnings.append("No accreditation or trust mark mentioned (UKAS, ARCA, BOHS, etc.)")
        elif not has_strong:
            self.warnings.append("Accreditation mentioned but wording is weak (prefer 'UKAS accredited' or 'ARCA member')")

        # Forms – basic presence and action check
        forms = soup.find_all("form")
        if "contact" in self.url.lower():
            if not forms:
                self.warnings.append("Contact page has no form")
            else:
                for form in forms:
                    action = form.get("action", "")
                    method = form.get("method", "").lower()
                    if not action or action == "#":
                        self.warnings.append("Contact form has no clear action/destination")
                    inputs = form.find_all(["input", "textarea"])
                    required_fields = ["name", "email", "message", "phone"]
                    found = [f for f in required_fields if any(f in (i.get("name") or "").lower() or f in (i.get("placeholder") or "").lower() for i in inputs)]
                    if len(found) < 2:
                        self.warnings.append("Contact form missing key fields (name/email/message/phone)")

        # Insurance / compliance
        if "insurance" not in self.text and "public liability" not in self.text and "indemnity" not in self.text:
            self.warnings.append("No mention of insurance or public liability")

        # H1 check
        h1s = soup.find_all("h1")
        if len(h1s) == 0:
            self.warnings.append("Missing H1 heading")
        elif len(h1s) > 1:
            self.warnings.append(f"Multiple H1 headings ({len(h1s)})")

        # Viewport / basic mobile signal
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            self.warnings.append("Missing viewport meta tag (mobile rendering risk)")

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if not canonical:
            self.warnings.append("Missing canonical tag")

    def as_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "warnings": self.warnings,
            "link_count": len(self.links)
        }
