"""Append-only suppression list and pre-send eligibility check.

Nothing in this module sends email. ``add`` only appends a row.
There is no delete, update, or send function. If the list is missing or
the header is wrong, checks fail closed: do not send.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

ALLOWED_LEGAL_STATUSES = frozenset({"limited_company", "llp"})
CSV_FIELDS = ["email", "domain", "reason", "date_added", "source"]
HEADER_LINE = ",".join(CSV_FIELDS) + "\n"

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "suppression_list.csv"

_FORMULA_PREFIXES = ("=", "+", "-", "@")


class SuppressionError(Exception):
    """The suppression file or a new row cannot be used safely."""


@dataclass(frozen=True)
class PreSendDecision:
    """Result of a pre-send check. ``allowed`` false means do not send."""

    allowed: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "reasons": list(self.reasons)}


def _normalise_email(email: str | None) -> str:
    if email is None:
        return ""
    return str(email).strip().lower()


def _normalise_domain(domain: str | None) -> str:
    if domain is None:
        return ""
    value = str(domain).strip().lower()
    if value.startswith("@"):
        value = value[1:]
    return value.rstrip(".")


def _email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.rsplit("@", 1)[1]


def _validate_email(email: str) -> None:
    if not email:
        raise SuppressionError("Email is empty.")
    if "{{" in email or "}}" in email:
        raise SuppressionError("Email still contains a placeholder.")
    if any(character.isspace() for character in email):
        raise SuppressionError("Email must not contain spaces.")
    if email.count("@") != 1:
        raise SuppressionError("Email must contain one @ sign.")
    local, domain = email.split("@", 1)
    if not local or "." not in domain or ".." in email:
        raise SuppressionError("Email does not look usable.")
    if domain.startswith(".") or domain.endswith("."):
        raise SuppressionError("Email does not look usable.")
    if len(email) > 254:
        raise SuppressionError("Email is too long.")


def _validate_domain(domain: str) -> None:
    if not domain:
        raise SuppressionError("Domain is empty.")
    if any(character.isspace() for character in domain):
        raise SuppressionError("Domain must not contain spaces.")
    if "@" in domain or "/" in domain or ":" in domain:
        raise SuppressionError("Domain must be a bare domain such as example.co.uk.")
    if "." not in domain or ".." in domain or domain.startswith("."):
        raise SuppressionError("Domain does not look usable.")


def _normalise_legal_status(legal_status: str | None) -> str:
    if legal_status is None:
        return ""
    value = str(legal_status).strip().lower().replace("-", " ").replace("_", " ")
    value = "_".join(part for part in value.split() if part)
    return value


def _parse_date(value: str | None) -> str:
    if value is None or str(value).strip() == "":
        return date.today().isoformat()
    raw = str(value).strip()
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SuppressionError("date_added must be YYYY-MM-DD.") from exc
    return parsed.isoformat()


def _single_line(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise SuppressionError(f"A {label} is required.")
    if "\n" in cleaned or "\r" in cleaned:
        raise SuppressionError(f"{label} must be a single line.")
    if cleaned.startswith(_FORMULA_PREFIXES):
        cleaned = "'" + cleaned
    return cleaned


def _require_list(path: Path) -> None:
    if not path.exists():
        raise SuppressionError(
            f"Suppression list is missing at {path}. Do not send. "
            "Restore the file. Do not start a new empty list in its place."
        )
    if not path.is_file():
        raise SuppressionError(f"Suppression list path is not a file: {path}")
    text = path.read_text(encoding="utf-8")
    if text == "":
        raise SuppressionError("Suppression file is empty. It was not modified. Do not send.")
    if not text.endswith("\n"):
        raise SuppressionError(
            "Suppression file must end with a newline. It was not modified. Do not send."
        )
    header = text.splitlines()[0]
    if [cell.strip() for cell in header.split(",")] != CSV_FIELDS:
        raise SuppressionError(
            "Suppression file header is unexpected. The file was not modified. Do not send."
        )


def _read_rows(path: Path) -> list[dict[str, str]]:
    _require_list(path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SuppressionError("Suppression file has no header. Do not send.")
        fields = [name.strip() for name in reader.fieldnames]
        if fields != CSV_FIELDS:
            raise SuppressionError(
                "Suppression file header is unexpected. The file was not modified. Do not send."
            )
        rows: list[dict[str, str]] = []
        for index, row in enumerate(reader, start=2):
            cleaned = {key: (row.get(key) or "").strip() for key in CSV_FIELDS}
            if not any(cleaned.values()):
                continue
            if not cleaned["email"] and not cleaned["domain"]:
                raise SuppressionError(
                    f"Row {index} has neither email nor domain. Do not send. "
                    "The file was not modified."
                )
            rows.append(cleaned)
        return rows


def _row_matches(row: dict[str, str], email: str) -> bool:
    row_email = _normalise_email(row.get("email"))
    row_domain = _normalise_domain(row.get("domain"))
    if row_email and row_email == email:
        return True
    # A domain blocks the whole domain only when the email cell is empty.
    # A row with both cells filled suppresses that address alone.
    if not row_email and row_domain and row_domain == _email_domain(email):
        return True
    return False


def add(
    email: str | None = None,
    reason: str = "",
    source: str = "",
    domain: str | None = None,
    date_added: str | None = None,
    path: Path | str | None = None,
) -> dict[str, str]:
    """Append one suppression row. Existing rows are never rewritten or deleted."""

    list_path = Path(path) if path is not None else DEFAULT_PATH
    cleaned_email = _normalise_email(email)
    cleaned_domain = _normalise_domain(domain)
    cleaned_reason = _single_line(reason or "", "reason")
    cleaned_source = _single_line(source or "", "source")

    if not cleaned_email and not cleaned_domain:
        raise SuppressionError("Provide an email, a domain, or both.")
    if cleaned_email:
        _validate_email(cleaned_email)
        if cleaned_domain and cleaned_domain != _email_domain(cleaned_email):
            raise SuppressionError(
                "Domain does not match the email address. The row was not written."
            )
    if cleaned_domain:
        _validate_domain(cleaned_domain)

    row = {
        "email": cleaned_email,
        "domain": cleaned_domain,
        "reason": cleaned_reason,
        "date_added": _parse_date(date_added),
        "source": cleaned_source,
    }
    _require_list(list_path)
    with list_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writerow(row)
    return row


def is_suppressed(
    email: str,
    path: Path | str | None = None,
    domain: str | None = None,
) -> bool:
    """Return whether this address, or a domain-wide row, is suppressed.

    Raises ``SuppressionError`` if the list is missing or unreadable.
    A missing list is not treated as "nobody is suppressed".
    """

    list_path = Path(path) if path is not None else DEFAULT_PATH
    cleaned = _normalise_email(email)
    _validate_email(cleaned)
    extra_domain = _normalise_domain(domain) if domain else ""
    if extra_domain:
        _validate_domain(extra_domain)

    for row in _read_rows(list_path):
        if _row_matches(row, cleaned):
            return True
        if extra_domain:
            row_email = _normalise_email(row.get("email"))
            row_domain = _normalise_domain(row.get("domain"))
            if not row_email and row_domain == extra_domain:
                return True
    return False


def pre_send_check(
    email: str,
    legal_status: str | None,
    path: Path | str | None = None,
    domain: str | None = None,
) -> PreSendDecision:
    """Refuse a recipient who is suppressed or not a limited company or LLP.

    Does not send email. Any raised ``SuppressionError`` also means do not send.
    """

    reasons: list[str] = []
    cleaned = _normalise_email(email)
    try:
        _validate_email(cleaned)
    except SuppressionError as exc:
        reasons.append(f"Email is not usable: {exc}")
        cleaned = ""

    status = _normalise_legal_status(legal_status)
    if not status:
        reasons.append(
            "Legal status is missing. Cold email is allowed only after a "
            "Companies House check, and only for limited_company or llp."
        )
    elif status not in ALLOWED_LEGAL_STATUSES:
        reasons.append(
            f"Legal status '{status}' is excluded from cold email. "
            "Only limited_company and llp may be contacted. Sole traders, "
            "ordinary partnerships and unknown status are out of scope."
        )

    list_path = Path(path) if path is not None else DEFAULT_PATH
    if cleaned:
        suppressed = is_suppressed(cleaned, path=list_path, domain=domain)
        if suppressed:
            reasons.append(
                "Recipient is on the suppression list. Entries are permanent. Do not send."
            )
    else:
        # Still require a readable list, so a bad address cannot hide a missing file.
        _require_list(list_path)

    return PreSendDecision(allowed=not reasons, reasons=reasons)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance.suppression",
        description=(
            "Append-only suppression list and pre-send check. This tool does not send email."
        ),
    )
    parser.add_argument(
        "--path",
        default=str(DEFAULT_PATH),
        help="Path to the suppression CSV. Defaults to data/suppression_list.csv.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_cmd = sub.add_parser("add", help="Append one suppression row.")
    add_cmd.add_argument("--email", default="")
    add_cmd.add_argument("--domain", default="")
    add_cmd.add_argument("--reason", required=True)
    add_cmd.add_argument("--source", required=True)
    add_cmd.add_argument("--date", default="", help="YYYY-MM-DD. Defaults to today.")

    is_cmd = sub.add_parser("is-suppressed", help="Check whether an address is suppressed.")
    is_cmd.add_argument("--email", required=True)
    is_cmd.add_argument("--domain", default="")

    pre_cmd = sub.add_parser(
        "pre-send-check",
        help="Reject suppressed addresses and legal statuses other than limited_company or llp.",
    )
    pre_cmd.add_argument("--email", required=True)
    pre_cmd.add_argument("--legal-status", required=True)
    pre_cmd.add_argument("--domain", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    list_path = Path(args.path)
    try:
        if args.command == "add":
            row = add(
                email=args.email,
                domain=args.domain or None,
                reason=args.reason,
                source=args.source,
                date_added=args.date or None,
                path=list_path,
            )
            shown = row["email"] or "(domain-wide)"
            print(
                f"Appended suppression row email={shown} domain={row['domain'] or '(none)'} "
                f"date_added={row['date_added']}. Existing rows were left unchanged."
            )
            return 0
        if args.command == "is-suppressed":
            suppressed = is_suppressed(
                args.email,
                path=list_path,
                domain=args.domain or None,
            )
            print("suppressed=yes" if suppressed else "suppressed=no")
            return 1 if suppressed else 0
        if args.command == "pre-send-check":
            decision = pre_send_check(
                args.email,
                args.legal_status,
                path=list_path,
                domain=args.domain or None,
            )
            print("allowed=yes" if decision.allowed else "allowed=no")
            for reason in decision.reasons:
                print(f"reason: {reason}")
            return 0 if decision.allowed else 1
    except SuppressionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print("error: unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
