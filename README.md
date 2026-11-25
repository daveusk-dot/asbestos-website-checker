# Asbestos Website Checker

Minimal Python crawler for auditing small trade websites (starting with asbestos firms).

## What it does
- Crawls a site (limited number of pages), obeying `robots.txt`, skipping PDFs/images, with a polite delay
- Page checks: title and meta description length, H1, viewport, canonical, image alt text, thin content
- Trust signals: insurance/public liability, accreditation wording (UKAS, ARCA, BOHS...), UK postcode/address
- Contact checks: phone (`tel:` links and UK number patterns), email (`mailto:` links), contact form fields
- Flags possible conflicting service wording (e.g. "asbestos removal" vs "survey only")
- Site-wide checks: https, duplicate titles/descriptions, LocalBusiness structured data
- Reports broken internal links (HTTP errors) along with the page that linked to them
- Generates a one-page Markdown summary suitable for outreach

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
# Print full JSON results
python checker.py https://example.co.uk/

# Write JSON and a one-page Markdown summary
python checker.py https://example.co.uk/ --json audit.json --report summary.md

# Options
#   --max-pages N     pages to crawl (default 15)
#   --delay SECONDS   pause between requests (default 0.5)
#   --ignore-robots   do not obey robots.txt
```

## Files
- `checker.py` - command line entry point and site-wide checks
- `website.py` - crawler
- `page.py` - per-page checks
- `report.py` - Markdown summary generator

The generated summary is automated; review it manually before sending to a client.
