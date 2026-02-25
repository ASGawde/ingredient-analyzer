"""
logic/seafood.py — Determine Seafood-free status from INCI name.

Returns:
  "No"  — contains fish, shellfish, or marine animal ingredient
  None  — no seafood detected

Note: algae, seaweed, sea salt are NOT seafood allergens → never flagged.
"""

# Complete list of seafood-derived INCI terms
_CONTAINS = [
    # Fish
    "fish",
    "salmon",
    "salmo salar",
    "cod",
    "gadus morhua",
    "tuna",
    "thunnus",
    "anchovy",
    "engraulis",
    "caviar",
    "acipenser",
    "roe",
    "marine collagen",
    "fish collagen",
    "hydrolyzed fish collagen",
    # Shellfish
    "chitosan",
    "chitin",
    "shrimp",
    "penaeus",
    "litopenaeus",
    "crab",
    "cancer ",       # space to avoid false positive on "cancerous" etc.
    "portunus",
    "lobster",
    "homarus",
    "oyster",
    "ostrea",
    "crassostrea",
    "mussel",
    "mytilus",
    "mollusk",
]

# These look like seafood terms but are NOT allergens
_FALSE_POSITIVES = [
    "algae",
    "seaweed",
    "kelp",
    "spirulina",
    "laminaria",
    "fucus",
    "sea salt",
    "sodium chloride",
    "magnesium chloride",
]


def is_seafood_free(inci_name: str) -> str | None:
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

