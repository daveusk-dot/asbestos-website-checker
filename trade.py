"""Per-trade phrase lists. Generic checks live in audit.py.

A new trade is a JSON file in trades/. Leave a list empty when that
check does not apply: empty terminology does not cost points.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TRADES_DIR = Path(__file__).resolve().parent / "trades"

DEFAULT_SCHEMES = [
    "chas",
    "safecontractor",
    "safe contractor",
    "constructionline",
    "trustmark",
]


class TradeError(Exception):
    """The trade id or its JSON file cannot be used."""


@dataclass
class TradeProfile:
    id: str
    label: str
    key_page_patterns: list[str] = field(default_factory=list)
    ukas_terms: list[str] = field(default_factory=list)
    trade_bodies: list[dict] = field(default_factory=list)
    hse_terms: list[str] = field(default_factory=list)
    standards: list[str] = field(default_factory=list)
    general_schemes: list[str] = field(default_factory=list)
    schemes_configured: bool = True
    current_terms: list[str] = field(default_factory=list)
    outdated_patterns: list[str] = field(default_factory=list)
    removal_terms: list[str] = field(default_factory=list)
    survey_only_terms: list[str] = field(default_factory=list)


def load_trade(trade_id: str, directory: Path | None = None) -> TradeProfile:
    if not re.fullmatch(r"[a-z0-9_]+", trade_id or ""):
        raise TradeError(f"Trade id {trade_id!r} is not a file name this checker will open.")
    root = directory or TRADES_DIR
    path = root / f"{trade_id}.json"
    if not path.is_file():
        raise TradeError(
            f"No trade config for {trade_id}. Add {path.name} under {root}."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TradeError(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise TradeError(f"{path.name} must contain a JSON object.")
    accreditation = data.get("accreditation") or {}
    terminology = data.get("terminology") or {}
    conflict = data.get("service_conflict") or {}
    schemes = accreditation.get("general_schemes", DEFAULT_SCHEMES)
    outdated = terminology.get("outdated_patterns") or []
    for pattern in outdated:
        try:
            re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise TradeError(f"Bad terminology pattern {pattern!r} in {path.name}: {exc}") from exc
    return TradeProfile(
        id=str(data.get("id") or trade_id),
        label=str(data.get("label") or trade_id),
        key_page_patterns=[str(item).lower() for item in data.get("key_page_patterns") or []],
        ukas_terms=[str(item).lower() for item in accreditation.get("ukas_terms") or []],
        trade_bodies=list(accreditation.get("trade_bodies") or []),
        hse_terms=[str(item).lower() for item in accreditation.get("hse_terms") or []],
        standards=[str(item).lower() for item in accreditation.get("standards") or []],
        general_schemes=[str(item).lower() for item in schemes],
        schemes_configured=bool(schemes),
        current_terms=[str(item).lower() for item in terminology.get("current") or []],
        outdated_patterns=[str(item) for item in outdated],
        removal_terms=[str(item).lower() for item in conflict.get("removal") or []],
        survey_only_terms=[str(item).lower() for item in conflict.get("survey_only") or []],
    )
