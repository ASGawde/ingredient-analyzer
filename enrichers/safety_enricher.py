"""
enrichers/safety_enricher.py
Responsible for cols 3–14:
  Allergen potential, Risk of irritation, Role in formulation, Note, Source,
  Comedogenic Rating, Concentration (3x), Side effects,
  Incompatible with, Works well with

Current sources:
  - col 5 (Role in formulation) — CosIng Functions field
  - col 6 (Note)                — CosIng Description field
  - col 7 (Source)              — hardcoded "CosIng" when data is found

Remaining cols (3,4,8–14) remain TODO for future scrapers.
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from scrapers.cosing import scrape_cosing


class SafetyEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        cosing = scrape_cosing(ingredient_name)

        if cosing.found:
            if cosing.role:
                result[5] = cosing.role          # Role in formulation
            if cosing.description:
                result[6] = cosing.description   # Note
            result[7] = "CosIng"                 # Source

        # TODO: populate from additional scrapers (INCIDecoder, CosDNA, EWG):
        # result[3]  = allergen_potential
        # result[4]  = risk_of_irritation
        # result[8]  = comedogenic_rating
        # result[9]  = concentration_rinse_off
        # result[10] = concentration_leave_on
        # result[11] = concentration_sensitive_eye
        # result[12] = side_effects
        # result[13] = incompatible_with
        # result[14] = works_well_with

        return result
