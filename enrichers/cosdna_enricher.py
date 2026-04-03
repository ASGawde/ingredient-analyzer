"""
enrichers/cosdna_enricher.py

Populates:
  Col 8 — Comedogenic Rating (0-5 scale)

Derived from acne logic categories:
  Cat A (highly comedogenic) → 4
  Cat B (heavy occlusives)   → 3
  Cat C (fatty acids)        → 2
  Cat E (algae)              → 1
  No category match          → 0
"""

from typing import Any, Dict
from .base_enricher import BaseEnricher
from logic.acne import _get_categories as get_acne_categories

# Acne category → comedogenic rating
_CAT_RATING = {
    "A": "4",
    "B": "3",
    "C": "2",
    "E": "1",
}


def _comedogenic_from_logic(inci_name: str) -> str:
    """Derive comedogenic rating from acne logic categories."""
    cats = get_acne_categories(inci_name)
    if not cats:
        return "0"
    ratings = [int(_CAT_RATING[c]) for c in cats if c in _CAT_RATING]
    return str(max(ratings)) if ratings else "0"


class CosdnaEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return {8: _comedogenic_from_logic(ingredient_name)}

    def enrich_with_inci(
        self, ingredient_name: str, inci_name: str
    ) -> Dict[int, Any]:
        return {8: _comedogenic_from_logic(inci_name)}