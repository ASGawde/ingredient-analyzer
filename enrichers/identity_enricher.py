"""
enrichers/identity_enricher.py

Populates cols 0-2: Ingredient name, INCI Name, Aliases.
Uses the CosIng live scraper (Playwright) unless scraping is disabled.
"""

from typing import Any, Dict
from .base_enricher import BaseEnricher
from scrapers.cosing import scrape_cosing

# Module-level flag toggled by main.py --no-scrape
_scraping_disabled = False


class IdentityEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {0: ingredient_name}

        if _scraping_disabled:
            return result

        cosing = scrape_cosing(ingredient_name)
        if cosing.found:
            if cosing.inci_name:
                result[1] = cosing.inci_name
            if cosing.aliases:
                result[2] = cosing.aliases

        return result
