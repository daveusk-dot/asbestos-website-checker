# Firm list template

`firm_list_template.csv` is an empty header. Do not put real firms in the template itself. Copy it to a working file that is not committed, or keep the working copy outside this repository, and fill that copy from directories you have actually read.

This file does not scrape Companies House or any directory.

## Columns

| Column | What to enter |
| --- | --- |
| `firm_name` | The name on the directory entry, then corrected to the registered name if Companies House differs. |
| `website` | The firm's own site, including `https://`. Leave blank if you have not found one. Do not guess a domain. |
| `trade` | One of `asbestos_surveying`, `gas`, `electrical`, `roofing`, `damp_proofing`, `conveyancing`, `letting`, or another short label you will actually use. The first cold campaign is asbestos only. |
| `companies_house_number` | The number from the Companies House record. Leave blank until you have looked it up. Never invent one. |
| `legal_status` | One of the values below, from that Companies House record. |
| `legal_status_checked_date` | The date you looked at Companies House, as `YYYY-MM-DD`. |
| `contact_name` | A named person only if the directory or the site publishes one. Otherwise leave blank. Do not invent a name. |
| `contact_role` | The role published next to that person, such as director or office manager. Leave blank if you do not have it. |
| `contact_email` | A work address the firm publishes. No personal webmail. No guessed `firstname.surname` addresses. |
| `email_source` | The page or directory row where that address was read, in words. |
| `accreditation` | Only what the directory shows, such as `UKAS`, `ATaC`, or `ARCA`. Leave blank if you did not see it. Do not infer. |
| `source_directory` | The directory or page the firm was found in. This is the phrase that later fills `{{SOURCE_DIRECTORY}}`. |
| `eligible_for_cold_email` | `yes`, `no`, or blank until the checks below are done. |

## Legal status

Look the firm up on Companies House and copy the status into `legal_status`. Use only these values:

| Value | Cold email |
| --- | --- |
| `limited_company` | Allowed, if the rest of the checks pass. Record a public limited company as `limited_company`. |
| `llp` | Allowed, if the rest of the checks pass. |
| `sole_trader` | Excluded. Individual subscriber under PECR. |
| `ordinary_partnership` | Excluded. Individual subscriber under PECR. |
| `unknown` | Excluded until a real check is recorded. |

Scottish partnerships, limited partnerships, charities, overseas companies, and anything else you are unsure about are recorded as `unknown` and excluded. That is narrower than the widest reading of the PECR corporate-subscriber rule. Do not widen it without revising `compliance/legitimate_interests_assessment.md`.

Re-check Companies House if `legal_status_checked_date` is more than 90 days old before a send. Ninety days is a suggestion, not a legal time limit.

## When `eligible_for_cold_email` may be `yes`

Set `yes` only if all of these are true:

- `legal_status` is `limited_company` or `llp`, and the check date is filled in.
- `contact_email` is a published work address, and `email_source` says where it was read.
- `source_directory` is filled in.
- The address is not on `data/suppression_list.csv`.

Set `no` for `sole_trader`, `ordinary_partnership`, `unknown`, a suppressed address, a personal webmail address, a guessed address, or a missing source.

Leave the cell blank until you have done the checks. A `yes` in this column does not replace the pre-send check. Immediately before each manual send, run:

```bash
python -m compliance.suppression pre-send-check \
  --email the-work-address \
  --legal-status limited_company
```

Use the status you actually recorded. If the command does not print `allowed=yes`, do not send.
