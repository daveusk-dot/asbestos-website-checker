# Conveyancer drip sequence

Readable copy of `sequence.yaml`. If the two files disagree, update them together before use. The YAML file is the machine-readable source for `stop_on` and the day offsets.

**Stop rules:** any reply stops the sequence at once, including an out-of-office reply. An opt-out stops it and the address is appended to `data/suppression_list.csv`. That list is append-only. Do not send the finding email unless the finding is real.

Day offsets are suggestions. The pre-send check must print `allowed=yes` before each email. Firms that are not a limited company or an LLP are not emailed. Nothing in this folder sends email.

If there is no published contact name, change `Hello {{CONTACT_NAME}},` to `Hello,` before sending. Do not invent a name.

## cv-01-introduction

**Suggested day:** 0

**Needs a real audit finding:** No.

**Subject:** A free look at {{FIRM_NAME}}'s website

**Body:**

Hello {{CONTACT_NAME}},

I am {{SENDER_NAME}}, {{SENDER_ROLE}} at {{BUSINESS_NAME}}. I help professional firms tidy the public pages of their websites. I am writing to {{FIRM_NAME}} because conveyancing firms are one of the groups I contact.

I am not a conveyancer and I do not advise on conveyancing work or on conveyancing quality schemes. This is only about the website at {{WEBSITE}}.

I can run a free audit. It is an automated check of public pages, followed by a manual review. It looks at page titles, headings, contact details, forms, and whether trust wording already on the site is easy to find. It does not promise rankings or new instructions.

If you would like the one-page summary, reply and ask for it. If you would not, the opt-out link below is enough.

Kind regards,
{{SENDER_NAME}}
{{SENDER_ROLE}}
{{BUSINESS_NAME}}
{{POSTAL_ADDRESS}}
{{SENDER_EMAIL}}
{{COMPANY_NUMBER_LINE}}

Where we obtained your details: the work contact details for {{FIRM_NAME}} were taken from {{SOURCE_DIRECTORY}} on {{SOURCE_DATE}}. They were not obtained from you directly.

Privacy notice: {{PRIVACY_NOTICE_URL}}

If you would like no further emails, use this opt-out link: {{OPT_OUT_URL}}
Or reply with the single word "unsubscribe". We will stop, and we will not email this address again.

## cv-02-what-the-check-covers

**Suggested day:** 5

**Needs a real audit finding:** No.

**Subject:** What the {{FIRM_NAME}} website check covers

**Body:**

Hello {{CONTACT_NAME}},

A short follow-up on the free audit of {{WEBSITE}}. I will stop if you reply, including if you only write to say no.

The check is automated, and I then do a manual review. On a conveyancer's site it is aimed at the public pages a potential client sees: whether each page has a sensible title and heading, whether a phone number or email is obvious, whether a contact form has a working destination, and whether wording you already use is consistent from page to page.

It does not review files, quotes, or legal content for accuracy. I would not suggest adding a badge or a membership you do not hold.

Reply if you want the summary. Otherwise you can ignore this, or opt out with the link below. You will not receive the rest of this sequence.

Kind regards,
{{SENDER_NAME}}
{{SENDER_ROLE}}
{{BUSINESS_NAME}}
{{POSTAL_ADDRESS}}
{{SENDER_EMAIL}}
{{COMPANY_NUMBER_LINE}}

Where we obtained your details: the work contact details for {{FIRM_NAME}} were taken from {{SOURCE_DIRECTORY}} on {{SOURCE_DATE}}. They were not obtained from you directly.

Privacy notice: {{PRIVACY_NOTICE_URL}}

If you would like no further emails, use this opt-out link: {{OPT_OUT_URL}}
Or reply with the single word "unsubscribe". We will stop, and we will not email this address again.

## cv-03-one-finding

**Suggested day:** 12

**Needs a real audit finding:** Yes. Skip this email if you do not have one. Do not invent it.

**Subject:** One point from {{FIRM_NAME}}'s website

**Body:**

Hello {{CONTACT_NAME}},

I have looked at {{WEBSITE}}. The audit is an automated check of public pages, followed by a manual review.

On {{FINDING_PAGE_URL}} I noted this: {{AUDIT_FINDING}}

That is one point, not a full report, and it is not a comment on your legal work. I can send the one-page summary if you want it. There is no fee for the summary.

If you reply, I will stop this sequence and answer only what you asked. If you would like no further email, use the opt-out link.

Kind regards,
{{SENDER_NAME}}
{{SENDER_ROLE}}
{{BUSINESS_NAME}}
{{POSTAL_ADDRESS}}
{{SENDER_EMAIL}}
{{COMPANY_NUMBER_LINE}}

Where we obtained your details: the work contact details for {{FIRM_NAME}} were taken from {{SOURCE_DIRECTORY}} on {{SOURCE_DATE}}. They were not obtained from you directly.

Privacy notice: {{PRIVACY_NOTICE_URL}}

If you would like no further emails, use this opt-out link: {{OPT_OUT_URL}}
Or reply with the single word "unsubscribe". We will stop, and we will not email this address again.

## cv-04-close

**Suggested day:** 21

**Needs a real audit finding:** No.

**Subject:** Closing the note to {{FIRM_NAME}}

**Body:**

Hello {{CONTACT_NAME}},

This is the last scheduled email in this sequence. I will not add you to another sequence unless you reply and ask me to.

The free audit of {{WEBSITE}} is still available if you want it: an automated check of public pages, followed by a manual review, with a one-page summary. Paid help exists only if, after that, you ask for it. I will not quote a price in this email. Prices, once set, will be at {{PRICING_URL}}. Until that page exists, I will only discuss price if you ask.

No further action is needed if you do not want the audit.

Kind regards,
{{SENDER_NAME}}
{{SENDER_ROLE}}
{{BUSINESS_NAME}}
{{POSTAL_ADDRESS}}
{{SENDER_EMAIL}}
{{COMPANY_NUMBER_LINE}}

Where we obtained your details: the work contact details for {{FIRM_NAME}} were taken from {{SOURCE_DIRECTORY}} on {{SOURCE_DATE}}. They were not obtained from you directly.

Privacy notice: {{PRIVACY_NOTICE_URL}}

If you would like no further emails, use this opt-out link: {{OPT_OUT_URL}}
Or reply with the single word "unsubscribe". We will stop, and we will not email this address again.
