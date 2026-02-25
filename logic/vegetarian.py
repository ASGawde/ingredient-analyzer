"""
logic/vegetarian.py — Determine Vegetarian status from INCI name.

Returns:
  "No"   — contains a non-vegetarian ingredient (slaughter/fish/insect derived)
  None   — ambiguous or vegetarian-acceptable; defer to SkinSafe

Logic:
  Vegetarian = Vegan + allowed exceptions (dairy, eggs, bee products, lanolin)
  So Vegetarian = No only for things that are ALSO non-vegan AND
  come from slaughtered animals, fish, shellfish, or insects.
  Dairy, eggs, bee products, and lanolin are vegetarian-acceptable.
"""

from logic.seafood import is_seafood_free

# ── Confirmed vegetarian (not vegan but vegetarian-acceptable) ────────────────
_VEGETARIAN_YES = [
    # Bee products
    "honey", "mel ", "beeswax", "cera alba", "cera flava",
    "propolis", "royal jelly", "bee pollen", "bee venom", "apis mellifera",
    # Dairy
    "milk", "casein", "caseinate", "whey", "lactalbumin", "lactoglobulin",
    "lactoferrin", "lactoperoxidase", "lactose", "colostrum", "ghee",
    "butter", "butyrum", "buttermilk", "cream", "yogurt", "yoghurt",
    # Eggs
    "albumen", "albumin", "egg protein", "ovalbumin",
    # Lanolin (from living sheep)
    "lanolin", "lanolate", "laneth", "wool wax", "wool fat", "adeps lanae",
]

# ── From slaughtered animals ──────────────────────────────────────────────────
_SLAUGHTER_TERMS = [
    "collagen", "hydrolyzed collagen", "soluble collagen",
    "elastin", "hydrolyzed elastin",
    "keratin", "hydrolyzed keratin",
    "tallow", "sodium tallowate", "adeps bovis",
    "lard",
    "gelatin", "hide glue",
    "mink oil", "emu oil",
    "placenta", "hydrolyzed placental protein",
    "rennet", "rennin",
    "hydrolyzed animal protein",
    "blood", "bone char", "bone meal",
    "catgut",
    "snail secretion", "snail filtrate",
    "castoreum", "ambergris", "civet",
    "turtle oil", "sea turtle oil",
    "spermaceti", "sperm oil", "shark liver oil",
]

# ── Insect-derived (non-vegetarian) ──────────────────────────────────────────
_INSECT_TERMS = [
    "carmine", "cochineal", "ci 75470", "carminic acid",
    "shellac", "cera lacca", "resinous glaze",
]

# ── Silk (from silkworm — insect) ─────────────────────────────────────────────
_SILK_TERMS = [
    "silk protein", "hydrolyzed silk", "sericin", "soluble silk",
    "silk amino acids", "silk extract", "hydrolyzed sericin",
    "fibroin", "silk fibroin", "hydrolyzed fibroin",
    "bombyx",
]

# ── Pearl / coral / sponge ────────────────────────────────────────────────────
_OTHER_ANIMAL_TERMS = [
    "pearl extract", "pearl powder",
    "coral", "corallina",
    "sponge",
]


def is_vegetarian(inci_name: str) -> str | None:
    if not inci_name:
        return None

    lower = inci_name.lower()

    # Fish and shellfish = non-vegetarian
    if is_seafood_free(inci_name) == "No":
        return "No"

    for term in _SLAUGHTER_TERMS:
        if term in lower:
            return "No"

    for term in _INSECT_TERMS:
        if term in lower:
            return "No"

    for term in _SILK_TERMS:
        if term in lower:
            return "No"

    for term in _OTHER_ANIMAL_TERMS:
        if term in lower:
            return "No"

    # Confirmed vegetarian-acceptable
    for term in _VEGETARIAN_YES:
        if term in lower:
            return "Yes"

    return None

