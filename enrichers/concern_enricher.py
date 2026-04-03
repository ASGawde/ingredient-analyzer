"""
enrichers/concern_enricher.py

Concern columns (55-78) are predicted by ModelEnricher.
This enricher is a no-op placeholder for future rule-based overrides.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class ConcernEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return {}
