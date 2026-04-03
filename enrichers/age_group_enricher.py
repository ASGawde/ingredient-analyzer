"""
enrichers/age_group_enricher.py
Responsible for cols 31-36 (age group flags).

SkinSafe teen badge is now handled by SkinSafeDBEnricher — no live scraping here.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from logic.age import get_age_ratings


class AgeGroupEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # Logic-based age ratings
        result.update(get_age_ratings(inci_name))

        return result