# Twenty-firm asbestos audit test

`audit_test_asbestos_20.csv` has 20 empty slots. `test_slot` is 1 to 20 and `trade` is `asbestos_surveying` so the sheet is not reused for another audience by mistake. Every other cell is blank. There are no real firms in the file.

The test is a manual process. This repository does not build the list, does not look up Companies House, and does not send the email.

## Process

1. **Build the list from public directories.** Take asbestos firms only, from UKAS and ATaC directories you have actually opened. Record `firm_name`, `website`, `source_directory`, and a published work contact. Do not buy a list and do not guess an email address. Stop at 20 slots. Leave a slot unused rather than padding it.
2. **Check legal status at Companies House.** Fill `legal_status` with `limited_company`, `llp`, `sole_trader`, `ordinary_partnership`, or `unknown`, using the rules in `firm_list_README.md`. Sole traders, ordinary partnerships, and unknown status are excluded from cold email under this project's PECR rule. Set `eligible_for_cold_email` to `no` for those rows. Do not invent a company number.
3. **Run the checker.** Use the existing `checker.py` against `website`. Do not change the checker to produce a score. It prints `total_warnings`.
4. **Review the output by hand.** Set `manual_review_done` to `yes` only after a person has read the warnings. Correct anything the checker overstated before it is written into an email. Set `audit_run_date` to the date of the crawl (`YYYY-MM-DD`).
5. **Check suppression.** Run `python -m compliance.suppression pre-send-check` with the work address and the legal status. If it does not print `allowed=yes`, do not send. Set `eligible_for_cold_email` to `no` and record the reason in `notes`.
6. **Send by hand.** Only for rows that passed step 5, and only with a template from `outreach/asbestos/` whose placeholders are filled, including one real finding. Put the send date in `sent_date`. This repository has no send command.
7. **Record the result.** Use `replies`, `outcome`, and `notes`. Leave `opens` blank. This project does not track opens, and a hidden tracking pixel is not part of the test. Record an open only if a method has been described in the privacy notice.

## Fields

| Field | How to fill it |
| --- | --- |
| `test_slot` | 1 to 20. Already filled. |
| `firm_name` | Registered or directory name. Blank until you have it. |
| `website` | The site you audited. |
| `trade` | `asbestos_surveying` on every row. |
| `source_directory` | UKAS, ATaC, or the exact page used. This feeds `{{SOURCE_DIRECTORY}}`. |
| `contact_name` | Only if published. Otherwise blank, and the email greeting is `Hello,`. |
| `contact_email` | Published work address. |
| `legal_status` | From Companies House. See the allowed values in `firm_list_README.md`. |
| `eligible_for_cold_email` | `yes` or `no` after the pre-send check. Blank means not checked. A `yes` does not replace running the check again at send time. |
| `audit_run_date` | Date the checker was run. |
| `audit_score` | Put `total_warnings` from the checker here unless a different figure is defined later. The checker does not calculate a score. |
| `manual_review_done` | `yes` or `no`. |
| `sent_date` | Date the first email was actually sent. Blank if not sent. |
| `opens` | Leave blank. |
| `replies` | A short note of what came back, or `none`. Do not paste a long thread. |
| `outcome` | One of `no_send`, `sent_no_reply`, `replied_interested`, `replied_not_interested`, `opted_out`, `bounced`, `suppressed_before_send`, `skipped_legal_status`. |
| `notes` | Anything the next send needs to know. No special-category data. |

## After a reply or an opt-out

Stop that firm's sequence at once. Do not send the follow-up.

If they opted out, or objected, or the address hard-bounced, append the address to `data/suppression_list.csv`. Do not delete the row afterwards. Set `outcome` to `opted_out` or `bounced`.

The point of the 20 is to see whether the data, the finding, and the opt-out path work. It is not a target for a reply rate.
