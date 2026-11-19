# Letting agent drip sequence

Readable copy of `sequence.yaml`. If the two files disagree, update them together before use. The YAML file is the machine-readable source for `stop_on` and the day offsets.

**Stop rules:** any reply stops the sequence at once, including an out-of-office reply. An opt-out stops it and the address is appended to `data/suppression_list.csv`. That list is append-only. Do not send the finding email unless the finding is real.

Day offsets are suggestions. The pre-send check must print `allowed=yes` before each email. Firms that are not a limited company or an LLP are not emailed. Nothing in this folder sends email.

If there is no published contact name, change `Hello {{CONTACT_NAME}},` to `Hello,` before sending. Do not invent a name.

## la-01-introduction

**Suggested day:** 0

**Needs a real audit finding:** No.

**Subject:** A free look at {{FIRM_NAME}}'s website

**Body:**

Hello {{CONTACT_NAME}},

I am {{SENDER_NAME}}, {{SENDER_ROLE}} at {{BUSINESS_NAME}}. I am writing to letting agents about their public websites, starting with a free audit of {{WEBSITE}}.

I do not advise on lettings law, client money, redress schemes, or landlord obligations. I look at the website only.

The audit is an automated check of public pages, followed by a manual review. It covers titles, headings, contact details, forms, and trust wording that is already on the site. It does not promise more landlord or tenant enquiries.

Reply if you would like the summary. If you would not, use the opt-out link and I will not continue this sequence.

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

## la-02-contact-path

**Suggested day:** 4

**Needs a real audit finding:** No.

**Subject:** Contact details on {{FIRM_NAME}}'s site

**Body:**

Hello {{CONTACT_NAME}},

One thing the audit looks at on {{WEBSITE}} is whether a person can see how to get in touch. The check is automated, followed by a manual review. It flags pages with no obvious phone number or email, and contact pages whose form is missing, has nowhere to send the message, or is short of the usual name, email, message, or phone fields.

I am not saying {{FIRM_NAME}} has that problem. This email does not contain a finding. I can run the check and send the summary if you reply and ask.

If you reply for any reason, this sequence stops. The opt-out link does the same.

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

## la-03-trust-wording

**Suggested day:** 10

**Needs a real audit finding:** No.

**Subject:** Trust wording on the {{FIRM_NAME}} website

**Body:**

Hello {{CONTACT_NAME}},

The same audit looks at trust wording that {{WEBSITE}} already publishes, for example insurance or a scheme membership, and whether that wording is consistent on the pages a crawl reaches.

I will not suggest a logo, a redress scheme, or an accreditation the firm cannot show. The check does not confirm that a membership is valid. It only reads the public site. It is an automated check of public pages, followed by a manual review.

If a real finding exists, it goes in a later email in this sequence, and only as something the site itself shows. Reply if you want the summary, or opt out below.

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

## la-04-one-finding

**Suggested day:** 18

**Needs a real audit finding:** Yes. Skip this email if you do not have one. Do not invent it.

**Subject:** One point from {{FIRM_NAME}}'s website

**Body:**

Hello {{CONTACT_NAME}},

I reviewed {{WEBSITE}} with an automated check and a manual review.

On {{FINDING_PAGE_URL}} I noted this: {{AUDIT_FINDING}}

This is a website observation, not advice about your agency's compliance. I can send the short summary if you want it, at no charge.

Any reply stops the rest of the sequence. The opt-out link stops it as well, and the address is then suppressed.

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

## la-05-close

**Suggested day:** 28

**Needs a real audit finding:** No.

**Subject:** Last email in this sequence for {{FIRM_NAME}}

**Body:**

Hello {{CONTACT_NAME}},

I will not send further scheduled emails to {{FIRM_NAME}} about this. The free audit remains available if you reply and ask for it: an automated check of public pages, followed by a manual review, and a one-page summary.

I will not start paid work unless you ask. Where prices are published they will be at {{PRICING_URL}}. Until that page exists I will only quote if you ask, using figures I have actually set, with the VAT treatment stated.

Nothing is required from you if you do not want the audit.

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
