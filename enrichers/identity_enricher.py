"""
enrichers/identity_enricher.py
Responsible for cols 0–2: Ingredient name, INCI Name, Aliases

Sources:
  - col 0: passed in directly
  - col 1: INCI Name  — scraped from CosIng
  - col 2: Aliases    — INN name from CosIng
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from scrapers.cosing import scrape_cosing


class IdentityEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {
            0: ingredient_name,
        }

        cosing = scrape_cosing(ingredient_name)

        if cosing.found:
            if cosing.inci_name:
                result[1] = cosing.inci_name
            if cosing.aliases:
                result[2] = cosing.aliases

        return result
