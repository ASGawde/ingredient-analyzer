"""
enrichers/safety_enricher.py

Hosts the CosIng role → formulation role mapping used by multiple enrichers.
Calls the CosIng live scraper to populate cols 5, 6, 7, 94 unless scraping
is disabled.
"""

from typing import Any, Dict, Optional
from .base_enricher import BaseEnricher
from scrapers.cosing import scrape_cosing

# Module-level flag toggled by main.py --no-scrape
_scraping_disabled = False


# ── CosIng role → our formulation role ───────────────────────────────────────
# Order matters — more specific entries must come before general ones.
COSING_ROLE_MAP = [
    # Exfoliant
    ("abrasive",                        "Exfoliant"),
    ("exfoliant",                       "Exfoliant"),
    ("keratolytic",                     "Exfoliant"),
    ("anti-seborrheic",                 "Exfoliant"),
    # Active - Antioxidant
    ("antioxidant",                     "Active - Antioxidant"),
    ("reducing",                        "Active - Antioxidant"),
    # Sunscreen
    ("uv absorber",                     "Sunscreen"),
    ("uv filter",                       "Sunscreen"),
    # Preservative
    ("preservative",                    "Preservative"),
    # Penetration Enhancer
    ("penetration enhancer",            "Penetration Enhancer"),
    # Skin conditioning subtypes — must come before generic "skin conditioning"
    ("skin conditioning - emollient",   "Emollient"),
    ("skin conditioning - humectant",   "Humectant"),
    ("skin conditioning - occlusive",   "Occlusive Agent"),
    ("skin conditioning - miscellaneous", "Active"),
    # Emollient
    ("emollient",                       "Emollient"),
    ("antifoaming",                     "Emollient"),
    # Humectant
    ("humectant",                       "Humectant"),
    # Occlusive Agent
    ("occlusive",                       "Occlusive Agent"),
    ("skin protecting",                 "Occlusive Agent"),
    # Emulsifier
    ("emulsifying",                     "Emulsifier"),
    ("surfactant",                      "Emulsifier"),
    ("cleansing",                       "Emulsifier"),
    ("foaming",                         "Emulsifier"),
    # Stabilizer
    ("emulsion stabilising",            "Stabilizer"),
    ("antistatic",                      "Stabilizer"),
    ("stabilising",                     "Stabilizer"),
    # Thickener
    ("viscosity controlling",           "Thickener"),
    ("plasticiser",                      "Texture Enhancer"),
    ("plasticizer",                      "Texture Enhancer"),
    ("binding",                         "Thickener"),
    ("gelling",                         "Thickener"),
    # Texture Enhancer
    ("film forming",                    "Texture Enhancer"),
    ("slip modifier",                   "Texture Enhancer"),
    # pH Adjuster
    ("buffering",                       "pH Adjuster"),
    # Chelating Agent
    ("chelating",                       "Chelating Agent"),
    # Colorant
    ("colorant",                        "Colorant"),
    # Fragrance
    ("fragrance",                       "Fragrance"),
    ("masking",                         "Fragrance"),
    ("perfuming",                       "Fragrance"),
    # Solvent (denaturant maps to Solvent + Penetration Enhancer per supervisor)
    ("solvent",                         "Solvent"),
    ("denaturant",                      "Solvent"),
    # Active — generic catch-all last
    ("astringent",                      "Active"),
    ("bleaching",                       "Active"),
    ("oxidising",                       "Active"),
    ("soothing",                        "Active"),
    ("tanning",                         "Active"),
    ("tonic",                           "Active"),
    ("antimicrobial",                   "Active"),
    ("skin conditioning",               "Active"),
    ("moisturising",                    "Active"),
    ("smoothing",                       "Active"),
    ("moisturizing",                    "Active"),
    # NOT SKINCARE — excluded (no entry):
    # anticaking, antiperspirant, antistatic (standalone), deodorant, depilatory,
    # hair conditioning, hair dyeing, hair fixing, hair waving/straightening,
    # oral care, propellant
]


def _map_cosing_role(cosing_role: str) -> Optional[str]:
    """
    Map a raw CosIng role string to our formulation role vocabulary.
    Pass 1: Try primary role (first listed).
    Pass 2: If primary doesnt map, scan all remaining roles.
    Returns None if no role matches (e.g. all roles are not skincare).
    """
    if not cosing_role:
        return None
    import re
    all_roles = [r.strip().lower() for r in re.split(r"[,\n]", cosing_role.strip()) if r.strip()]
    if not all_roles:
        return None

    # Pass 1: primary role only
    primary = all_roles[0]
    for keyword, our_role in COSING_ROLE_MAP:
        if keyword in primary:
            return our_role

    # Pass 2: scan remaining roles in order
    for role in all_roles[1:]:
        for keyword, our_role in COSING_ROLE_MAP:
            if keyword in role:
                return our_role

    return None


class SafetyEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        if _scraping_disabled:
            return {}

        result: Dict[int, Any] = {}
        cosing = scrape_cosing(ingredient_name)

        if cosing.found:
            if cosing.role:
                mapped = _map_cosing_role(cosing.role)
                if mapped:
                    result[5] = mapped
                result[94] = cosing.role
            if cosing.description:
                result[6] = cosing.description
            result[7] = "CosIng"

        return result
