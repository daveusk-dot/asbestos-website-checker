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
