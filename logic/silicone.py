"""
logic/silicone.py — Determine Silicone-free status from INCI name.

Returns:
  "No"  — ingredient contains a silicone compound
  None  — no silicone detected (possibly silicone-free, defer to SkinSafe)

Key distinction: silica/silicate are NOT silicones → never flagged.
"""

import re

# ── 1. Obvious silicone keywords ──────────────────────────────────────────────
_CONTAINS = [
    "silicone",
    "siloxane",
    "dimethicone",
    "methicone",
    "trimethicone",
    "phenyl trimethicone",
    "amodimethicone",
    "dimethiconol",
    "silicone quaternium",
    "cyclopentasiloxane",
    "cyclohexasiloxane",
    "cyclomethicone",
    "polysilicone",
    "silsesquioxane",
]

# ── 2. Silane stem (triethoxycaprylylsilane, etc.) ────────────────────────────
# Match "silan" as a word stem but NOT "silica" or "silicate"
_SILANE_PATTERN = re.compile(r'silan(?!e\s*$)', re.IGNORECASE)  # catches silane, silanol, etc.
# Actually simpler: match "silan" anywhere that isn't preceded by "sili" (silica/silicate)
_SILANE_PATTERN = re.compile(r'(?<!sili)silan', re.IGNORECASE)

# ── 3. Silicone root + crosspolymer/polymer combo ─────────────────────────────
_SILICONE_ROOTS = ["dimethicone", "siloxane", "methicone"]
_POLYMER_TERMS  = ["crosspolymer", "polymer"]

# ── 4. Terms that look like silicone but are NOT ──────────────────────────────
_FALSE_POSITIVES = [
    "silica",
    "silicate",
    "silicon dioxide",
]


def is_silicone_free(inci_name: str) -> str | None:
    """
    Evaluate Silicone-free status from the INCI name.

    Returns:
        "No"  if a silicone compound is detected
        None  if no silicone detected
    """
    if not inci_name:
        return None

    lower = inci_name.lower()

    # ── Guard: strip known false positives before checking ───────────────────
    # Replace silica/silicate with a placeholder so they don't trigger checks
    clean = lower
    for fp in _FALSE_POSITIVES:
        clean = clean.replace(fp, "")

    # ── 1 & 2 & 3 & 5 & 6: simple substring checks ───────────────────────────
    for term in _CONTAINS:
        if term in clean:
            return "No"

    # ── Silane stem ───────────────────────────────────────────────────────────
    if _SILANE_PATTERN.search(clean):
        return "No"

    # ── 4. Silicone root + crosspolymer/polymer combo ─────────────────────────
    has_root    = any(root in clean for root in _SILICONE_ROOTS)
    has_polymer = any(poly in clean for poly in _POLYMER_TERMS)
    if has_root and has_polymer:
        return "No"

    return None

