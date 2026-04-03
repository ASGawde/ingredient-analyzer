"""
enrichers/skin_type_enricher.py

Populates cols 19-24 (sensitivity) and 25-30 (acne-prone) via logic modules.
Skin type suitability (cols 15-18) is predicted by ModelEnricher.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from logic.sensitivity import get_sensitivity_ratings
from logic.acne import get_acne_ratings


class SkinTypeEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # ── Sensitivity ratings (cols 19-24) ──────────────────────────────────
        result.update(get_sensitivity_ratings(inci_name))

        # ── Acne-prone ratings (cols 25-30) ───────────────────────────────────
        result.update(get_acne_ratings(inci_name))

        return result