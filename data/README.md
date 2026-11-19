# Data files

These files are empty structures. They do not contain a real firm, a real inbox, or a scraped directory.

| File | Role |
| --- | --- |
| `suppression_list.csv` | Permanent opt-out list. Append only. See `compliance/README.md`. |
| `firm_list_template.csv` | Header for a firm list. Rules in `firm_list_README.md`. |

Do not commit a filled firm list or a filled tracker if it contains live contact details. Keep working copies outside the repository, or strip them before a commit.

The suppression file is the exception: it stays in the repository, starts with a header only, and grows only when a real suppression event is recorded. Do not delete it and do not remove rows.
