"""
logic/vegan.py — Determine Vegan status from INCI name.

Returns:
  "No"   — contains a non-vegan ingredient
  "Yes"  — confirmed vegan (synthetic, mineral, or botanical)
  None   — ambiguous; defer to SkinSafe

Logic:
  Vegan = No if:
    1. Seafood-free = No  (fish/shellfish)
    2. Dairy-free = No
    3. Contains bee-derived ingredient
    4. Contains lanolin / wool-derived
    5. Contains animal protein (collagen, elastin, keratin, silk, etc.)
    6. Contains carmine / cochineal
    7. Contains other slaughter-derived ingredients (tallow, lard, gelatin, etc.)
"""

from logic.seafood import is_seafood_free
from logic.dairy import is_dairy_free

# ── Bee-derived ───────────────────────────────────────────────────────────────
_BEE_TERMS = [
    "honey", "mel ", "mel extract", "honey extract", "honey powder",
    "honey ferment", "hydrolyzed honey", "honey wax", "honey acid",
    "cera alba", "beeswax", "white beeswax", "yellow beeswax",
    "hydrogenated beeswax", "hydrolyzed beeswax", "beeswax acid",
    "beeswax absolute", "beeswax extract",
    "propolis", "royal jelly",
    "bee venom", "apitoxin", "apis mellifera",
    "bee pollen",
]

# ── Lanolin / wool ────────────────────────────────────────────────────────────
_LANOLIN_TERMS = [
    "lanolin", "lanolate", "laneth", "lanogene",
    "wool wax", "wool fat", "adeps lanae",
]

# ── Animal proteins ───────────────────────────────────────────────────────────
_ANIMAL_PROTEIN_TERMS = [
    "collagen", "hydrolyzed collagen", "soluble collagen",
    "elastin", "hydrolyzed elastin",
    "keratin", "hydrolyzed keratin", "wool keratin",
    "placenta", "hydrolyzed placental protein",
    "cholesterol",
    # Silk
    "silk protein", "hydrolyzed silk", "sericin", "soluble silk",
    "silk amino acids", "silk extract", "hydrolyzed sericin",
    "fibroin", "silk fibroin", "hydrolyzed fibroin",
    "bombyx",
]

# ── Carmine / cochineal ───────────────────────────────────────────────────────
_CARMINE_TERMS = [
    "carmine", "cochineal", "ci 75470", "carminic acid",
]

# ── Slaughter-derived ─────────────────────────────────────────────────────────
_SLAUGHTER_TERMS = [
    "tallow", "sodium tallowate", "adeps bovis",
    "lard", "gelatin", "hide glue",
    "mink oil", "emu oil",
    "rennet", "rennin",
    "hydrolyzed animal protein",
    "snail secretion", "snail filtrate",
    "pearl extract", "pearl powder",
    "castoreum", "ambergris", "civet", "musk",
    "shellac", "cera lacca",
]

# ── Confirmed vegan: synthetic / mineral ─────────────────────────────────────
_ALWAYS_VEGAN = [
    "synthetic wax", "candelilla", "carnauba", "sunflower wax",
    "rice bran wax", "niacinamide", "salicylic acid", "ascorbic acid",
    "phenoxyethanol", "carbomer", "propylene glycol", "butylene glycol",
    "titanium dioxide", "zinc oxide", "iron oxide", "mica", "kaolin",
    "bentonite", "silica",
]


def is_vegan(inci_name: str) -> str | None:
    if not inci_name:
        return None

    lower = inci_name.lower()

    # ── Check non-vegan triggers ──────────────────────────────────────────────
    if is_seafood_free(inci_name) == "No":
        return "No"

    if is_dairy_free(inci_name) == "No":
        return "No"

    for term in _BEE_TERMS:
        if term in lower:
            return "No"

    for term in _LANOLIN_TERMS:
        if term in lower:
            return "No"

    for term in _ANIMAL_PROTEIN_TERMS:
        if term in lower:
            return "No"

    for term in _CARMINE_TERMS:
        if term in lower:
            return "No"

    for term in _SLAUGHTER_TERMS:
        if term in lower:
            return "No"

    # ── Check confirmed vegan ─────────────────────────────────────────────────
    for term in _ALWAYS_VEGAN:
        if term in lower:
            return "Yes"

    return None

