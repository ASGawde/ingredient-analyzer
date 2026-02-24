"""
enrichers/dietary_enricher.py

Responsible for cols 37–54 (18 boolean dietary/lifestyle flags).
Source: SkinSafe badges via scrapers/skinsafe.py

Values written:
  "Yes"       — badge confirmed present on SkinSafe
  "No"        — ingredient name contains known allergen keyword
  "Not found" — ingredient page not found on SkinSafe
  None/empty  — found on SkinSafe but no signal either way
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from scrapers.skinsafe import scrape_skinsafe


class DietaryEnricher(BaseEnricher):

    # Maps SkinSafe result field → column index
    _COL_MAP = {
        "vegetarian":    37,
        "vegan":         38,
        "gluten_free":   39,
        "paleo":         40,
        "unscented":     41,
        "paraben_free":  42,
        "sulphate_free": 43,
        "silicon_free":  44,
        "nut_free":      45,
        "soy_free":      46,
        "latex_free":    47,
        "sesame_free":   48,
        "citrus_free":   49,
        "dye_free":      50,
        "fragrance_free":51,
        "scent_free":    52,
        "seafood_free":  53,
        "dairy_free":    54,
    }

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}
        ss = scrape_skinsafe(ingredient_name)

        for field_name, col_idx in self._COL_MAP.items():
            value = getattr(ss, field_name, None)
            if value is not None:
                result[col_idx] = value

        return result
