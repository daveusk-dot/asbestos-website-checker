"""Per-niche configuration.

Everything that is specific to one trade (which accreditations to look for, which
things a site should mention, which wording clashes) lives in a YAML file in the
`niches/` folder, so the crawler and checks stay generic.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml

NICHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niches")


class NicheConfigError(ValueError):
    """Raised when a niche file is missing or invalid."""


@dataclass
class Thresholds:
    title_min: int = 10
    title_max: int = 70
    description_min: int = 50
    description_max: int = 160
    thin_content_words: int = 150


@dataclass
class TrustMarks:
    label: str = "accreditation"
    strong: List[str] = field(default_factory=list)   # wording that clearly states a claim
    weak: List[str] = field(default_factory=list)     # bare names that are only a hint
    advice_missing: str = "Show your accreditations and memberships on every service page."
    advice_weak: str = "Use specific wording, e.g. 'X accredited' or 'member of X'."


@dataclass
class RequiredMention:
    id: str
    label: str
    terms: List[str]
    advice: str = ""


@dataclass
class Conflict:
    id: str
    label: str
    message: str
    a: List[str]
    b: List[str]
    advice: str = ""


@dataclass
class Niche:
    id: str = "generic"
    name: str = "Generic trade website"
    thresholds: Thresholds = field(default_factory=Thresholds)
    trust_marks: Optional[TrustMarks] = None
    required_mentions: List[RequiredMention] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)


_TOP_KEYS = {"id", "name", "thresholds", "trust_marks", "required_mentions", "conflicts"}


def _terms(value, where):
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v.strip() for v in value):
        raise NicheConfigError(f"{where} must be a non-empty list of words/phrases")
    return [v.strip().lower().replace("-", " ") for v in value]


def _check_keys(data, allowed, where):
    unknown = set(data) - set(allowed)
    if unknown:
        raise NicheConfigError(f"{where}: unknown key(s) {sorted(unknown)} (allowed: {sorted(allowed)})")


def _parse(data, default_id):
    if not isinstance(data, dict):
        raise NicheConfigError("niche file must contain a YAML mapping")
    _check_keys(data, _TOP_KEYS, "niche file")

    niche = Niche(id=str(data.get("id", default_id)), name=str(data.get("name", default_id)))

    if "thresholds" in data:
        t = data["thresholds"] or {}
        _check_keys(t, Thresholds.__dataclass_fields__, "thresholds")
        for key, val in t.items():
            if not isinstance(val, int) or val < 0:
                raise NicheConfigError(f"thresholds.{key} must be a non-negative whole number")
        niche.thresholds = Thresholds(**t)

    if data.get("trust_marks"):
        tm = data["trust_marks"]
        _check_keys(tm, TrustMarks.__dataclass_fields__, "trust_marks")
        strong = _terms(tm["strong"], "trust_marks.strong") if tm.get("strong") else []
        weak = _terms(tm["weak"], "trust_marks.weak") if tm.get("weak") else []
        if not strong and not weak:
            raise NicheConfigError("trust_marks needs at least one of 'strong' or 'weak'")
        niche.trust_marks = TrustMarks(
            label=str(tm.get("label", "accreditation")),
            strong=strong,
            weak=weak,
            advice_missing=str(tm.get("advice_missing", TrustMarks.advice_missing)),
            advice_weak=str(tm.get("advice_weak", TrustMarks.advice_weak)),
        )

    seen_ids = set()
    for i, rm in enumerate(data.get("required_mentions") or []):
        where = f"required_mentions[{i}]"
        _check_keys(rm, RequiredMention.__dataclass_fields__, where)
        for key in ("id", "label", "terms"):
            if key not in rm:
                raise NicheConfigError(f"{where} is missing '{key}'")
        if rm["id"] in seen_ids:
            raise NicheConfigError(f"{where}: duplicate id '{rm['id']}'")
        seen_ids.add(rm["id"])
        niche.required_mentions.append(RequiredMention(
            id=str(rm["id"]), label=str(rm["label"]),
            terms=_terms(rm["terms"], f"{where}.terms"), advice=str(rm.get("advice", "")),
        ))

    for i, c in enumerate(data.get("conflicts") or []):
        where = f"conflicts[{i}]"
        _check_keys(c, Conflict.__dataclass_fields__, where)
        for key in ("id", "label", "message", "a", "b"):
            if key not in c:
                raise NicheConfigError(f"{where} is missing '{key}'")
        niche.conflicts.append(Conflict(
            id=str(c["id"]), label=str(c["label"]), message=str(c["message"]),
            a=_terms(c["a"], f"{where}.a"), b=_terms(c["b"], f"{where}.b"),
            advice=str(c.get("advice", "")),
        ))

    return niche


def list_niches():
    """Names of the niche files that ship in the niches/ folder (templates excluded)."""
    if not os.path.isdir(NICHE_DIR):
        return []
    return sorted(
        os.path.splitext(f)[0] for f in os.listdir(NICHE_DIR)
        if f.endswith((".yaml", ".yml")) and not f.startswith("_")
    )


def load_niche(spec=None):
    """Load a niche by name (niches/<name>.yaml), by path to a YAML file, or the generic default."""
    if spec is None or spec == "generic":
        return Niche()

    candidates = [spec]
    for ext in (".yaml", ".yml"):
        candidates.append(os.path.join(NICHE_DIR, spec + ext))
    path = next((p for p in candidates if os.path.isfile(p)), None)
    if path is None:
        available = ", ".join(list_niches()) or "none"
        raise NicheConfigError(f"Niche '{spec}' not found. Available: {available}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise NicheConfigError(f"{path}: invalid YAML: {e}")

    default_id = os.path.splitext(os.path.basename(path))[0]
    try:
        return _parse(data, default_id)
    except NicheConfigError as e:
        raise NicheConfigError(f"{path}: {e}")
