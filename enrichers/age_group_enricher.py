"""
enrichers/age_group_enricher.py

Responsible for cols 31–36: Teen, 20s, 30s, 40s, 50s, 60+

Teen (col 31) comes from SkinSafe's "Teen safe" badge.
20s–60+ (cols 32–36) are TODO — no source yet.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from scrapers.skinsafe import scrape_skinsafe


class AgeGroupEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        ss = scrape_skinsafe(ingredient_name)
        if ss.teen is not None:
            result[31] = ss.teen   # "Yes" / "No" / "Not found"

        # TODO cols 32–36 (20s–60+): no data source identified yet
        return result
