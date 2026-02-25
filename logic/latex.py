"""
logic/latex.py — Determine Latex-free status from INCI name.

Returns:
  "No"  — contains latex or cross-reactive ingredient
  None  — no latex detected
"""

# ── 1. True latex sources ─────────────────────────────────────────────────────
_CONTAINS = [
    "latex",
    "natural rubber",
    "hevea brasiliensis",
    "rubber",
]

# ── 2. Cross-reactive botanical stems ────────────────────────────────────────
_CROSS_REACTIVE_STEMS = [
    # Banana
    "musa sapientum",
    "musa paradisiaca",
    "musa ",        # catches any musa species
    # Avocado
    "persea gratissima",
    "persea americana",
    "persea ",
    # Kiwi
    "actinidia chinensis",
    "actinidia deliciosa",
    "actinidia ",
    # Chestnut
    "castanea sativa",
    # Papaya
    "carica papaya",
    "papain",
]


def is_latex_free(inci_name: str) -> str | None:
    if not inci_name:
        return None

    lower = inci_name.lower()

    for term in _CONTAINS:
        if term in lower:
            return "No"

    for stem in _CROSS_REACTIVE_STEMS:
        if stem in lower:
            return "No"

    return None

