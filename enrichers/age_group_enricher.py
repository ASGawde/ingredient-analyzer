"""
enrichers/age_group_enricher.py

Placeholder enricher for age-group-specific recommendations.
Currently returns no additional data; ready for future rules/scrapers.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class AgeGroupEnricher(BaseEnricher):
    """Stub implementation — fills no columns yet."""

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # TODO: Implement logic for suitability by age group (teens, adult, mature, etc.).
        return {}
