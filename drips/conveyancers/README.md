# Conveyancer sequence

Four emails, suggested for days 0, 5, 12, and 21. Read `sequence.md`. The machine-readable copy, including `stop_on: [reply, opt_out]`, is `sequence.yaml`.

This sequence is about the firm's website. It is not conveyancing advice and it does not comment on quality schemes except to say we will not tell a firm to add a badge it does not hold.

Email `cv-03-one-finding` is sent only when `{{AUDIT_FINDING}}` and `{{FINDING_PAGE_URL}}` come from a real audit. Otherwise skip it.

Cold email still requires `limited_company` or `llp`, a published work address, and a clear `allowed=yes` from the pre-send check. On opt-out, append the address to `data/suppression_list.csv` and do not continue.
