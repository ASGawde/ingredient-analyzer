"""
enrichers/skin_type_enricher.py

Placeholder enricher for skin-type-specific columns.
Currently returns no additional data; ready to be wired to future scrapers.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class SkinTypeEnricher(BaseEnricher):
    """Stub implementation — fills no columns yet."""

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # TODO: Implement logic for skin-type suitability, dryness/oiliness flags, etc.
        return {}
