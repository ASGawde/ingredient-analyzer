"""
logic/acne.py — Determine acne-prone suitability from INCI name.

Acne-prone levels (cols 25-30):
  25: Not acne prone
  26: A little acne-prone
  27: Moderately acne-prone
  28: Acne-prone
  29: Very acne-prone
  30: Extremely acne-prone

Output: "Yes" (suitable) or "No" (not suitable)
Default: "Yes" for all levels if no category matches.

Exclusion rules:
  Not acne-prone        → no exclusions
  A little acne-prone   → exclude A
  Moderately acne-prone → exclude A, B
  Acne-prone            → exclude A, B, C
  Very acne-prone       → exclude A, B, C, E
  Extremely acne-prone  → exclude A, B, C, D, E

Position-based rules (Dimethicone/Trimethicone first 5) ignored 
"""

# ── Category A: Highly comedogenic ───────────────────────────────────────────
_CAT_A = [
    "isopropyl myristate",
    "isopropyl palmitate",
    "myristyl myristate",
    "isocetyl stearate",
    "octyl palmitate",
    "butyl stearate",
    "laureth-4",
    "oleth-3",
    "wheat germ oil",
    "coconut oil",
    "cocos nucifera oil",
    "triticum vulgare germ oil",
]

# ── Category B: Heavy occlusives / plant butters ──────────────────────────────
_CAT_B = [
    "shea butter",
    "butyrospermum parkii butter",
    "mango butter",
    "mangifera indica seed butter",
    "illipe butter",
    "shorea stenoptera seed butter",
    "theobroma cacao seed butter",
    "cocoa butter",
    "hydrogenated vegetable oil",
    "lanolin",
    "beeswax",
    "cera alba",
]

# ── Category C: Fatty acids / emollients ─────────────────────────────────────
_CAT_C = [
    "ethylhexyl palmitate",
    "cetearyl ethylhexanoate",
    "glyceryl stearate",
    "peg-100 stearate",
    "oleyl alcohol",
    "isopropyl isostearate",
    "cetyl palmitate",
]

# ── Category E: Algae extracts ────────────────────────────────────────────────
_CAT_E = [
    "algae extract",
    "laminaria digitata extract",
    "chlorella extract",
    "spirulina extract",
]

# ── Exclusion rules per acne level ────────────────────────────────────────────
# Note: Category D (Dimethicone/Trimethicone) is position-based —
# only flagged if among first 5 ingredients in a formula.
# This cannot be determined at the ingredient level. Excluded from logic.

_EXCLUSIONS = {
    25: set(),               # Not acne-prone
    26: {"A"},               # A little acne-prone
    27: {"A", "B"},          # Moderately acne-prone
    28: {"A", "B", "C"},     # Acne-prone
    29: {"A", "B", "C", "E"},# Very acne-prone
    30: {"A", "B", "C", "E"},# Extremely acne-prone (D excluded — position-based)
}

_CAT_MAP = {
    "A": _CAT_A,
    "B": _CAT_B,
    "C": _CAT_C,
    "E": _CAT_E,
}


def _get_categories(inci_name: str) -> set:
    if not inci_name:
        return set()

    lower = inci_name.lower()
    cats = set()

    for cat, terms in _CAT_MAP.items():
        for term in terms:
            if term in lower:
                cats.add(cat)
                break

    return cats


def get_acne_ratings(inci_name: str) -> dict:
    """
    Returns {col_index: "Yes"/"No"} for cols 25-30.
    Defaults to all Yes if no category matches.
    """
    cats = _get_categories(inci_name)

    if not cats:
        return {col: "Yes" for col in _EXCLUSIONS}

    result = {}
    for col_idx, excluded_cats in _EXCLUSIONS.items():
        if cats & excluded_cats:
            result[col_idx] = "No"
        else:
            result[col_idx] = "Yes"

    return result