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
        if "asbestos removal" in self.text and "survey only" in self.text:
            self.warnings.append("Possible conflicting service wording (removal vs survey only)")
        if "contact" not in self.text and "phone" not in self.text and "email" not in self.text:
            self.warnings.append("No obvious contact details found")

    def as_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "warnings": self.warnings,
            "link_count": len(self.links)
        }
