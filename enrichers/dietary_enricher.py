"""
enrichers/dietary_enricher.py
Responsible for cols 37–54 (18 dietary/lifestyle flags).

Priority per field:
  1. Logic modules  — rule-based on INCI name, wins if it returns a value
  2. SkinSafe badge — used when logic has no opinion
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from scrapers.skinsafe import scrape_skinsafe
from logic.paleo import is_paleo


_COL_MAP = {
    "vegetarian":     37,
    "vegan":          38,
    "gluten_free":    39,
    "paleo":          40,
    "unscented":      41,
    "paraben_free":   42,
    "sulphate_free":  43,
    "silicon_free":   44,
    "nut_free":       45,
    "soy_free":       46,
    "latex_free":     47,
    "sesame_free":    48,
    "citrus_free":    49,
    "dye_free":       50,
    "fragrance_free": 51,
    "scent_free":     52,
    "seafood_free":   53,
    "dairy_free":     54,
}


class DietaryEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # Without INCI name, use ingredient_name as fallback for logic
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # ── Step 1: SkinSafe badges (baseline) ───────────────────────────────
        ss = scrape_skinsafe(ingredient_name)
        for field_name, col_idx in _COL_MAP.items():
            value = getattr(ss, field_name, None)
            if value is not None:
                result[col_idx] = value

        # ── Step 2: Logic overrides (INCI-based, always win) ─────────────────
        paleo_verdict = is_paleo(inci_name)
        if paleo_verdict is not None:
            result[40] = paleo_verdict

        return result