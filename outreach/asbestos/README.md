# Asbestos cold outreach

Three emails for a UKAS or ATaC accredited asbestos firm: one first note and two follow-ups. The firm must be a limited company or an LLP. Sole traders, ordinary partnerships, and unchecked firms are not emailed.

The audit you are offering is the existing checker plus a manual review of its warnings. Say that. Do not describe it as a full consultancy report, a ranking study, or a view on whether the firm's accreditation or licence is valid.

Do not start the sequence until you have one real finding. Copy it from the checker output, then adjust the wording only where the manual review shows the checker was wrong or too blunt. If you have no finding, do not send a vaguer email in its place.

Do not attach the pricing sheet to these emails. Paid work is discussed only if the firm replies and asks.

## When to send

| File | Suggested day | Condition |
| --- | --- | --- |
| `01-initial.md` | 0 | Pre-send check passed, and `{{AUDIT_FINDING}}` is a real finding. |
| `02-follow-up.md` | 5 | No reply and no opt-out since email 1. |
| `03-final.md` | 12 | No reply and no opt-out since email 2. Then stop. |

The days are suggestions. A reply or an opt-out overrides them at once. An out-of-office reply also stops the sequence. If the person then asks for the summary, send the summary and do not resume the schedule.

Suggested window: a weekday, in UK business hours.

## Greeting

The templates start `Hello {{CONTACT_NAME}},`. If the directory does not name a person, change that line to `Hello,` before sending. Do not guess a name, and do not leave the braces in.

## What a finding looks like

This is the shape of the sentence, not text to send about a real firm:

> The service page uses both "asbestos removal" and "survey only".

`{{FINDING_PAGE_URL}}` is the public page you read. `{{AUDIT_FINDING}}` is one sentence. Do not add a claim the page did not support.

## Stop and suppression

`sequence.yaml` is the machine-readable copy of these rules. `stop_on` is `reply` and `opt_out`. On opt-out, append the address:

```bash
python -m compliance.suppression add \
  --email the-work-address \
  --reason opt_out \
  --source email_reply
```

Use `--source opt_out_link` when the opt-out came from `{{OPT_OUT_URL}}`. A hard bounce or a complaint is also appended (`hard_bounce` or `complaint`) and is not emailed again.
