# Email footer

Use this block at the end of every marketing email. It is the named sender, the business identity, the postal address, the source line, the privacy notice line, and the opt-out.

Do not send an email while any `{{placeholder}}` is still in it. Do not send while `{{OPT_OUT_URL}}` is a dead link or while `{{PRIVACY_NOTICE_URL}}` does not open a real notice. This repository does not send email and does not host those pages.

`{{COMPANY_NUMBER_LINE}}` must be replaced with one real line, such as the company number, or removed if there is no company number. Do not invent a number.

## Block

```
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
```
