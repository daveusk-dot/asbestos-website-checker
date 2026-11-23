"""Polite crawler for a small trade site.

The first response picks the host to stay on, so a redirect between www
and the bare host is followed and later links use that host. robots.txt
is fetched once per origin and honoured. Non-HTML responses are recorded
and not parsed.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from fetch import DEFAULT_TIMEOUT, FetchResult, build_user_agent
from normalize import (
    canonical_origin,
    dedup_key,
    ensure_scheme,
    host_key,
    is_non_html_extension,
    rewrite_url,
    same_site,
    strip_fragment,
)
from page import Page, parse_page

MAX_CRAWL_DELAY = 5.0


def effective_delay(user_delay: float, crawl_delay: float | None) -> float:
    base = max(0.0, float(user_delay or 0))
    if crawl_delay is None:
        return base
    try:
        parsed = float(crawl_delay)
    except (TypeError, ValueError):
        return base
    if parsed < 0:
        return base
    return min(MAX_CRAWL_DELAY, max(base, parsed))


def looks_like_html(content_type: str, content: bytes, text: str) -> bool:
    sample = content[:800] if content else (text or "")[:800].encode("utf-8", errors="ignore")
    sample = sample.lstrip().lower()
    if sample.startswith((b"%pdf", b"\x89png", b"\xff\xd8\xff", b"gif8", b"pk\x03\x04")):
        return False
    ctype = (content_type or "").lower().split(";", 1)[0].strip()
    if ctype in {"text/html", "application/xhtml+xml"}:
        return True
    if ctype and ctype not in {"text/plain", "application/octet-stream"}:
        return False
    return (
        sample.startswith(b"<!doctype html")
        or sample.startswith(b"<html")
        or b"<head" in sample
        or b"<title" in sample
        or b"<body" in sample
    )


def classify_status(status: int, error: str | None) -> str:
    if error or not status:
        return "broken"
    if 200 <= status < 400:
        return "ok"
    if status in {401, 403, 429}:
        return "uncertain"
    if status >= 400:
        return "broken"
    return "uncertain"


@dataclass
class CrawlResult:
    start_url: str
    final_url: str
    pages: list[Page] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    external_links: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    user_agent: str = ""
    homepage: Page | None = None


class Website:
    def __init__(
        self,
        start_url: str,
        max_pages: int = 15,
        delay: float = 0.5,
        fetcher=None,
        user_agent: str | None = None,
        check_external: bool = True,
        max_external: int = 40,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.start_url = ensure_scheme(start_url)
        self.max_pages = max(1, int(max_pages))
        self.delay = max(0.0, float(delay))
        self.fetcher = fetcher
        self.user_agent = user_agent or build_user_agent()
        self.check_external = check_external
        self.max_external = max(0, int(max_external))
        self.timeout = timeout
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        }
        self.scheme: str | None = None
        self.netloc: str | None = None
        self.host: str | None = None
        self._crawl_delay: float | None = None
        self._requests_made = 0
        self._robots: dict[str, RobotFileParser] = {}
        self.sources: dict[tuple, set[str]] = defaultdict(set)

    def crawl(self) -> CrawlResult:
        if self.fetcher is None:
            from fetch import requests_fetcher

            self.fetcher = requests_fetcher
        queue = [strip_fragment(self.start_url)]
        seen: set[tuple] = set()
        pages: list[Page] = []
        errors: list[dict] = []
        skipped: list[dict] = []
        external: dict[str, set[str]] = defaultdict(set)
        notes: list[str] = []
        fetched = 0
        final_url = self.start_url

        while queue and fetched < self.max_pages:
            raw = queue.pop(0)
            url = self._rewrite(raw) if self.scheme else strip_fragment(raw)
            key = dedup_key(url)
            if key in seen:
                continue
            if is_non_html_extension(url):
                seen.add(key)
                skipped.append(self._skip(url, "non-html extension", key))
                continue
            if not self._allowed(url):
                seen.add(key)
                skipped.append(self._skip(url, "robots.txt", key))
                continue
            seen.add(key)
            self._pause()
            fetched += 1
            result = self._fetch(url, read_body=True)
            source_list = sorted(self.sources.get(key, ()))
            if result.error or result.status_code == 0 or result.status_code >= 400:
                errors.append(
                    {
                        "url": url,
                        "status": result.status_code or None,
                        "error": result.error or f"HTTP {result.status_code}",
                        "sources": source_list,
                        "kind": "fetch",
                    }
                )
                continue
            final = result.url or url
            if self.scheme is None:
                self.scheme, self.netloc = canonical_origin(final)
                self.host = host_key(self.netloc)
                final_url = self._rewrite(final)
                seen.add(dedup_key(final_url))
                start_host = host_key(urlparse(self.start_url).netloc)
                if start_host != self.host or urlparse(self.start_url).scheme != self.scheme:
                    notes.append(f"The start URL redirected to {final_url}.")
            elif host_key(urlparse(final).netloc) != self.host:
                errors.append(
                    {
                        "url": url,
                        "status": result.status_code,
                        "error": f"Redirected off-site to {final}",
                        "sources": source_list,
                        "kind": "offsite",
                    }
                )
                continue
            else:
                final_url = final_url or self._rewrite(final)
            page_url = self._rewrite(final)
            if not looks_like_html(result.content_type, result.content, result.text):
                skipped.append(
                    {
                        "url": page_url,
                        "reason": "non-html response",
                        "content_type": result.content_type,
                        "sources": source_list,
                    }
                )
                continue
            try:
                page = parse_page(page_url, result.text, headers=result.headers)
            except Exception as exc:
                errors.append(
                    {
                        "url": page_url,
                        "status": result.status_code,
                        "error": f"Could not parse page: {exc}",
                        "sources": source_list,
                        "kind": "parse",
                    }
                )
                continue
            pages.append(page)
            for link in page.internal_links:
                if not same_site(link, self.host or ""):
                    external[link].add(page.url)
                    continue
                rewritten = self._rewrite(link)
                link_key = dedup_key(rewritten)
                self.sources[link_key].add(page.url)
                if link_key not in seen and rewritten not in queue:
                    queue.append(rewritten)
            for link in page.external_links:
                external[link].add(page.url)

        external_links = self._check_external(external)
        homepage = self._homepage(pages, final_url)
        return CrawlResult(
            start_url=self.start_url,
            final_url=final_url if pages else self.start_url,
            pages=pages,
            errors=errors,
            skipped=skipped,
            external_links=external_links,
            notes=notes,
            user_agent=self.user_agent,
            homepage=homepage,
        )

    def _homepage(self, pages: list[Page], final_url: str) -> Page | None:
        if not pages:
            return None
        wanted = dedup_key(final_url)
        for page in pages:
            if dedup_key(page.url) == wanted:
                return page
        return pages[0]

    def _rewrite(self, url: str) -> str:
        if not self.scheme or not self.netloc:
            return strip_fragment(url)
        return rewrite_url(url, scheme=self.scheme, netloc=self.netloc)

    def _skip(self, url: str, reason: str, key: tuple) -> dict:
        return {"url": url, "reason": reason, "sources": sorted(self.sources.get(key, ()))}

    def _pause(self) -> None:
        if self._requests_made == 0:
            self._requests_made += 1
            return
        self._requests_made += 1
        delay = effective_delay(self.delay, self._crawl_delay)
        if delay:
            time.sleep(delay)

    def _fetch(self, url: str, *, read_body: bool) -> FetchResult:
        try:
            result = self.fetcher(
                url,
                headers=self.headers,
                timeout=self.timeout,
                read_body=read_body,
            )
        except TypeError:
            try:
                result = self.fetcher(url, headers=self.headers, timeout=self.timeout)
            except Exception as exc:
                return FetchResult(url=url, status_code=0, text="", headers={}, error=str(exc))
        except Exception as exc:
            return FetchResult(url=url, status_code=0, text="", headers={}, error=str(exc))
        if not isinstance(result, FetchResult):
            return FetchResult(url=url, status_code=0, text="", headers={}, error="Fetcher returned an unexpected result.")
        return result

    def _allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots.get(origin)
        if parser is None:
            parser = self._load_robots(origin)
            self._robots[origin] = parser
        return parser.can_fetch(self.user_agent, url)

    def _load_robots(self, origin: str) -> RobotFileParser:
        robots_url = origin.rstrip("/") + "/robots.txt"
        self._pause()
        result = self._fetch(robots_url, read_body=True)
        text = ""
        if not result.error and result.status_code == 200:
            sample = (result.text or "")[:600].lower()
            if "html" not in result.content_type.lower() and "<html" not in sample:
                text = result.text or ""
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(text.splitlines())
        delay = parser.crawl_delay(self.user_agent)
        if delay is None:
            delay = parser.crawl_delay("*")
        if delay is not None:
            self._crawl_delay = float(delay)
        return parser

    def _check_external(self, external: dict[str, set[str]]) -> list[dict]:
        checked = []
        items = list(external.items())
        extra = 0
        if len(items) > self.max_external:
            extra = len(items) - self.max_external
            items = items[: self.max_external]
        for url, sources in items:
            if not self.check_external:
                checked.append(
                    {
                        "url": url,
                        "status": None,
                        "error": None,
                        "classification": "skipped",
                        "sources": sorted(sources),
                    }
                )
                continue
            self._pause()
            result = self._fetch(url, read_body=False)
            checked.append(
                {
                    "url": url,
                    "status": result.status_code or None,
                    "final_url": result.url,
                    "error": result.error,
                    "classification": classify_status(result.status_code, result.error),
                    "sources": sorted(sources),
                }
            )
        if extra:
            checked.append(
                {
                    "url": "",
                    "status": None,
                    "error": None,
                    "classification": "not_checked",
                    "sources": [],
                    "note": f"{extra} further external links were not checked.",
                }
            )
        return checked
