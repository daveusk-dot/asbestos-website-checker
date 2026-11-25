"""Turn an audit summary (from checker.run_audit) into a one-page Markdown report."""
from datetime import date
from urllib.parse import urlparse

# Generic issue code -> (finding headline, quick-win advice). Order = order in the report.
# Niche-specific findings (trust marks, required mentions, conflicting wording) carry their own
# headline and advice, taken from the niche config, and are listed before these.
FINDINGS = [
    ("no_contact",
     "No contact details",
     "Put a phone number and email address in the header or footer of every page."),
    ("no_direct_contact",
     "No phone number or email visible",
     "Show a clickable phone number (tel: link) and email, not just a contact page link."),
    ("contact_no_form",
     "Contact page has no form",
     "Add a simple enquiry form (name, email/phone, message)."),
    ("form_no_action",
     "Contact form has no clear destination",
     "Check the form actually submits somewhere and enquiries are received."),
    ("form_missing_fields",
     "Contact form missing key fields",
     "Include at least name, a way to reply, and a message box."),
    ("title_missing", "Missing page title", "Give every page a unique, descriptive title."),
    ("title_length", "Page title too short or too long", "Keep titles to a sensible length (under about 70 characters)."),
    ("meta_description_missing", "Missing meta description",
     "Write a short, unique description (about 50-160 characters) for each page."),
    ("meta_description_length", "Meta description too short or too long",
     "Keep descriptions to roughly 50-160 characters."),
    ("h1_missing", "Missing H1 heading", "Give each page one clear H1 heading."),
    ("h1_multiple", "Multiple H1 headings", "Use a single H1 per page."),
    ("thin_content", "Thin content", "Expand thin pages with useful detail, or merge them."),
    ("images_no_alt", "Images without alt text", "Add short descriptive alt text to images."),
    ("viewport_missing", "No mobile viewport tag", "Add a viewport meta tag so the site renders properly on phones."),
    ("canonical_missing", "No canonical tag", "Add canonical tags to avoid duplicate-page confusion."),
]

SITE_FINDINGS = {
    "not_https": "Move the site to https.",
    "duplicate_title": "Give each page its own unique title.",
    "duplicate_meta_description": "Write a unique meta description for each page.",
    "no_local_schema": "Add LocalBusiness structured data (name, address, phone, areas served).",
    "no_address": "Show your business address/postcode on the site for local trust and search.",
}

MAX_PAGES_LISTED = 6


def _label(url):
    path = urlparse(url).path.strip("/")
    return path if path else "Home"


def _format_pages(urls, total):
    if len(urls) == total and total > 1:
        return f"all {total} pages"
    labels = [_label(u) for u in urls]
    if len(labels) > MAX_PAGES_LISTED:
        extra = len(labels) - MAX_PAGES_LISTED
        labels = labels[:MAX_PAGES_LISTED] + [f"+{extra} more"]
    return ", ".join(labels)


def _pretty_date(iso):
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        d = date.today()
    return f"{d.day} {d.strftime('%B %Y')}"


def build_markdown(summary):
    pages = summary["pages"]
    total = len(pages)

    # code -> list of page urls affected, and the first issue seen for each code
    affected = {}
    first_issue = {}
    for p in pages:
        for issue in p.get("issues", []):
            affected.setdefault(issue["code"], []).append(p["url"])
            first_issue.setdefault(issue["code"], issue)

    generic = {code: (headline, advice) for code, headline, advice in FINDINGS}
    niche_codes = [c for c in affected if c not in generic]
    ordered_codes = niche_codes + [c for c, _, _ in FINDINGS]

    findings = []   # (headline, detail, advice)
    for code in ordered_codes:
        urls = affected.get(code)
        if not urls:
            continue
        issue = first_issue[code]
        default_headline, default_advice = generic.get(code, (issue["message"], ""))
        headline = issue.get("headline") or default_headline
        advice = issue.get("advice") or default_advice
        detail = f"Seen on {_format_pages(urls, total)}"
        if code == "no_accreditation" and len(urls) < total:
            headline = "Trust marks shown inconsistently"
            detail = f"Missing on {_format_pages(urls, total)}; shown elsewhere"
        if code == "title_length":
            examples = [i["message"] for p in pages for i in p["issues"] if i["code"] == code][:3]
            detail += " (" + "; ".join(examples) + ")"
        findings.append((headline, detail, advice))

    for issue in summary.get("site_issues", []):
        advice = SITE_FINDINGS.get(issue["code"])
        if advice:
            detail = issue["message"]
            findings.append(("Site-wide: " + issue["message"].split(":")[0], detail, advice))

    errors = summary.get("errors", [])

    lines = [
        "# Quick Website Audit Summary",
    ]
    if summary.get("business"):
        lines.append(f"**Business:** {summary['business']}  ")
    lines += [
        f"**Site:** {summary['start_url']}  ",
        f"**Pages checked:** {total}  ",
        f"**Date:** {_pretty_date(summary.get('date'))}",
        "",
        "## Overall",
    ]
    if not findings and not errors:
        lines.append("No issues were found on the pages checked. The basics look solid.")
    else:
        parts = [f"{len(findings)} issue type(s) found across {total} page(s)."]
        if errors:
            parts.append(f"{len(errors)} page(s) could not be fetched.")
        lines.append(" ".join(parts))

    if findings:
        lines += ["", "## Key findings", ""]
        for n, (headline, detail, _) in enumerate(findings, 1):
            lines.append(f"{n}. **{headline}**  ")
            lines.append(f"   {detail}")
        lines += ["", "## Quick wins"]
        seen = set()
        for _, _, advice in findings:
            if advice and advice not in seen:
                seen.add(advice)
                lines.append(f"- {advice}")

    if errors:
        lines += ["", "## Pages that could not be checked"]
        for e in errors:
            origin = ""
            if e.get("linked_from"):
                origin = " (linked from " + ", ".join(_label(u) for u in e["linked_from"][:3]) + ")"
            lines.append(f"- {_label(e['url'])}: {e['error']}{origin}")

    lines += [
        "",
        "---",
        "*Generated by a lightweight automated audit tool. Manual review recommended for final recommendations.*",
        "",
    ]
    return "\n".join(lines)
