"""
enrichers/base_enricher.py — Abstract base class for all enrichers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseEnricher(ABC):

    @abstractmethod
    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        """
        Analyse one ingredient and return a dict of {column_index: value}.
        Only include columns this enricher is responsible for.
        """
        ...

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        """
        Enrichers that need the INCI name for logic overrides this method.
        Default falls back to enrich() so existing enrichers work unchanged.
        """
        return self.enrich(ingredient_name)

    def safe_enrich(self, ingredient_name: str) -> Dict[int, Any]:
        """Wraps enrich() with error handling."""
        try:
            return self.enrich(ingredient_name)
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error on '{ingredient_name}': {e}")
            return {}