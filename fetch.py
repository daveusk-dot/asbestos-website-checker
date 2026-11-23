"""HTTP helper and the user agent string.

Tests inject their own fetcher. The real one is used only from the CLI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

PROJECT_URL = "https://github.com/daveusk-dot/asbestos-website-checker"
USER_AGENT_BASE = f"AsbestosWebsiteChecker/1.0 (+{PROJECT_URL})"
DEFAULT_TIMEOUT = 15


def build_user_agent() -> str:
    """Identify the crawler and, when AUDIT_CONTACT is set, who is running it."""
    contact = os.environ.get("AUDIT_CONTACT", "").strip()
    if contact:
        return f"{USER_AGENT_BASE}; contact: {contact}"
    return USER_AGENT_BASE


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]
    content: bytes = b""
    error: str | None = None

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")


def requests_fetcher(
    url: str,
    *,
    headers: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    read_body: bool = True,
) -> FetchResult:
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
    except requests.RequestException as exc:
        return FetchResult(url=url, status_code=0, text="", headers={}, content=b"", error=str(exc))
    try:
        raw_headers = {key.lower(): value for key, value in response.headers.items()}
        if not read_body:
            return FetchResult(
                url=response.url,
                status_code=response.status_code,
                text="",
                headers=raw_headers,
                content=b"",
            )
        content = response.content
        encoding = response.encoding or "utf-8"
        text = content.decode(encoding, errors="replace")
        return FetchResult(
            url=response.url,
            status_code=response.status_code,
            text=text,
            headers=raw_headers,
            content=content,
        )
    finally:
        response.close()
