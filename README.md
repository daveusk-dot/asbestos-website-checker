# Website Checker for Small Trade Businesses

Python crawler that audits small trade websites and produces a one-page summary you can use for outreach.
It started with asbestos firms, but everything trade-specific lives in a per-niche config file, so it can be
pointed at any trade.

## What it does
- Crawls a site (limited number of pages), obeying `robots.txt`, skipping PDFs/images, with a polite delay
- Generic page checks: title and meta description length, H1, viewport, canonical, image alt text, thin content
- Contact checks: phone (`tel:` links and UK number patterns), email (`mailto:` links), contact form fields, UK postcode
- Site-wide checks: https, duplicate titles/descriptions, LocalBusiness structured data
- Niche checks from config: trust marks/accreditations, things a site should mention (e.g. insurance), conflicting wording
- Reports broken internal links along with the page that linked to them
- Batch mode: audit a list of sites in one go, with a report per site and an overview spreadsheet

## Setup
```bash
pip install -r requirements.txt
```

## Run one site
```bash
# Print full JSON results (generic checks only)
python checker.py https://example.co.uk/

# Use a niche, and write JSON plus a one-page Markdown summary
python checker.py https://example.co.uk/ --niche asbestos --json audit.json --report summary.md

# See which niches are available
python checker.py --list-niches
```

## Run a batch
Make a CSV with a `url` column (optional columns: `name`, `niche`, `max_pages`), or a plain text file with one
URL per line (`#` starts a comment):

```csv
url,name,niche,max_pages
https://example-one.co.uk,Example One Ltd,asbestos,10
https://example-two.co.uk,Example Two,,
```

```bash
python checker.py --batch sites.csv --niche asbestos --out-dir audits
```

A `niche` in the CSV overrides `--niche` for that row; rows with neither use generic checks. Output:

```
audits/
  summary.csv                 one row per site: status, pages checked, warnings, top issues, report path
  example-one-co-uk/
    report.md                 the one-page summary
    audit.json                full results
```

One failing site (unreachable, bad niche name) never stops the batch; it is recorded in `summary.csv`
with status `unreachable` or `error`.

Other options: `--max-pages N`, `--delay SECONDS` (between requests), `--site-delay SECONDS` (between sites),
`--ignore-robots`.

## Adding a niche
1. Copy `niches/_template.yaml` to `niches/<your-niche>.yaml`.
2. Fill in the sections that apply: `trust_marks`, `required_mentions`, `conflicts`, `thresholds`.
3. Run `python checker.py --list-niches` to confirm it loads. Typos in key names are reported as errors.

Check real accreditation names with the relevant trade body before listing them, and keep the advice wording
to "only state what you actually hold".

## Files
- `checker.py` - command line, batch mode and site-wide checks
- `website.py` - crawler
- `page.py` - per-page checks
- `niche.py` - loads and validates niche config
- `niches/` - one YAML file per trade (`_template.yaml` is the starting point)
- `report.py` - Markdown summary generator
- `tests/` - run with `python -m unittest discover -s tests`

The generated summary is automated; review it manually before sending to anyone.
