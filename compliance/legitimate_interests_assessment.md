# Legitimate interests assessment

**Status: draft. Do not send email until this note is completed, dated, and adopted.**

This is an operational record for {{BUSINESS_NAME}}. It is not advice from a solicitor and it is not a decision by the Information Commissioner's Office. {{SENDER_NAME}} must read it and change it if the processing changes.

| Item | Entry |
| --- | --- |
| Controller | {{BUSINESS_NAME}}, {{POSTAL_ADDRESS}}, {{SENDER_EMAIL}} |
| Person adopting this note | {{SENDER_NAME}}, {{SENDER_ROLE}} |
| Date adopted | {{LIA_DATE}} |
| Review on or before | {{LIA_REVIEW_DATE}} |
| ICO registration | {{ICO_REGISTRATION_NUMBER}} — confirm whether one is required; do not invent it |
| Email provider, if any | {{EMAIL_PROVIDER}} |

## The processing this note covers

A small number of emails to a named work address at a UK firm, offering a free audit of that firm's website. Paid help is discussed only if the firm asks.

Audiences:

- Asbestos surveyors found in UKAS or ATaC public directories.
- Conveyancers.
- Letting agents.

Channel: email, sent by a person. Nothing in this repository sends email.

Data used: firm name, website, work email, contact name and role where published, legal status from Companies House, the directory and date, one website finding taken from the checker plus a manual review, and later replies. Suppression records are kept when someone opts out or objects.

## Who may be emailed

Cold email is limited to firms whose Companies House status is recorded as `limited_company` or `llp`.

Sole traders and ordinary partnerships are treated as individual subscribers under PECR and are out of scope. `unknown` is out of scope until a real check is recorded.

This rule is narrower than the full PECR category of "corporate subscriber". Scottish partnerships, limited partnerships, charities, public bodies, and overseas companies are not in the allowed list. Record them as `unknown` and do not email them unless this note is revised first. Do not describe that extra caution as a ban the statute imposes on Scottish partnerships.

The pre-send check in `compliance/suppression.py` refuses any address that is suppressed, or whose legal status is not `limited_company` or `llp`.

## 1. Purpose test

The purpose is direct marketing of {{BUSINESS_NAME}}'s own website-audit service to corporate subscribers, plus keeping a record of who asked not to be contacted.

That is a real business purpose. It is specific: one free audit offer, not a newsletter, not a sold list, and not a claim about the firm's regulated work.

The purpose is not served by emailing personal inboxes, sole traders, ordinary partnerships, or firms that have not had a Companies House check.

## 2. Necessity test

A work email is the contact these directories publish, and the message is about the firm's public website. The email carries a page-specific finding or a short description of the audit, a privacy link, and an opt-out that can be used at once.

Post is a possible alternative, but it is a poor fit for a link to a privacy notice and a one-click or one-reply refusal, and it does not remove the need to identify the sender. Email is proportionate only while the volume stays small, each message has a reason, and the sequence stops on any reply.

Data is limited to what the send and the opt-out need. The checker reads public web pages. It is not a reason to collect staff lists, private mobiles, or special-category data.

The first asbestos test is capped at 20 firms and is sent by hand, with the result written down. See `data/audit_test_README.md`.

## 3. Balancing test

The people affected are individuals at their work address, inside a limited company or an LLP. The content is not about their private life. The likely effect of an unwanted email is annoyance, not damage, provided the message is honest and easy to refuse.

They may not expect the email. That weighs against us. The mitigations are:

- The sender is named and the postal address is real.
- The email says which directory the address came from, and when (Article 14).
- Every email has a working opt-out and a privacy notice link.
- Any reply stops the sequence. An opt-out is written to the suppression list and is not removed.
- No finding is invented. The audit is described as an automated check plus a manual review.
- The email does not advise on asbestos licensing, conveyancing, client money, or redress schemes, and it does not tell a firm to display a badge it does not hold.
- There is no open-tracking pixel in this project, and no automated decision about the person.
- Personal webmail addresses are not used.
- Bought lists and scraped personal addresses are not used.

On that basis, the firm's interest in sending a limited, identified, stoppable B2B email can outweigh the inconvenience to a work inbox. This balance holds only for the processing described above.

## Opt-out and the right to object

This balance is not re-run when someone objects. Under UK GDPR Article 21(2), an objection to direct marketing stops that marketing. PECR also requires a simple means of refusing, and the refusal must be honoured.

Operational rule: any opt-out, unsubscribe, or objection is appended to `data/suppression_list.csv` and the sequence stops. Rows are never deleted. An erasure request for marketing data is met by keeping the suppression entry and stopping use of the address for marketing, not by forgetting that they opted out.

A reply that is not an opt-out also stops the scheduled sequence. If they asked for the summary, send the summary. Do not carry on with the rest of the sequence.

## Decision

**Not yet adopted. Do not send.**

Once the placeholders in this note are filled with true information, the opt-out URL works, the privacy notice is published, and {{SENDER_NAME}} has dated the note, legitimate interests can be relied on for this described email to `limited_company` and `llp` recipients only.

Until that date, the lawful basis is not in place for a real send.

## When this note stops being valid

Stop and rewrite the note before sending further email if any of these happen:

- a bought list, a competition entry, or a scraped personal inbox is added
- sole traders, ordinary partnerships, or unchecked firms are included
- the message claims rankings, leads, or a regulatory status the site did not state
- the opt-out link fails, or opt-outs are not added to the suppression list
- the suppression file is deleted, edited to remove a row, or replaced with a shorter file
- a new audience, a new channel, or open-tracking is introduced
- {{RETENTION_PERIOD}} is changed without updating the privacy notice

## Retention

Keep suppression rows permanently.

Keep other firm and correspondence records for {{RETENTION_PERIOD}}, then delete or anonymise them, except where a suppression row must remain. {{RETENTION_PERIOD}} is unset until {{SENDER_NAME}} chooses it. Do not copy a period from this sentence: none has been chosen.
