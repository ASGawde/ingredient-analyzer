"""
enrichers/benefits_enricher.py

Benefit columns (79-87) are predicted by ModelEnricher.
This enricher is a no-op placeholder for future rule-based overrides.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class BenefitsEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return {}
