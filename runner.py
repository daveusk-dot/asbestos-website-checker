"""Run one audit and write the JSON and markdown outputs."""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlparse

from audit import assess
from fetch import build_user_agent
from summary import render_markdown
from trade import load_trade
from website import Website


def run_audit(
    start_url: str,
    max_pages: int = 15,
    *,
    delay: float = 0.5,
    trade: str = "asbestos_surveying",
    output_dir: Path | str | None = None,
    fetcher=None,
    check_external: bool = True,
    max_external: int = 40,
    firm_name: str | None = None,
    today: date | None = None,
    psi_api_key: str | None = None,
    slot: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """Crawl one site and return the summary. Write files when output_dir is set."""
    audited_on = today or date.today()
    profile = load_trade(trade)
    site = Website(
        start_url,
        max_pages=max_pages,
        delay=delay,
        fetcher=fetcher,
        user_agent=user_agent,
        check_external=check_external,
        max_external=max_external,
    )
    crawl = site.crawl()
    assessment = assess(crawl, profile, audited_on, firm_name=firm_name)
    pagespeed = fetch_pagespeed(
        assessment.final_url,
        fetcher=site.fetcher,
        api_key=_psi_key(psi_api_key),
        user_agent=site.user_agent,
    )
    markdown = render_markdown(assessment, pagespeed)
    payload = _payload(assessment, pagespeed, crawl.user_agent)
    payload["markdown"] = markdown
    if output_dir is not None:
        folder = Path(output_dir)
        folder.mkdir(parents=True, exist_ok=True)
        stem = output_stem(assessment.final_url, firm_name, audited_on, slot)
        json_path = folder / f"{stem}.json"
        markdown_path = folder / f"{stem}.md"
        on_disk = {key: value for key, value in payload.items() if key != "markdown"}
        json_path.write_text(json.dumps(on_disk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown_path.write_text(markdown, encoding="utf-8")
        payload["json_path"] = str(json_path)
        payload["markdown_path"] = str(markdown_path)
    return payload


def output_stem(final_url: str, firm_name: str | None, day: date, slot: str | None = None) -> str:
    base = (firm_name or "").strip() or urlparse(final_url).netloc or "site"
    prefix = ""
    if slot and re.fullmatch(r"\d+", str(slot).strip()):
        prefix = f"{int(slot):02d}-"
    return f"{prefix}{slugify(base)}-{day.isoformat()}"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return (value[:80] or "site")


def fetch_pagespeed(url: str, *, fetcher, api_key: str, user_agent: str) -> dict:
    if not api_key:
        return {"skipped": True, "reason": "PSI_API_KEY is not set"}
    if fetcher is None:
        return {"skipped": True, "reason": "No HTTP fetcher was available for PageSpeed."}
    query = urlencode(
        {
            "url": url,
            "strategy": "mobile",
            "category": "performance",
            "key": api_key,
        }
    )
    target = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?{query}"
    try:
        result = fetcher(
            target,
            headers={"User-Agent": user_agent or build_user_agent()},
            timeout=60,
            read_body=True,
        )
    except TypeError:
        try:
            result = fetcher(target, headers={"User-Agent": user_agent or build_user_agent()}, timeout=60)
        except Exception as exc:
            return {"skipped": True, "reason": f"PageSpeed request failed ({exc})"}
    except Exception as exc:
        return {"skipped": True, "reason": f"PageSpeed request failed ({exc})"}
    if getattr(result, "error", None) or getattr(result, "status_code", 0) != 200:
        status = getattr(result, "error", None) or getattr(result, "status_code", "error")
        return {"skipped": True, "reason": f"PageSpeed request failed ({status})"}
    try:
        data = json.loads(result.text)
        score = data["lighthouseResult"]["categories"]["performance"]["score"]
        mobile = int(round(float(score) * 100))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {"skipped": True, "reason": "PageSpeed response did not include a performance score"}
    return {"skipped": False, "strategy": "mobile", "mobile_score": mobile}


def _psi_key(value: str | None) -> str:
    if value is None:
        return os.environ.get("PSI_API_KEY", "").strip()
    return value.strip()


def _payload(assessment, pagespeed: dict, user_agent: str) -> dict:
    return {
        "start_url": assessment.start_url,
        "final_url": assessment.final_url,
        "audited_at": assessment.audited_on.isoformat(),
        "trade": assessment.trade_id,
        "trade_label": assessment.trade_label,
        "firm_name": assessment.firm_name,
        "pages_checked": assessment.pages_checked,
        "score": assessment.score,
        "total_warnings": len(assessment.findings),
        "score_breakdown": assessment.items,
        "penalties": assessment.penalties,
        "findings": assessment.findings,
        "notes": assessment.notes,
        "signals": assessment.signals,
        "pagespeed": pagespeed,
        "user_agent": user_agent,
        "pages": [page.as_dict() for page in assessment.pages],
        "external_links": assessment.external_links,
        "skipped": assessment.skipped,
        "errors": assessment.errors,
    }
