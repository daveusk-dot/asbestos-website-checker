# Compliance

Templates and checks for UK B2B email. Nothing here sends email, and nothing here changes the website checker.

| File | Purpose |
| --- | --- |
| `legitimate_interests_assessment.md` | Draft purpose, necessity, and balancing test |
| `privacy_notice_line.md` | The privacy line, and what the linked page must say |
| `source_line.md` | The Article 14 "where we obtained your details" line |
| `email_footer.md` | The block every marketing email ends with |
| `suppression.py` | Append-only suppression list and pre-send check |
| `PLACEHOLDERS.md` | Every braced placeholder still to be filled |

The live suppression file is `data/suppression_list.csv`. It is header-only until a real opt-out is recorded.

## Suppression rules

- Add a row when someone opts out, objects, complains, or hard-bounces, and when a reply should stop contact with that address.
- Rows are never deleted and never rewritten. A mistaken row stays. Do not email that address.
- A row with an email suppresses that address only, even if the domain column is also filled.
- A row with a blank email and a domain suppresses every address at that domain.
- If `data/suppression_list.csv` is missing, empty, or has the wrong header, do not send and do not create a fresh file over the old one.

## Pre-send check

Cold email is allowed only when both are true:

1. The address is not suppressed.
2. `legal_status` is `limited_company` or `llp`.

`sole_trader`, `ordinary_partnership`, `unknown`, a blank status, and any other value are refused. Run the check immediately before each manual send. A `yes` in a spreadsheet does not replace it.

```bash
python -m compliance.suppression pre-send-check \
  --email work@firm.example \
  --legal-status limited_company
```

Exit `0` means allowed. Exit `1` means do not send. Exit `2` means the list or the arguments are unsafe; do not send.

```bash
python -m compliance.suppression add \
  --email work@firm.example \
  --reason opt_out \
  --source email_reply \
  --date 2026-11-19

python -m compliance.suppression is-suppressed --email work@firm.example
```

`is-suppressed` exits `1` when the address is suppressed and `0` when it is not.

Suggested `reason` values: `opt_out`, `reply`, `complaint`, `hard_bounce`, `manual`. Suggested `source` values: `email_reply`, `opt_out_link`, `phone`, `manual`. Other plain words are accepted. Do not delete a row to correct a reason; append another row if you need a clearer record.
