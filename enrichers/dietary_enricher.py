"""
enrichers/dietary_enricher.py

Placeholder enricher for dietary/lifestyle compatibility:
e.g. vegan, cruelty-free, halal, etc.
Currently returns no additional data.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher


class DietaryEnricher(BaseEnricher):
    """Stub implementation — fills no columns yet."""

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        # TODO: Implement logic using future sources (e.g. INCIDecoder, brand data).
        return {}
