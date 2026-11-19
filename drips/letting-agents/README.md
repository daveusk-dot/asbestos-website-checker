# Letting agent sequence

Five emails, suggested for days 0, 4, 10, 18, and 28. Read `sequence.md`. The machine-readable copy, including `stop_on: [reply, opt_out]`, is `sequence.yaml`.

This sequence is about the firm's website. It does not advise on lettings law, client money, redress schemes, or landlord obligations, and it does not tell a firm to display a membership it cannot show.

Email `la-04-one-finding` is sent only when `{{AUDIT_FINDING}}` and `{{FINDING_PAGE_URL}}` come from a real audit. Otherwise skip it.

Cold email still requires `limited_company` or `llp`, a published work address, and a clear `allowed=yes` from the pre-send check. On opt-out, append the address to `data/suppression_list.csv` and do not continue.
