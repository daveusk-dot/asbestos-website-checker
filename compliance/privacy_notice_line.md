# Privacy notice line

Put this line in every marketing email, after the source line and before the opt-out:

```
Privacy notice: {{PRIVACY_NOTICE_URL}}
```

`{{PRIVACY_NOTICE_URL}}` must open a page that {{BUSINESS_NAME}} actually controls. A link to a homepage, an empty page, or a document that still contains placeholders is not enough.

This file is a checklist for that page. It is not a finished privacy notice and it is not legal advice.

## What the page needs to say

Complete these before the first send:

- Controller: {{BUSINESS_NAME}}, {{SENDER_NAME}}, {{POSTAL_ADDRESS}}, {{SENDER_EMAIL}}.
- If there is no company number, say so in ordinary words. If there is one, use it. Do not invent {{COMPANY_NUMBER_LINE}}.
- Purposes: offering a free website audit, answering replies, and quoting paid website work only when the firm asks.
- Lawful basis: legitimate interests, pointing at the assessment in `compliance/legitimate_interests_assessment.md`. Consent is not the basis for this cold email.
- Categories of data: firm name, work email address, contact name and role where published, website address, the directory it came from, correspondence, and suppression records.
- Source: the named directory or page in {{SOURCE_DIRECTORY}}, seen on {{SOURCE_DATE}}. Say that the details were not obtained from the person directly (UK GDPR Article 14).
- Recipients: no sale of the list. Name the email provider used to send or store mail: {{EMAIL_PROVIDER}}. If mail is sent by hand from a normal mailbox, say that.
- Retention: {{RETENTION_PERIOD}} for firm and correspondence records. Suppression entries are kept permanently so an opt-out can still be honoured. They are not deleted to satisfy an erasure request.
- Rights: access, rectification, erasure, restriction, and objection. State that the right to object to direct marketing is absolute: a request to stop ends marketing to that address.
- Complaint: the Information Commissioner's Office, with the ICO's public contact details.
- ICO registration: confirm whether {{BUSINESS_NAME}} must be on the register. If it must, publish {{ICO_REGISTRATION_NUMBER}}. If it need not, remove that placeholder and record why.
- No automated decision about a person. The website checker flags pages. It does not score people and it does not decide who is emailed on its own.
- Children: this contact is not aimed at children.

## Opt-out page

`{{OPT_OUT_URL}}` is separate from the privacy notice, but the notice should link to it.

Before any send, the opt-out URL must:

- open without a password or an account
- identify the address being opted out, either in the link or because the person can type it once
- cause that address to be appended to `data/suppression_list.csv`
- not be used as an excuse to send a further marketing email

A reply of "unsubscribe", or any other wording that asks you to stop, is also an opt-out. Add the address. A one-line confirmation with no sales content is fine. Do not follow it with the next email in the sequence.
