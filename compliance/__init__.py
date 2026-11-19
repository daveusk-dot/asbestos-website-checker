"""Compliance helpers for list handling. Nothing in this package sends email."""

from compliance.suppression import (
    ALLOWED_LEGAL_STATUSES,
    HEADER_LINE,
    PreSendDecision,
    SuppressionError,
    add,
    is_suppressed,
    pre_send_check,
)

__all__ = [
    "ALLOWED_LEGAL_STATUSES",
    "HEADER_LINE",
    "PreSendDecision",
    "SuppressionError",
    "add",
    "is_suppressed",
    "pre_send_check",
]
