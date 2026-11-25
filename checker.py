import argparse
import json
import sys
from collections import defaultdict
from datetime import date

from page import Page
from website import Website


def _site_level_issues(start_url, pages):
    """Checks that only make sense across the whole site."""
    issues = []

    if start_url.lower().startswith("http://"):
        issues.append({"code": "not_https", "message": "Site is served over http:// rather than https://"})

    by_title = defaultdict(list)
    by_desc = defaultdict(list)
    for p in pages:
        if p.title:
            by_title[p.title].append(p.url)
        if p.meta_description:
            by_desc[p.meta_description].append(p.url)

    for title, urls in by_title.items():
        if len(urls) > 1:
            issues.append({
                "code": "duplicate_title",
                "message": f"Duplicate title on {len(urls)} pages: {title}",
                "urls": urls,
            })
    for desc, urls in by_desc.items():
        if len(urls) > 1:
            issues.append({
                "code": "duplicate_meta_description",
                "message": f"Duplicate meta description on {len(urls)} pages",
                "urls": urls,
            })

    if pages and not any(p.has_local_schema for p in pages):
        issues.append({
            "code": "no_local_schema",
            "message": "No LocalBusiness/Organization structured data found on any page",
        })
    if pages and not any(p.has_postcode for p in pages):
        issues.append({
            "code": "no_address",
            "message": "No UK postcode/address found on any page (local trust signal)",
        })
    return issues


def run_audit(start_url, max_pages=15, delay=0.5, respect_robots=True):
    site = Website(start_url, max_pages=max_pages, delay=delay, respect_robots=respect_robots)
    results = site.crawl()

    page_data = []
    page_objects = []
    errors = []
    total_warnings = 0

    for url, page in results.items():
        if isinstance(page, dict):
            errors.append({
                "url": url,
                "error": page["error"],
                "linked_from": sorted(site.linked_from.get(url, [])),
            })
            continue
        page_objects.append(page)
        data = page.as_dict()
        total_warnings += len(data["warnings"])
        page_data.append(data)

    site_issues = _site_level_issues(site.start_url, page_objects)

    return {
        "start_url": start_url,
        "date": date.today().isoformat(),
        "pages_checked": len(page_data),
        "total_warnings": total_warnings,
        "pages": page_data,
        "errors": errors,
        "site_issues": site_issues,
        "skipped": [{"url": u, "reason": r} for u, r in site.skipped],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit a small trade website.")
    parser.add_argument("url", help="Start URL, e.g. https://example.co.uk/")
    parser.add_argument("--max-pages", type=int, default=15, help="Maximum pages to crawl (default 15)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default 0.5)")
    parser.add_argument("--ignore-robots", action="store_true", help="Do not obey robots.txt")
    parser.add_argument("--json", metavar="FILE", help="Write the full JSON results to FILE")
    parser.add_argument("--report", metavar="FILE", help="Write a one-page Markdown summary to FILE")
    args = parser.parse_args(argv)

    summary = run_audit(
        args.url,
        max_pages=args.max_pages,
        delay=args.delay,
        respect_robots=not args.ignore_robots,
    )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"JSON results written to {args.json}", file=sys.stderr)

    if args.report:
        from report import build_markdown
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(build_markdown(summary))
        print(f"Report written to {args.report}", file=sys.stderr)

    if not args.json and not args.report:
        print(json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    main()
