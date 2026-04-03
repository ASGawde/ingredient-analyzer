"""
logic/age.py — Determine age range suitability from INCI name.

Age range cols (31-36):
  31: Teen
  32: 20s
  33: 30s
  34: 40s
  35: 50s
  36: 60+

Output: "Yes" (suitable) or "No" (not suitable)
Default: "Yes" for all ages if no category matches.

Exclusion rules:
  Teen → exclude A, B, C
  20s  → no exclusions
  30s  → no exclusions
  40s  → exclude D
  50s  → exclude D, E
  60+  → exclude D, E, F

Position-based rules (propylene glycol first 5, etc.) ignored 
Encoded separately from sensitivity/acne 
"""

# ── Category A: Highly comedogenic (same as acne cat A) ──────────────────────
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
    "theobroma Cacao seed butter",
    "cocoa butter",
    "hydrogenated vegetable oil",
    "lanolin",
    "beeswax",
    "cera alba",
]

# ── Category C: Prescription-strength retinoids ───────────────────────────────
_CAT_C = [
    "tretinoin",
    "adapalene",
    "tazarotene",
    "isotretinoin",
]

# ── Category D: Barrier thinners ─────────────────────────────────────────────
_CAT_D = [
    "sodium lauryl sulfate",
    "ammonium lauryl sulfate",
    "sodium tallowate",
    "sodium cocoate",
    "tea-lauryl sulfate",
    "hydrogen peroxide",
    "potassium permanganate",
    "ammonium persulfate",
]

# ── Category E: Alcohols ──────────────────────────────────────────────────────
_CAT_E = [
    "alcohol denat",
    "sd alcohol",
    "ethanol",
    "isopropyl alcohol",
]

# ── Category F: Penetration enhancers ────────────────────────────────────────
_CAT_F = [
    "ethoxydiglycol",
    "dimethyl isosorbide",
    "propylene glycol",
]

# ── Exclusion rules per age range ─────────────────────────────────────────────
_EXCLUSIONS = {
    31: {"A", "B", "C"},       # Teen
    32: set(),                 # 20s — no exclusions
    33: set(),                 # 30s — no exclusions
    34: {"D"},                 # 40s
    35: {"D", "E"},            # 50s
    36: {"D", "E", "F"},       # 60+
}

_CAT_MAP = {
    "A": _CAT_A,
    "B": _CAT_B,
    "C": _CAT_C,
    "D": _CAT_D,
    "E": _CAT_E,
    "F": _CAT_F,
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


def get_age_ratings(inci_name: str) -> dict:
    """
    Returns {col_index: "Yes"/"No"} for cols 31-36.
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