"""
enrichers/base_enricher.py — Abstract base class for all enrichers.

Every enricher takes an ingredient name and returns a partial record dict
keyed by column index (int). The pipeline merges all partial records.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseEnricher(ABC):

    @abstractmethod
    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        """
        Analyse one ingredient and return a dict of {column_index: value}.
        Only include columns this enricher is responsible for.
        Columns not returned will stay at their default (empty).
        """
        ...

    def safe_enrich(self, ingredient_name: str) -> Dict[int, Any]:
        """Wraps enrich() with error handling so one failure doesn't stop the pipeline."""
        try:
            return self.enrich(ingredient_name)
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error on '{ingredient_name}': {e}")
            return {}
