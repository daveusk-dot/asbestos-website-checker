# Website support tiers

**Draft for David Harding to confirm. This is not a quote, not a contract, and not legal advice.**

Do not send this sheet, and do not quote from it, until every placeholder below is filled with a real figure or a real rule. No price in this file has been chosen.

Amounts are in pounds sterling. If billing will not be in GBP, rewrite that sentence before use.

## VAT — confirm before use

Prices **{{VAT_TREATMENT}}** VAT.

`{{VAT_TREATMENT}}` must be replaced with either **include** or **exclude**. This draft deliberately does not pick one. A price with the braces still in place is not ready to send.

## Tiers

| Tier | Price | Billing | Contract length | Notice period |
| --- | --- | --- | --- | --- |
| Foundation | {{PRICE_FOUNDATION}} | {{BILLING_BASIS_FOUNDATION}} | {{CONTRACT_LENGTH_FOUNDATION}} | {{NOTICE_PERIOD}} |
| Visibility | {{PRICE_VISIBILITY}} | {{BILLING_BASIS_VISIBILITY}} | {{CONTRACT_LENGTH_VISIBILITY}} | {{NOTICE_PERIOD}} |
| Demand | {{PRICE_DEMAND}} | {{BILLING_BASIS_DEMAND}} | {{CONTRACT_LENGTH_DEMAND}} | {{NOTICE_PERIOD}} |

`{{BILLING_BASIS_FOUNDATION}}`, `{{BILLING_BASIS_VISIBILITY}}`, and `{{BILLING_BASIS_DEMAND}}` must each say whether that tier is a one-off fee or a repeating fee, and how often a repeating fee is charged.

`{{CONTRACT_LENGTH_FOUNDATION}}`, `{{CONTRACT_LENGTH_VISIBILITY}}`, and `{{CONTRACT_LENGTH_DEMAND}}` must each say how long the arrangement lasts, and whether it then ends or continues.

## What you are not buying

These tiers do not include a promise of Google rankings, leads, instructions, or revenue. They do not include accreditation advice, insurance advice, or legal advice. They do not include permission to add a logo, a membership, or a licence the firm cannot evidence. They do not include email to the firm's own customers.

The names Visibility and Demand describe the aim of the work. They are not a promise that visibility or demand will rise.

## Foundation

**Draft — confirm before offering.**

A first tidy of trust signals and basic on-page items, limited to what the current checker can see and a person then reviews.

- An automated crawl of the public site, up to the page limit set when the checker is run, plus a manual review of the warnings. The checker does not replace that review.
- A short written summary of the same kind as `CLIENT-SUMMARY.md`.
- A fix list, for David or the firm to apply, covering only the items the checker already flags:
  - missing titles, or titles shorter than 10 characters or longer than 70
  - a missing H1, or more than one H1
  - a missing viewport meta tag
  - a missing canonical tag
  - no obvious contact details on a page
  - a contact URL with no form, a form with no clear action, or a form missing the usual name, email, message, or phone cues
  - no mention of insurance, public liability, or indemnity
  - no accreditation or trust mark, or only a weak mention. The checker looks for UKAS, ARCA, BOHS, IOSH, CHAS, and SafeContractor, and for stronger phrases such as "UKAS accredited" and "ARCA member"
  - possible conflicting service wording, such as asbestos removal alongside survey-only language
  - HTTP errors and pages the crawl could not read
- {{FOUNDATION_REVIEW_ROUNDS}} further look at those same items after changes are made. Set the number. Do not imply an unlimited retainer.

Wording changes are recommendations. The firm approves anything that states an insurance position, an accreditation, or a licensed service. Do not publish a claim the firm cannot evidence.

## Visibility

**Draft — confirm before offering.**

Everything in Foundation, plus on-site work for the service and location pages the crawler actually reaches.

- The same checks, reported page by page, for those service and location URLs.
- A short list of internal links to add between service pages and location pages, taken from the links the checker already collects.
- Title and H1 suggestions for those pages, so the place and the service are stated plainly.

Google Business Profile, map results, citation sites, and rank tracking are **not** things the checker does. Include them in this tier only if the manual work will really be done.

**{{VISIBILITY_INCLUDES_GBP}}** must be set to `yes` or `no`.

- `no` — this tier does not include Google Business Profile or any off-site listing.
- `yes` — describe the manual work in a sentence under this heading before the sheet is used. Do not say the checker performed it.

## Demand

**Draft — confirm before offering.**

Everything in Visibility, plus copy recommendations where the audit shows wording that is missing, conflicting, or unclear.

- Recommended page copy for up to {{DEMAND_COPY_PAGES}} pages. Set the number.
- A suggested order for those fixes.
- Extra items beyond that copy: {{DEMAND_EXTRAS}}. Write `none` if there are no extras. Do not leave this as a surprise list of backlinks, advertising, or photography unless that work is really included.

The firm approves the copy before it is published. The audit remains an automated check plus a manual review.

## Contract length

Foundation lasts {{CONTRACT_LENGTH_FOUNDATION}}. Visibility lasts {{CONTRACT_LENGTH_VISIBILITY}}. Demand lasts {{CONTRACT_LENGTH_DEMAND}}.

What happens at the end of that length: {{RENEWAL_TERMS}}. Say whether the arrangement ends, renews only if both sides agree, or continues until notice is given. Do not imply an automatic renewal unless that is the rule you will actually use.

## Notice period and how to cancel

The notice period for each tier is {{NOTICE_PERIOD}}.

Either side cancels by email.

1. The client emails {{CANCELLATION_EMAIL}}, gives the firm name, and gives the date the notice starts.
2. {{BUSINESS_NAME}} cancels in the same way, by email to the person who agreed the work.
3. The arrangement ends when {{NOTICE_PERIOD}} has run from that start date, unless {{RENEWAL_TERMS}} sets a different end.
4. Cancellation fee: {{CANCELLATION_FEE}}. Write `none` if there is no fee. Do not add a fee later that was not written here.
5. Money already paid, and work already done: {{REFUND_TERMS}}. Write the actual rule. This draft does not invent a refund position.

No cancellation is complete until the email is sent. A telephone call alone is not the cancellation method in this draft.

This sheet is not a signed agreement. Have it read before it is used with a client.
