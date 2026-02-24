"""
enrichers/concern_enricher.py

Placeholder enricher for mapping ingredients → concerns they help with
(e.g. acne, hyperpigmentation, rosacea).
Currently returns no additional data.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class ConcernEnricher(BaseEnricher):
    """Stub implementation — fills no columns yet."""

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # TODO: Implement concern mapping using rules + external knowledge.
        return {}
