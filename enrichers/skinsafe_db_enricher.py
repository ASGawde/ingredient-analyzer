"""
enrichers/skinsafe_db_enricher.py

Fast lookup enricher using the pre-scraped SkinSafe database CSV.

Priority:
  1. SkinSafe DB says Yes  → Yes
  2. Ingredient name contains known bad keyword → No
  3. SkinSafe DB says No (no keyword match) → Yes (assume safe)

Populates cols 37-54 (dietary/lifestyle flags) and col 31 (teen_safe).
"""

import os
import csv
import re
from typing import Dict, Any, Optional

from .base_enricher import BaseEnricher

# ── Name-based rules ───────────────────────────────────────────────────────────
NAME_CONTAINS_NO = {
    "gluten_free":    ["wheat", "barley", "gluten", "triticum", "oat",
                       "avena", "hordeum", "secale"],
    "nut_free":       ["almond", "walnut", "hazelnut", "cashew", "pistachio",
                       "macadamia", "jojoba", "pecan", "prunus amygdalus",
                       "juglans", "corylus", "anacardium", "pistacia"],
    "soy_free":       ["soy", "soja", "glycine soja", "glycine max"],
    "dairy_free":     ["milk", "lactose", "casein", "whey", "lacto",
                       "bovine", "lac "],
    "sesame_free":    ["sesame", "sesamum"],
    "citrus_free":    ["citrus", "lemon", "orange", "grapefruit", "lime",
                       "bergamot", "tangerine", "reticulata", "limon",
                       "aurantium", "grandis", "sinensis"],
    "seafood_free":   ["fish", "marine", "seaweed", "algae", "salmon",
                       "chitosan", "chondrus", "carrageenan", "agar",
                       "kelp", "laminaria", "fucus"],
    "fragrance_free": ["fragrance", "parfum", "perfume", "aroma"],
    "silicon_free":   ["silicone", "dimethicone", "cyclomethicone",
                       "siloxane", "trimethicone"],
    "sulphate_free":  ["sodium lauryl sulfate", "sodium laureth sulfate",
                       "ammonium lauryl sulfate"],
    "latex_free":     ["latex", "hevea"],
    "vegan":          ["honey", "beeswax", "cera alba", "lanolin",
                       "collagen", "keratin", "silk", "carmine",
                       "gelatin", "casein", "whey", "shellac", "squalene"],
    "vegetarian":     ["carmine", "gelatin", "tallow", "lard",
                       "animal fat", "bone"],
}

# Map from DB column name → schema column index
BADGE_TO_COL = {
    "irritant_free":  None,   # not a direct col, used for irritancy logic
    "teen_safe":      31,     # Teen col
    "fragrance_free": 50,
    "paraben_free":   41,
    "gluten_free":    39,
    "soy_free":       45,
    "nut_free":       44,
    "dairy_free":     53,
    "dye_free":       49,
    "silicon_free":   43,
    "sulphate_free":  42,
    "latex_free":     46,
    "sesame_free":    47,
    "citrus_free":    48,
    "seafood_free":   52,
    "vegan":          38,
    "vegetarian":     37,
    "paleo":          40,
    "unscented":      None,   # not a separate col in schema
    "scent_free":     51,
}


def _load_db() -> Dict[str, Dict]:
    """Load skinsafe_badges_all.csv into a dict keyed by normalized name."""
    db = {}
    csv_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "skinsafe_db.csv")
    )
    if not os.path.exists(csv_path):
        print(f"[SkinSafeDBEnricher] WARNING: {csv_path} not found — falling back to live scraper")
        return db

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("ingredient_name", "").strip()
            if not name:
                continue
            key = re.sub(r"[\s\-]+", " ", name.lower())
            db[key] = dict(row)

    print(f"[SkinSafeDBEnricher] Loaded {len(db)} ingredients from skinsafe_db.csv")
    return db


_DB = _load_db()


def _apply_name_logic(ingredient_name: str, badges: Dict[str, str]) -> Dict[str, str]:
    """
    For any badge that SkinSafe returned No, check ingredient name.
    If name contains a bad keyword → keep No.
    If no bad keyword → flip to Yes (assume safe).
    """
    name_lower = ingredient_name.lower()
    result = {}

    for badge, value in badges.items():
        if value == "Yes":
            result[badge] = "Yes"
        else:
            # Check name-based rules
            keywords = NAME_CONTAINS_NO.get(badge, [])
            if any(kw in name_lower for kw in keywords):
                result[badge] = "No"
            else:
                result[badge] = "Yes"  # assume safe

    return result


class SkinSafeDBEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(
        self,
        ingredient_name: str,
        inci_name: str,
        role: Optional[str] = None,
    ) -> Dict[int, Any]:

        # Try lookup by ingredient name and INCI name
        record = None
        for name in [ingredient_name, inci_name]:
            key = re.sub(r"[\s\-]+", " ", name.strip().lower())
            if key in _DB:
                record = _DB[key]
                break

        if not record:
            # Not in DB — apply name-based logic directly, default all to No
            # then flip to Yes where name has no bad keyword
            badges = {badge: "No" for badge in BADGE_TO_COL}
            badges = _apply_name_logic(ingredient_name, badges)
            result: Dict[int, Any] = {}
            for badge, col_idx in BADGE_TO_COL.items():
                if col_idx is not None:
                    result[col_idx] = badges.get(badge, "Yes")
            return result

        # Extract badges
        badges = {
            badge: record.get(badge, "No")
            for badge in BADGE_TO_COL
        }

        # Apply name-based logic on No values
        badges = _apply_name_logic(ingredient_name, badges)

        # Map to schema column indices
        result: Dict[int, Any] = {}
        for badge, col_idx in BADGE_TO_COL.items():
            if col_idx is not None:
                result[col_idx] = badges.get(badge, "Yes")

        return result