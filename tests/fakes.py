"""In-memory HTTP stand-in for crawler tests. Nothing here touches the network."""

from __future__ import annotations

from urllib.parse import urlparse

from fetch import FetchResult

EMPTY_ROBOTS = "User-agent: *\nDisallow:\n"


class MapFetcher:
    def __init__(self, pages: dict, robots: str = EMPTY_ROBOTS):
        self.pages = pages
        self.robots = robots
        self.urls: list[str] = []
        self.headers: dict | None = None

    def __call__(self, url, headers=None, timeout=None, read_body=True):
        self.urls.append(url)
        self.headers = headers
        parsed = urlparse(url)
        path = parsed.path or "/"
        host = parsed.hostname or ""
        if host == "www.googleapis.com" and "pagespeed" in self.pages:
            body = self.pages["pagespeed"]
            return _html_result(url, body, "application/json")
        if path == "/robots.txt" and (host, path) not in self.pages and path not in self.pages:
            return _html_result(url, self.robots, "text/plain")
        body = self.pages.get((host, path), self.pages.get(path))
        if body is None:
            return FetchResult(
                url=url,
                status_code=404,
                text="missing",
                headers={"content-type": "text/html"},
                content=b"missing",
            )
        if isinstance(body, FetchResult):
            return body
        if isinstance(body, tuple):
            status, text, content_type = body
            encoded = text.encode() if isinstance(text, str) else text
            return FetchResult(
                url=url,
                status_code=status,
                text=text if isinstance(text, str) else "",
                headers={"content-type": content_type},
                content=encoded,
            )
        return _html_result(url, body, "text/html")


def _html_result(url: str, body: str, content_type: str) -> FetchResult:
    return FetchResult(
        url=url,
        status_code=200,
        text=body,
        headers={"content-type": content_type},
        content=body.encode(),
    )


def html_page(body: str, title: str = "Harbour Asbestos Surveys in Birmingham", head: str = "") -> str:
    return (
        "<!DOCTYPE html><html><head>"
        f"<title>{title}</title>{head}"
        "</head><body>"
        f"{body}</body></html>"
    )
