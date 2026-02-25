"""
logic/sesame.py — Determine Sesame-free status from INCI name.

Returns:
  "No"  — contains sesame-derived ingredient
  None  — no sesame detected
"""

_CONTAINS = [
    "sesamum",
    "sesame",
]


def is_sesame_free(inci_name: str) -> str | None:
    if not inci_name:
        return None

    lower = inci_name.lower()

    for term in _CONTAINS:
        if term in lower:
            return "No"

    return None

