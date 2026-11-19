# Asbestos Website Checker

Minimal Python crawler for auditing small trade websites (starting with asbestos firms).

## What it does
- Crawls a site (limited number of pages)
- Checks for missing/short/long titles
- Flags possible conflicting service wording (e.g. “asbestos removal” vs “survey only”)
- Flags pages with no obvious contact details
- Collects internal links and reports HTTP errors

## Setup
```bash
pip install -r requirements.txt
```

## Run
Edit the URL at the bottom of `checker.py`, then:
```bash
python checker.py
```

This is a starter sketch. Next steps: add more of the 9-check template, improve conflict detection, and generate a clean one-page summary for outreach.

## Compliance and outreach

These folders are the outreach and compliance material. They are templates and records only, and nothing in this repository sends email.

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

To run the suppression and template tests:

```bash
pip install -r requirements-dev.txt
python -m pytest
```
