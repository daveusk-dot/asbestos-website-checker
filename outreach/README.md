# Outreach

Cold email templates. They are not wired to a sending tool. Copying one into a mailbox is a manual step, done only after the checks below.

| Folder | Who it is for |
| --- | --- |
| `asbestos/` | UKAS or ATaC accredited asbestos firms that are limited companies or LLPs |

Conveyancers and letting agents have separate sequences under `drips/`. Do not use the asbestos templates for them.

Before any send:

1. Fill every braced placeholder. Search the draft for `{{` and stop if any remain. The full list is `compliance/PLACEHOLDERS.md`.
2. Confirm `{{OPT_OUT_URL}}` works and `{{PRIVACY_NOTICE_URL}}` opens a real notice. See `compliance/privacy_notice_line.md`.
3. Confirm the firm is `limited_company` or `llp` on Companies House. See `data/firm_list_README.md`.
4. Run `python -m compliance.suppression pre-send-check` for that address and status. Send only if it prints `allowed=yes`.
5. Use a finding you actually saw. Do not invent one.

Stop rules, including for this short sequence: any reply stops the remaining emails. An opt-out also appends the address to `data/suppression_list.csv`. Rows in that file are never deleted.
