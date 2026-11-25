import time
from urllib.parse import urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests

from page import Page, normalise_host

USER_AGENT = "AsbestosAuditBot/1.0"

# Links to these file types are not crawled (they are not HTML pages).
SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".zip", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".mov", ".avi", ".css", ".js", ".xml", ".json",
)


def normalise_url(url):
    """Drop the fragment and any trailing slash on the path (except the root)."""
    url, _ = urldefrag(url)
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    return parsed._replace(path=path).geturl()


class Website:
    def __init__(self, start_url, max_pages=20, delay=0.5, respect_robots=True):
        self.start_url = normalise_url(start_url)
        self.base_domain = normalise_host(urlparse(start_url).netloc)
        self.max_pages = max_pages
        self.delay = delay
        self.respect_robots = respect_robots

        self.crawled = {}      # url -> Page or {"error": ...}
        self.to_crawl = [self.start_url]
        self.linked_from = {}  # url -> set of pages that link to it
        self.skipped = []      # (url, reason) for things deliberately not crawled

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.robots = self._load_robots() if respect_robots else None

    def _load_robots(self):
        parsed = urlparse(self.start_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        try:
            resp = self.session.get(robots_url, timeout=10)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                return rp
        except requests.RequestException:
            pass
        return None  # no usable robots.txt: allow everything

    def _allowed(self, url):
        return self.robots is None or self.robots.can_fetch(USER_AGENT, url)

    def _should_skip(self, url):
        path = urlparse(url).path.lower()
        return path.endswith(SKIP_EXTENSIONS)

    def crawl(self):
        first = True
        while self.to_crawl and len(self.crawled) < self.max_pages:
            url = self.to_crawl.pop(0)
            if url in self.crawled:
                continue

            if self._should_skip(url):
                self.skipped.append((url, "not an HTML page"))
                continue
            if not self._allowed(url):
                self.skipped.append((url, "disallowed by robots.txt"))
                continue

            if not first and self.delay:
                time.sleep(self.delay)
            first = False

            try:
                resp = self.session.get(url, timeout=10)
            except Exception as e:
                self.crawled[url] = {"error": str(e)}
                continue

            if resp.status_code != 200:
                self.crawled[url] = {"error": f"HTTP {resp.status_code}"}
                continue

            final_host = normalise_host(urlparse(resp.url).netloc)
            if final_host != self.base_domain:
                self.crawled[url] = {"error": f"Redirects off-site to {resp.url}"}
                continue

            content_type = resp.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                self.skipped.append((url, f"content type {content_type or 'unknown'}"))
                continue

            page = Page(resp.url, self.base_domain)
            page.analyze(resp.text)
            self.crawled[url] = page

            for link in page.links:
                link = normalise_url(link)
                self.linked_from.setdefault(link, set()).add(url)
                if link not in self.crawled and link not in self.to_crawl:
                    self.to_crawl.append(link)

        return self.crawled
