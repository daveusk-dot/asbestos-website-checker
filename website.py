import requests
from urllib.parse import urlparse
from page import Page

class Website:
    def __init__(self, start_url, max_pages=20):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.max_pages = max_pages
        self.crawled = {}
        self.to_crawl = [start_url]

    def crawl(self):
        while self.to_crawl and len(self.crawled) < self.max_pages:
            url = self.to_crawl.pop(0)
            if url in self.crawled:
                continue

            try:
                resp = requests.get(url, timeout=10, headers={"User-Agent": "AsbestosAuditBot/1.0"})
                if resp.status_code != 200:
                    self.crawled[url] = {"error": f"HTTP {resp.status_code}"}
                    continue

                page = Page(url, self.base_domain)
                page.analyze(resp.text)
                self.crawled[url] = page

                for link in page.links:
                    if link not in self.crawled and link not in self.to_crawl:
                        self.to_crawl.append(link)
            except Exception as e:
                self.crawled[url] = {"error": str(e)}

        return self.crawled
