"""
logic/sensitivity.py — Determine skin sensitivity suitability from INCI name.

Sensitivity levels (cols 19-24):
  19: Not sensitive
  20: A little sensitive
  21: Moderately sensitive
  22: Sensitive
  23: Very sensitive
  24: Extremely sensitive

Output: "Yes" (suitable) or "No" (not suitable) or None (unknown)

Category exclusion rules:
  Not sensitive        → allow A,B,C,D,E,F  (no exclusions)
  A little sensitive   → exclude A, F
  Moderately sensitive → exclude A, C, F
  Sensitive            → exclude A, C, E, F
  Very sensitive       → exclude A, C, D, E, F
  Extremely sensitive  → exclude A, B, C, D, E, F

Position-based rules (first 5/10 ingredients) are ignored —
all ingredients flagged unconditionally per Yuliya's instruction.
"""

# ── Category A: Strong irritants ──────────────────────────────────────────────
_CAT_A = [
    "benzoyl peroxide",
    "glycolic acid",
    "lactic acid",
    "mandelic acid",
    "salicylic acid",
    "betaine salicylate",
    "gluconolactone",
    "lactobionic acid",
    "trichloroacetic acid",
    "phenol",
    "resorcinol",
    "sulfur",
    "selenium sulfide",
    "potassium hydroxide",
    "sodium hydroxide",
    "urea",
    "tretinoin",
    "adapalene",
    "tazarotene",
    "isotretinoin",
    "sodium lauryl sulfate",
    "ammonium lauryl sulfate",
    "sodium tallowate",
    "sodium cocoate",
    "hydrogen peroxide",
    "potassium permanganate",
    "ammonium persulfate",
    "hydroquinone",
    "monobenzone",
    "capsaicin",
    "methyl salicylate",
    "camphor",
]

# ── Category B: Fragrance and volatile irritants ──────────────────────────────
_CAT_B = [
    "parfum",
    "fragrance",
    "limonene",
    "linalool",
    "eugenol",
    "citral",
    "geraniol",
    "menthol",
    "peppermint oil",
    "eucalyptus oil",
    "benzyl alcohol",
    "benzyl salicylate",
    "benzyl benzoate",
    "cinnamal",
    "cinnamyl alcohol",
    "coumarin",
    "farnesol",
    "hexyl cinnamal",
    "isoeugenol",
    "amyl cinnamal",
    "hydroxycitronellal",
    "anise alcohol",
    # Citrus peel oils
    "citrus limon peel oil",
    "citrus aurantium dulcis peel oil",
    "citrus paradisi peel oil",
    "citrus bergamia peel oil",
    "citrus aurantifolia peel oil",
    # Essential oils by botanical name
    "lavandula angustifolia oil",
    "lavandula hybrida oil",
    "rosa damascena flower oil",
    "cananga odorata flower oil",
    "eugenia caryophyllus bud oil",
    "cinnamomum zeylanicum bark oil",
    "melaleuca alternifolia leaf oil",
    "mentha piperita oil",
    "mentha spicata oil",
    "thymus vulgaris oil",
    "rosmarinus officinalis leaf oil",
    # Common name oils
    "lavender oil",
    "ylang ylang oil",
    "rose oil",
    "jasmine oil",
    "clove oil",
    "cinnamon oil",
    "tea tree oil",
    "spearmint oil",
    "wintergreen oil",
    "thyme oil",
    "rosemary oil",
]

# ── Category C: Alcohol and barrier disruptors ────────────────────────────────
_CAT_C = [
    "alcohol denat",
    "sd alcohol",
    "isopropyl alcohol",
    "sodium lauryl sulfate",
    "ammonium lauryl sulfate",
    "sodium myreth sulfate",
    "tea-lauryl sulfate",
]

# ── Category D: Strong actives ────────────────────────────────────────────────
_CAT_D = [
    "retinol",
    "retinaldehyde",
    "retinyl palmitate",
    "retinyl acetate",
    "glycolic acid",
    "lactic acid",
    "mandelic acid",
    "salicylic acid",
    "betaine salicylate",
    "tartaric acid",
    "malic acid",
    "citric acid",
    "ascorbic acid",
    "l-ascorbic acid",
]

# ── Category E: Penetration enhancers ────────────────────────────────────────
_CAT_E = [
    "propylene glycol",
    "ethoxydiglycol",
    "dimethyl isosorbide",
]

# ── Category F: Preservatives ─────────────────────────────────────────────────
_CAT_F = [
    "methylisothiazolinone",
    "methylchloroisothiazolinone",
    "benzisothiazolinone",
    "octylisothiazolinone",
    "benzalkonium chloride",
    "dmdm hydantoin",
    "imidazolidinyl urea",
    "diazolidinyl urea",
    "quaternium-15",
    "bronopol",
    "2-bromo-2-nitropropane-1,3-diol",
    "sodium hydroxymethylglycinate",
]

# ── Additional pattern checks ─────────────────────────────────────────────────
import re

# Citrus + peel oil pattern
_CITRUS_PEEL_PATTERN = re.compile(
    r'citrus.*(peel|zest)\s*oil', re.IGNORECASE
)
# Mentha + oil pattern
_MENTHA_PATTERN = re.compile(r'mentha.*oil', re.IGNORECASE)


def _get_categories(inci_name: str) -> set:
    """Return the set of irritant categories this ingredient belongs to."""
    if not inci_name:
        return set()

    lower = inci_name.lower()
    cats = set()

    for term in _CAT_A:
        if term in lower:
            cats.add("A")
            break

    for term in _CAT_B:
        if term in lower:
            cats.add("B")
            break
    if not "B" in cats:
        if _CITRUS_PEEL_PATTERN.search(inci_name):
            cats.add("B")
        elif _MENTHA_PATTERN.search(inci_name):
            cats.add("B")

    for term in _CAT_C:
        if term in lower:
            cats.add("C")
            break

    for term in _CAT_D:
        if term in lower:
            cats.add("D")
            break

    for term in _CAT_E:
        if term in lower:
            cats.add("E")
            break

    for term in _CAT_F:
        if term in lower:
            cats.add("F")
            break

    return cats


# ── Exclusion rules per sensitivity level ────────────────────────────────────
_EXCLUSIONS = {
    19: set(),                          # Not sensitive        — no exclusions
    20: {"A", "F"},                     # A little sensitive
    21: {"A", "C", "F"},                # Moderately sensitive
    22: {"A", "C", "E", "F"},           # Sensitive
    23: {"A", "C", "D", "E", "F"},      # Very sensitive
    24: {"A", "B", "C", "D", "E", "F"}, # Extremely sensitive
}


def get_sensitivity_ratings(inci_name: str) -> dict:
    """
    Returns a dict of {col_index: "Yes"/"No"} for cols 19-24.
    Only returns values when the ingredient is in a known category.
    If the ingredient has no irritant categories, returns empty dict
    (SkinSafe or other sources will fill in).
    """
    cats = _get_categories(inci_name)

    if not cats:
        return {}   # No opinion — defer to other sources

    result = {}
    for col_idx, excluded_cats in _EXCLUSIONS.items():
        if cats & excluded_cats:
            result[col_idx] = "No"   # At least one of its categories is excluded
        else:
            result[col_idx] = "Yes"  # All its categories are allowed

    return result
