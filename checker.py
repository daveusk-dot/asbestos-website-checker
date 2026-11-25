import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from urllib.parse import urlparse

from niche import NicheConfigError, list_niches, load_niche
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


def run_audit(start_url, max_pages=15, delay=0.5, respect_robots=True, niche=None, business=None):
    """Audit one site. `niche` is a Niche object (see niche.load_niche); None means generic checks only."""
    site = Website(start_url, max_pages=max_pages, delay=delay, respect_robots=respect_robots, niche=niche)
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
        "business": business,
        "niche": niche.name if niche else "Generic trade website",
        "date": date.today().isoformat(),
        "pages_checked": len(page_data),
        "total_warnings": total_warnings,
        "pages": page_data,
        "errors": errors,
        "site_issues": site_issues,
        "skipped": [{"url": u, "reason": r} for u, r in site.skipped],
    }


# --------------------------------------------------------------------------
# Batch mode
# --------------------------------------------------------------------------

SUMMARY_COLUMNS = [
    "name", "url", "niche", "status", "pages_checked", "pages_with_errors",
    "total_warnings", "top_issues", "report", "error",
]


def _with_scheme(url):
    url = url.strip()
    return url if re.match(r"^https?://", url, re.I) else "https://" + url


def read_batch_file(path):
    """Read sites from a CSV (header with a 'url' column; optional name, niche, max_pages)
    or a plain text file with one URL per line ('#' starts a comment)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        raise ValueError(f"{path} contains no URLs")

    header = [h.strip().lower() for h in next(csv.reader([lines[0]]))]
    sites = []
    if "url" in header:
        for row in csv.DictReader(lines):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if not row.get("url"):
                continue
            sites.append({
                "url": _with_scheme(row["url"]),
                "name": row.get("name") or None,
                "niche": row.get("niche") or None,
                "max_pages": int(row["max_pages"]) if row.get("max_pages") else None,
            })
    else:
        for ln in lines:
            sites.append({"url": _with_scheme(ln.split(",")[0]), "name": None, "niche": None, "max_pages": None})
    if not sites:
        raise ValueError(f"{path} contains no URLs")
    return sites


def _slug(url, used):
    host = urlparse(url).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    base = re.sub(r"[^a-z0-9]+", "-", host).strip("-") or "site"
    slug, n = base, 2
    while slug in used:
        slug, n = f"{base}-{n}", n + 1
    used.add(slug)
    return slug


def _top_issues(summary, limit=5):
    counts = Counter(i["code"] for p in summary["pages"] for i in p["issues"])
    counts.update(i["code"] for i in summary["site_issues"])
    return "; ".join(f"{code}({n})" for code, n in counts.most_common(limit))


def run_batch(batch_file, out_dir, default_niche=None, max_pages=15, delay=0.5,
              respect_robots=True, site_delay=1.0):
    """Audit every site in `batch_file`, writing out_dir/<site>/{audit.json,report.md} and
    out_dir/summary.csv. One failing site never stops the run. Returns the summary rows."""
    from report import build_markdown

    sites = read_batch_file(batch_file)
    os.makedirs(out_dir, exist_ok=True)
    niches = {}
    used = set()
    rows = []

    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", encoding="utf-8", newline="") as sf:
        writer = csv.DictWriter(sf, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()

        for n, site in enumerate(sites, 1):
            if n > 1 and site_delay:
                time.sleep(site_delay)

            row = dict.fromkeys(SUMMARY_COLUMNS, "")
            row.update(name=site["name"] or "", url=site["url"])
            print(f"[{n}/{len(sites)}] {site['url']}", file=sys.stderr)

            try:
                spec = site["niche"] or default_niche
                if spec not in niches:
                    niches[spec] = load_niche(spec)
                niche = niches[spec]
                row["niche"] = niche.id

                summary = run_audit(
                    site["url"],
                    max_pages=site["max_pages"] or max_pages,
                    delay=delay,
                    respect_robots=respect_robots,
                    niche=niche,
                    business=site["name"],
                )

                site_dir = os.path.join(out_dir, _slug(site["url"], used))
                os.makedirs(site_dir, exist_ok=True)
                with open(os.path.join(site_dir, "audit.json"), "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2)
                report_path = os.path.join(site_dir, "report.md")
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(build_markdown(summary))

                row.update(
                    status="ok" if summary["pages_checked"] else "unreachable",
                    pages_checked=summary["pages_checked"],
                    pages_with_errors=len(summary["errors"]),
                    total_warnings=summary["total_warnings"],
                    top_issues=_top_issues(summary),
                    report=os.path.relpath(report_path, out_dir),
                )
                if not summary["pages_checked"] and summary["errors"]:
                    row["error"] = summary["errors"][0]["error"]
            except NicheConfigError as e:
                row.update(status="error", error=str(e))
            except Exception as e:  # keep going: one bad site must not stop the batch
                row.update(status="error", error=f"{type(e).__name__}: {e}")

            rows.append(row)
            writer.writerow(row)
            sf.flush()

    print(f"Summary written to {summary_path}", file=sys.stderr)
    return rows


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit small trade websites.")
    parser.add_argument("url", nargs="?", help="Start URL, e.g. https://example.co.uk/")
    parser.add_argument("--batch", metavar="FILE",
                        help="CSV (columns: url, optional name, niche, max_pages) or text file of URLs, one per line")
    parser.add_argument("--out-dir", default="audits", help="Batch mode: output folder (default: audits)")
    parser.add_argument("--site-delay", type=float, default=1.0,
                        help="Batch mode: seconds to wait between sites (default 1.0)")
    parser.add_argument("--niche", help="Niche name (see --list-niches) or path to a niche YAML file")
    parser.add_argument("--list-niches", action="store_true", help="List the available niches and exit")
    parser.add_argument("--max-pages", type=int, default=15, help="Maximum pages per site (default 15)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default 0.5)")
    parser.add_argument("--ignore-robots", action="store_true", help="Do not obey robots.txt")
    parser.add_argument("--json", metavar="FILE", help="Single site: write the full JSON results to FILE")
    parser.add_argument("--report", metavar="FILE", help="Single site: write a one-page Markdown summary to FILE")
    args = parser.parse_args(argv)

    if args.list_niches:
        print("generic (default: no niche-specific checks)")
        for name in list_niches():
            print(name)
        return None

    if bool(args.url) == bool(args.batch):
        parser.error("give either a URL or --batch FILE")

    if args.batch:
        try:
            return run_batch(
                args.batch, args.out_dir, default_niche=args.niche, max_pages=args.max_pages,
                delay=args.delay, respect_robots=not args.ignore_robots, site_delay=args.site_delay,
            )
        except (OSError, ValueError) as e:
            parser.error(str(e))

    try:
        niche = load_niche(args.niche)
    except NicheConfigError as e:
        parser.error(str(e))

    summary = run_audit(
        _with_scheme(args.url),
        max_pages=args.max_pages,
        delay=args.delay,
        respect_robots=not args.ignore_robots,
        niche=niche,
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
