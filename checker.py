"""Audit a small UK trade website and write a client-ready summary.

Single site:
    python checker.py https://example.com --max-pages 15

A CSV with a website column (the firm list or the 20-firm tracker):
    python checker.py --batch data/audit_test_asbestos_20.csv

Reports go to reports/ unless --output is set. That folder is gitignored.
Nothing in this tool sends email.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from batch import run_batch
from runner import run_audit
from trade import TradeError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a small UK trade website and write a client-ready summary."
    )
    parser.add_argument("url", nargs="?", help="Website to audit, for example https://example.com")
    parser.add_argument("--batch", type=Path, help="CSV with a website column. One report is written per filled row.")
    parser.add_argument("--max-pages", type=int, default=15, help="Maximum HTML pages to fetch on each site (default 15).")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds to wait between requests (default 0.5).")
    parser.add_argument("--trade", default="asbestos_surveying", help="Trade config id (default asbestos_surveying).")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports"),
        help="Folder for JSON, markdown, and the updated CSV copy (default reports/).",
    )
    parser.add_argument("--max-external", type=int, default=40, help="Maximum external links to request (default 40).")
    parser.add_argument("--skip-external", action="store_true", help="Do not request links that leave the site.")
    parser.add_argument("--firm-name", default=None, help="Name to print on a single-site report.")
    parser.add_argument("--json", action="store_true", help="Print the JSON summary to stdout instead of the markdown.")
    args = parser.parse_args(argv)

    if args.batch and args.url:
        parser.error("Pass a URL or --batch, not both.")
    if not args.batch and not args.url:
        parser.error("Pass a URL, or --batch with a CSV.")
    if args.max_pages < 1:
        parser.error("--max-pages must be at least 1.")
    if args.delay < 0:
        parser.error("--delay cannot be negative.")

    if args.batch:
        outcome = run_batch(
            args.batch,
            args.output,
            run_audit=run_audit,
            default_trade=args.trade,
            max_pages=args.max_pages,
            delay=args.delay,
            check_external=not args.skip_external,
            max_external=args.max_external,
        )
        print(
            f"Audited {outcome['audited']} site(s). "
            f"Skipped {outcome['skipped_blank']} blank row(s). "
            f"Updated sheet: {outcome['csv_path']}"
        )
        return 0

    try:
        summary = run_audit(
            args.url,
            args.max_pages,
            delay=args.delay,
            trade=args.trade,
            output_dir=args.output,
            check_external=not args.skip_external,
            max_external=args.max_external,
            firm_name=args.firm_name,
        )
    except (ValueError, TradeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Score: {summary['score']}/100")
    if summary.get("markdown_path"):
        print(f"Wrote {summary['markdown_path']}")
    if summary.get("json_path"):
        print(f"Wrote {summary['json_path']}")
    print()
    if args.json:
        printable = {key: value for key, value in summary.items() if key != "markdown"}
        print(json.dumps(printable, indent=2, ensure_ascii=False))
    else:
        print(summary["markdown"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
