"""
logic/dairy.py — Determine Dairy-free status from INCI name.

Returns:
  "No"  — contains dairy-derived ingredient
  None  — no dairy detected

Note: lactic acid, sodium lactate, lactate, lactylate are fermentation-derived
and do NOT trigger dairy flag.
"""

_CONTAINS = [
    "milk",
    " lac ",         # space-padded to avoid "lactic", "lactate", "black", etc.
    "lac extract",
    "milk extract",
    "milk protein",
    "hydrolyzed milk protein",
    "casein",
    "sodium caseinate",
    "calcium caseinate",
    "whey",
    "lactoglobulin",
    "lactalbumin",
    "yogurt",
    "yoghurt",
    "buttermilk",
    "cream",
    "caseinate",
    "caprae lac",
    "goat milk",
    "donkey milk",
    "mare milk",
    "sheep milk",
    "fermented milk",
    "milk ferment",
    "colostrum",
    "ghee",
    "butter",
    "butyrum",
    "lactoferrin",
    "lactoperoxidase",
]

# These contain "lac" or "lact" but are NOT dairy
_FALSE_POSITIVES = [
    "lactic acid",
    "sodium lactate",
    "lactate",
    "lactylate",
    "polylactic",
    "lactobacillus",
    "black",
    "lactose",      # lactose itself is ambiguous but listed as dairy-free safe
]


def is_dairy_free(inci_name: str) -> str | None:
    if not inci_name:
        return None

    lower = inci_name.lower()

    # Remove false positives before checking
    clean = lower
    for fp in _FALSE_POSITIVES:
        clean = clean.replace(fp, "")

    for term in _CONTAINS:
        if term in clean:
            return "No"

    return None

