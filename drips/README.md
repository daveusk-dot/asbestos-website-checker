# Drip sequences

Two separate sequences. They are not sent by this repository. A person sends each email, after the pre-send check, and only if the sequence has not already stopped.

| Folder | Audience | Emails | Suggested days |
| --- | --- | --- | --- |
| `conveyancers/` | Conveyancers | 4 | 0, 5, 12, 21 |
| `letting-agents/` | Letting agents | 5 | 0, 4, 10, 18, 28 |

Each folder has `sequence.yaml` (machine-readable, including `stop_on`) and `sequence.md` (the same emails for reading). The day numbers are suggestions.

## Stop rules

These apply to both sequences, and they override the calendar:

- **Any reply stops the sequence immediately.** That includes a short no, a request for the summary, and an automatic out-of-office. If they asked for the summary, send the summary. Do not send the remaining scheduled emails.
- **An opt-out stops the sequence immediately.** Append the address to `data/suppression_list.csv`. Do not delete that row. A one-line confirmation, with no marketing, is allowed.
- A hard bounce or a complaint is also added to the suppression list and is not emailed again.
- The finding email is skipped when there is no real finding from the checker plus a manual review. Do not invent a finding. Skipping that one email does not cancel the later close email, unless a stop rule has already fired.
- Before every email, `python -m compliance.suppression pre-send-check` must print `allowed=yes`. Limited companies and LLPs only.

Every email uses the footer in `compliance/email_footer.md`: named sender, business name, postal address, source line, privacy notice line, and opt-out.
