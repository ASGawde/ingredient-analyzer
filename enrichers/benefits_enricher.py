"""
enrichers/benefits_enricher.py

Placeholder enricher for higher-level human-readable benefit summaries
aggregated from other columns/sources.
Currently returns no additional data.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class BenefitsEnricher(BaseEnricher):
    """Stub implementation — fills no columns yet."""

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # TODO: Implement benefit summarisation (possibly via LLM + rules).
        return {}
