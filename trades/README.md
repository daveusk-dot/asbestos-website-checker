# Trade configs

`asbestos_surveying.json` is the phrase list for UK asbestos surveyors. The checker loads `trades/<trade>.json`. Generic checks (HTTPS, contact, insurance types, company number, NAP, schema) always run. The file only changes the trade-specific phrases.

To add a trade, copy the asbestos file and edit it. Use a lower-case id such as `gas` or `electrical`. In a tracker CSV, put that id in the `trade` column, or pass `--trade gas`.

Leave a list empty when it does not apply. Empty terminology, UKAS terms, trade bodies, standards, or HSE terms score as "not used for this trade" and do not reduce the mark. An empty `general_schemes` list does the same. If `general_schemes` is omitted, the construction schemes (CHAS, SafeContractor, Constructionline, TrustMark) are used.

`key_page_patterns` are matched against the page path. Accreditation and insurance are scored once for the whole site. When those paths exist and never mention the item, the report says so.

`service_conflict` is a pair of phrase lists. A page that contains one phrase from each list is reported as conflicting wording.
