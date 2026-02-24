"""
logic/paleo.py — Determine Paleo status from INCI name alone.

Returns:
  "No"  — ingredient is definitively NOT Paleo (rule matched)
  None  — no rule matched; defer to SkinSafe badge or leave blank
"""

import re

# ── Rule sets (all checks are case-insensitive) ───────────────────────────────

# 1. Ethoxylated / PEG / PPG
_CONTAINS_NOT_PALEO = [
    "peg",
    "ppg",
    "acrylate",
    "acrylates",
    "methacrylate",
    "carbomer",
    "dimethicone",
    "siloxane",
    "silicone",
    "polymer",
    "copolymer",
    "crosspolymer",
    "polyquaternium",
    "pvp",
    "vp/",
    "petrolatum",
    "mineral oil",
    "paraffin",
    "edta",
    "bht",
    "bha",
    "fragrance",
    "parfum",
    "aroma",
]

# Ends in or contains "-eth" (Laureth, Ceteareth, Oleth, etc.)
# Matches: -eth, eth- (prefix), or any word ending in "eth" (laurETH, cetearETH)
_ETH_PATTERN = re.compile(r'-eth\b|\beth-|\w+eth\b', re.IGNORECASE)


def is_paleo(inci_name: str) -> str | None:
    """
    Evaluate Paleo status from the INCI name.

    Args:
        inci_name: The INCI name string (e.g. "SODIUM LAURETH SULFATE")

    Returns:
        "No"  if any NOT-Paleo rule fires
        None  if no rule matched (unknown / possibly Paleo)
    """
    if not inci_name:
        return None

    lower = inci_name.lower()

    # Substring checks
    for term in _CONTAINS_NOT_PALEO:
        if term in lower:
            return "No"

    # -eth pattern (Laureth, Ceteareth, Steareth, Oleth, etc.)
    if _ETH_PATTERN.search(inci_name):
        return "No"

    return None

