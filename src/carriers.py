"""Carrier detection and metadata helpers."""

from __future__ import annotations

import re
from typing import Iterable


_CARRIER_PATTERNS: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    (
        "顺丰",
        (
            re.compile(r"顺丰"),
            re.compile(r"\bsf\s*express\b", re.IGNORECASE),
            re.compile(r"\bsf\b", re.IGNORECASE),
        ),
    ),
    (
        "韵达",
        (
            re.compile(r"韵达"),
            re.compile(r"\byunda\b", re.IGNORECASE),
            re.compile(r"\byd\b", re.IGNORECASE),
        ),
    ),
    (
        "SPX",
        (
            re.compile(r"\bspx(?:\s+express)?\b", re.IGNORECASE),
            re.compile(r"shopee\s*express", re.IGNORECASE),
        ),
    ),
]


def detect_carrier(*texts: str | None) -> str | None:
    """Return the canonical carrier name detected from free text."""
    for text in texts:
        if not text:
            continue
        haystack = str(text)
        for carrier, patterns in _CARRIER_PATTERNS:
            if any(pattern.search(haystack) for pattern in patterns):
                return carrier
    return None


def merge_carrier_metadata(metadata: dict | None, *texts: str | None) -> dict:
    """Copy metadata and inject carrier when recognized from metadata or content."""
    merged = dict(metadata or {})
    carrier = detect_carrier(
        merged.get("carrier"),
        merged.get("company"),
        *texts,
    )
    if carrier:
        merged["carrier"] = carrier
    return merged


def carrier_patterns() -> Iterable[str]:
    """Expose canonical carrier names for diagnostics/tests."""
    return (carrier for carrier, _ in _CARRIER_PATTERNS)
