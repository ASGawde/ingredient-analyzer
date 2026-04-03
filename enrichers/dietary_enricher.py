"""
enrichers/dietary_enricher.py
Responsible for cols 37-54 (18 dietary/lifestyle flags).

Priority per field:
  1. Logic modules  — rule-based on INCI name, sets the baseline
  2. Default to "Yes" for all remaining flags

SkinSafe data is now handled by SkinSafeDBEnricher — no live scraping here.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from logic.paleo import is_paleo
from logic.silicone import is_silicone_free
from logic.latex import is_latex_free
from logic.sesame import is_sesame_free
from logic.seafood import is_seafood_free
from logic.dairy import is_dairy_free
from logic.vegan import is_vegan
from logic.vegetarian import is_vegetarian

_LOGIC_MAP = [
    (37, is_vegetarian),
    (38, is_vegan),
    (40, is_paleo),
    (44, is_silicone_free),
    (47, is_latex_free),
    (48, is_sesame_free),
    (53, is_seafood_free),
    (54, is_dairy_free),
]


class DietaryEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # Step 1: Logic as baseline
        for col_idx, logic_fn in _LOGIC_MAP:
            verdict = logic_fn(inci_name)
            if verdict is not None:
                result[col_idx] = verdict

        # Step 2: Default to Yes for all remaining — SkinSafeDBEnricher overrides
        for col_idx in range(37, 55):
            if col_idx not in result:
                result[col_idx] = "Yes"

        return result