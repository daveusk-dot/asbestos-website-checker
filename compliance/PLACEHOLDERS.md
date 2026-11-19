# Placeholders David must fill

Nothing in this list has been invented. A template, price, or assessment is not ready to send or to show to a client while the braces are still there.

Search the draft for `{{`. If any token remains, stop.

Per-firm tokens change every email. Identity, price, and policy tokens are filled once and then reused.

## Identity

| Token | What to put there |
| --- | --- |
| `{{SENDER_NAME}}` | The named person who sends the email. |
| `{{SENDER_ROLE}}` | That person's real role, in their own words. |
| `{{BUSINESS_NAME}}` | The real trading or registered name. |
| `{{POSTAL_ADDRESS}}` | A real postal address where post for the business is received. |
| `{{SENDER_EMAIL}}` | A mailbox that person reads. |
| `{{COMPANY_NUMBER_LINE}}` | One true line, such as the company number, or delete the line if there is no company number. Do not invent a number. |

## Links that must work

| Token | What to put there |
| --- | --- |
| `{{OPT_OUT_URL}}` | A working opt-out page or link. It must open without a password and cause the address to be appended to `data/suppression_list.csv`. Test it before the first send. |
| `{{PRIVACY_NOTICE_URL}}` | The URL of a real privacy notice. The checklist is `privacy_notice_line.md`. |
| `{{PRICING_URL}}` | The URL of the published prices. Until that page exists, rewrite the sentence so this token is gone. Do not send the braces. |

## Each recipient

| Token | What to put there |
| --- | --- |
| `{{FIRM_NAME}}` | The firm's name. |
| `{{CONTACT_NAME}}` | A person the firm publishes. If there is no name, change the greeting to `Hello,` and remove this token. Do not invent a name. |
| `{{WEBSITE}}` | The site that was audited, or the site being offered an audit. |
| `{{AUDIT_FINDING}}` | One finding taken from the checker and the manual review. If there is no finding, do not send the email that requires one. |
| `{{FINDING_PAGE_URL}}` | The public page the finding came from. |
| `{{SOURCE_DIRECTORY}}` | The directory or page where the work address was read. Name it. Do not write "public sources" and nothing else. |
| `{{SOURCE_DATE}}` | The date that directory or page was read. |
| `{{PREVIOUS_EMAIL_DATE}}` | The date the previous email in that sequence was sent. |

## Prices and contract terms

| Token | What to put there |
| --- | --- |
| `{{PRICE_FOUNDATION}}` | The Foundation price. None has been set. |
| `{{PRICE_VISIBILITY}}` | The Visibility price. None has been set. |
| `{{PRICE_DEMAND}}` | The Demand price. None has been set. |
| `{{VAT_TREATMENT}}` | The word `include` or the word `exclude`. The sheet does not choose. |
| `{{BILLING_BASIS_FOUNDATION}}` | Whether Foundation is a one-off or a repeating fee, and how often. |
| `{{BILLING_BASIS_VISIBILITY}}` | The same for Visibility. |
| `{{BILLING_BASIS_DEMAND}}` | The same for Demand. |
| `{{CONTRACT_LENGTH_FOUNDATION}}` | How long Foundation lasts. |
| `{{CONTRACT_LENGTH_VISIBILITY}}` | How long Visibility lasts. |
| `{{CONTRACT_LENGTH_DEMAND}}` | How long Demand lasts. |
| `{{NOTICE_PERIOD}}` | The notice period for cancellation. |
| `{{CANCELLATION_EMAIL}}` | The mailbox that receives a cancellation. |
| `{{CANCELLATION_FEE}}` | The fee, or the word `none`. |
| `{{RENEWAL_TERMS}}` | Whether the arrangement ends, renews only by agreement, or continues until notice. |
| `{{REFUND_TERMS}}` | What happens to money already paid and work already done. |
| `{{VISIBILITY_INCLUDES_GBP}}` | `yes` or `no`. The checker does not audit Google Business Profile. |
| `{{FOUNDATION_REVIEW_ROUNDS}}` | How many further looks at the same checklist are included. |
| `{{DEMAND_COPY_PAGES}}` | How many pages of copy recommendations are included. |
| `{{DEMAND_EXTRAS}}` | Anything else in Demand, or the word `none`. |

## Legitimate-interests note and privacy notice

| Token | What to put there |
| --- | --- |
| `{{LIA_DATE}}` | The date the legitimate-interests note is adopted. Until then, do not send. |
| `{{LIA_REVIEW_DATE}}` | The date by which the note will be read again. |
| `{{RETENTION_PERIOD}}` | How long firm and correspondence records are kept. Suppression rows are kept permanently, whatever this says. |
| `{{EMAIL_PROVIDER}}` | The provider that stores or sends the mail, or a plain statement that mail is sent from the sender's own mailbox. |
| `{{ICO_REGISTRATION_NUMBER}}` | The real registration number, or remove the token after confirming none is required. Do not invent one. |
