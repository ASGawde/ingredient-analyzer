"""
enrichers/skin_type_enricher.py
Responsible for cols 15–30:
  Skin type (Normal, Dry, Oily, Combination) — cols 15-18     TODO
  Sensitivity scale (6 levels)               — cols 19-24     ✓ logic
  Acne-prone scale (6 levels)                — cols 25-30     TODO
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from logic.sensitivity import get_sensitivity_ratings


class SkinTypeEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # ── Sensitivity ratings (cols 19-24) ──────────────────────────────────
        sensitivity = get_sensitivity_ratings(inci_name)
        result.update(sensitivity)

        # TODO: skin type suitability (cols 15-18)
        # TODO: acne-prone suitability (cols 25-30)

        return result