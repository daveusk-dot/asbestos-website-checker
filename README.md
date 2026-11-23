# Asbestos Website Checker

Python crawler that audits a small UK trade website and writes a client-ready summary. Asbestos surveying is the first trade. Another trade is a JSON file under `trades/`.

The folders `outreach/`, `drips/`, `pricing/`, `data/`, and `compliance/` are templates and records. Nothing in this repository sends email.

## Setup

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest, for the tests
```

## Run one site

```bash
python checker.py https://example.com --max-pages 15
```

Useful flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--max-pages` | 15 | HTML pages to fetch |
| `--delay` | 0.5 | Seconds between requests. robots.txt `Crawl-delay` is honoured, capped at 5 seconds |
| `--trade` | `asbestos_surveying` | Config file `trades/<id>.json` |
| `--output` | `reports/` | JSON and markdown. This folder is gitignored |
| `--skip-external` | off | Do not request links that leave the site |
| `--max-external` | 40 | Cap on external links that are requested |
| `--firm-name` | | Name printed on the summary |
| `--json` | off | Print the JSON summary instead of the markdown |

Set `AUDIT_CONTACT` (an email or URL) before crawling a site you do not own. It is added to the user agent. `PSI_API_KEY` adds a mobile PageSpeed Insights score. Without it, that step is skipped and the mark out of 100 does not change.

## Run a list

The firm-list template and the 20-firm tracker both have a `website` column.

```bash
python checker.py --batch path/to/your-tracker.csv --max-pages 15
```

Blank `website` cells are skipped. Each filled row gets a JSON file and a markdown file. A copy of the sheet named `<original>.updated.csv` is written in the output folder with `audit_run_date` (`YYYY-MM-DD`) and `audit_score` (0–100). The file you passed in is not changed. A `trade` cell selects `trades/<trade>.json` when that file exists.

Do not commit a filled tracker or a report that names a real firm. The empty sheet in `data/` stays empty.

## What is checked

The crawler follows redirects, treats `www` and the bare host as one site, and ignores fragments, trailing slashes, and tracking parameters (`utm_*`, `gclid`, `fbclid`, and similar) when deciding if a URL was already fetched. `robots.txt` is respected. PDF, images, and other non-HTML responses are not parsed. There is a delay between requests. The user agent names this project and, when set, `AUDIT_CONTACT`.

Accreditation and insurance are judged once for the site. If they appear somewhere but not on a service URL (a path containing `survey`, `service`, `removal`, and the other patterns in the trade file), the report says so. That second note does not reduce the score again. A “Contact” item in a menu is not treated as a phone number. Phones are read from `tel:` links and from UK-format numbers. Emails are read from `mailto:` links and from addresses. Template inboxes such as `info@example.com` do not count as a real address.

Per trade, the asbestos file looks for:

- UKAS, including a 4 or 5 digit number near the word UKAS (years and ISO numbers are ignored)
- ISO/IEC 17020 or 17025
- ATaC, ARCA, or BOHS, and a note if BOHS appears without P402
- An HSE asbestos licence when the site describes removal. A site that does not describe removal is not marked down for having no licence
- CHAS, SafeContractor, Constructionline, or TrustMark

For every trade:

- Public liability, professional indemnity, and employer’s liability, and whether a £ amount is stated
- Company number and registered office (what a limited company should show; this tool does not look the firm up)
- VAT number, privacy policy, cookie notice
- Name, UK postcode, and phone consistency across pages
- LocalBusiness-type JSON-LD (`LocalBusiness`, `ProfessionalService`, or a similar type) with name, address, telephone, and `areaServed`
- HTTPS, mixed content, meta description, image alt text, viewport, canonical, H1, title length, noindex
- Placeholder text (lorem ipsum, “My Company”, and the usual template inboxes), a holding page, and a stale copyright year
- For asbestos, HSG264 / management / refurbishment and demolition wording, against leftover “Type 2” or “Type 3”
- Broken internal links, with the page that linked to them, and broken external links up to the cap. HTTP 401, 403, and 429 are recorded as uncertain, not broken

A page that says both “asbestos removal” and “survey only” is flagged as conflicting wording.

## Score

The mark starts from the points below. They add up to 100. Penalties are subtracted afterwards, and the result is kept between 0 and 100. If the homepage cannot be fetched, the score is 0.

A missing contact page is mentioned in the report and is not a separate line in the score. Phone and email are the scored contact signals. PageSpeed is reported when `PSI_API_KEY` is set and is not part of the 100.

| Check | Points |
| --- | --- |
| UKAS mentioned | 5 |
| UKAS accreditation number | 4 |
| ISO/IEC 17020 or 17025 | 4 |
| Trade body (ATaC, ARCA, or BOHS) | 5 |
| HSE licence, or removal not offered | 4 |
| CHAS, SafeContractor, Constructionline, or TrustMark | 2 |
| Public liability mentioned | 5 |
| Professional indemnity mentioned | 4 |
| Employer's liability mentioned | 2 |
| An insurance amount is stated | 1 |
| Company number | 4 |
| Registered office | 3 |
| VAT number | 2 |
| Privacy policy | 3 |
| Cookie notice | 2 |
| UK phone number | 3 |
| Email address | 1 |
| Business name consistent | 3 |
| Phone numbers consistent | 4 |
| Postcodes consistent | 4 |
| LocalBusiness-type JSON-LD | 2 |
| JSON-LD name, address, telephone, and areaServed | 1 |
| HTTPS | 8 |
| No mixed content | 2 |
| Homepage meta description | 2 |
| Image alt text | 2 |
| Viewport | 1 |
| Canonical | 1 |
| Homepage title length | 1 |
| Single H1 on the homepage | 1 |
| Homepage is not noindex | 1 |
| No template or placeholder text | 4 |
| Not a holding page | 3 |
| Copyright year is current | 1 |
| Current survey terminology | 3 |
| Outdated terminology is not used alone | 1 |
| Testimonials or reviews | 1 |

Category totals: accreditation and trade bodies 24, insurance 12, legal and contact 18, NAP and schema 14, technical 19, content 13.

Penalties:

- Removal and survey-only wording on the same page: −5
- Broken internal link: −2 each, up to −6
- Broken external link: −1 each, up to −3

Mixed content is scored only on HTTPS pages. An HTTP site loses the HTTPS points and is not also marked down for mixed content. Several postcodes are not a mismatch when every page that shows one shares at least one of them; the report lists them so a branch address can be checked by hand. Title length is scored on the homepage, in the range 15–60 characters. Image alt text scores 2 when at least 90% of images have an alt attribute (an empty alt counts), 1 from 50% up, and 0 below that. No images scores 2.

Leave a list empty in a trade file when that check does not apply. Empty UKAS terms, trade bodies, standards, HSE terms, schemes, or terminology score as “not used for this trade” and do not reduce the mark. See `trades/README.md`.

## Report

The markdown follows `CLIENT-SUMMARY.md`: overall, key findings, quick wins, and a line that the result is automated and needs a manual review. It also shows the score by area. It does not say an accreditation, a policy, or a company number is valid. It only says what the pages contain.

## Tests

```bash
python -m pytest
```

The tests use fictional HTML and a stand-in for HTTP. `tests/fixtures/harbour/` is a made-up firm, Harbour and Wren, served locally by one test. There are no real firms in this repository.

## Not in this version

- No lookup against the UKAS directory or Companies House. The compliance notes for this project say not to invent a number, and the checker only reads the site.
- Pages that are built entirely in JavaScript will look empty. The crawler does not run a browser.
- Subdomains other than `www` are treated as different hosts.
- PageSpeed is a single mobile performance score, and only when `PSI_API_KEY` is set.
- Gas, electrical, roofing, and damp are not filled in. Add `trades/<id>.json` using the asbestos file as the pattern.

## Compliance and outreach

| Folder | What it is |
| --- | --- |
| `outreach/` | Cold email to UKAS or ATaC asbestos firms (limited companies and LLPs) |
| `drips/` | Separate sequences for conveyancers and letting agents |
| `pricing/` | Draft Foundation, Visibility, and Demand tiers |
| `data/` | Empty firm-list template, suppression list, and the 20-firm asbestos tracker |
| `compliance/` | Legitimate-interests note, email footer, and the suppression check |

Rules for any real send:

- Email only a limited company or an LLP, after the status has been read on Companies House. Sole traders, ordinary partnerships, and unknown status are excluded.
- Every marketing email names the sender, names the business, gives a postal address, says where the address came from, links to a privacy notice, and offers a working opt-out.
- Any reply stops the sequence. An opt-out also appends the address to `data/suppression_list.csv`. Rows in that file are never deleted.
- Run `python -m compliance.suppression pre-send-check` immediately before each manual send.
- Fill every braced placeholder first. The list is `compliance/PLACEHOLDERS.md`. Do not invent a finding, a price, an address, or a company number.
