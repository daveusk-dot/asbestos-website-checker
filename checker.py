from website import Website
import json

def run_audit(start_url, max_pages=15):
    site = Website(start_url, max_pages=max_pages)
    results = site.crawl()

    report = []
    total_warnings = 0

    for url, page in results.items():
        if isinstance(page, dict) and "error" in page:
            report.append({"url": url, "error": page["error"]})
            continue

        data = page.as_dict()
        total_warnings += len(data["warnings"])
        report.append(data)

    summary = {
        "start_url": start_url,
        "pages_checked": len(results),
        "total_warnings": total_warnings,
        "pages": report
    }

    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    # Example – replace with a real asbestos firm URL
    run_audit("https://example.com", max_pages=10)
