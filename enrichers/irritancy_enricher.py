"""
enrichers/irritancy_enricher.py

Populates:
  Col 3 — Allergen potential  (role + ingredient name logic)
  Col 4 — Risk of irritation  (14k CSV lookup → role+ingredient logic → Low)

Both cols use the same priority:
  1. 14k CSV (col 4 only)
  2. Role + ingredient name logic
  3. Default Low (col 4) / blank (col 3)
"""

import csv
import os
import re
from typing import Dict, Any, Optional

from .base_enricher import BaseEnricher


# ══════════════════════════════════════════════════════════════════════════════
# ALLERGEN POTENTIAL LOGIC
# ══════════════════════════════════════════════════════════════════════════════

_PRESERVATIVE_ALLERGEN_HIGH = {
    "methylisothiazolinone", "methylchloroisothiazolinone", "mci/mi",
    "formaldehyde", "quaternium-15", "dmdm hydantoin",
    "imidazolidinyl urea", "diazolidinyl urea",
    "bronopol", "2-bromo-2-nitropropane-1,3-diol",
    "sodium hydroxymethylglycinate", "tris(hydroxymethyl)nitromethane",
    "methyldibromo glutaronitrile",
}
_PRESERVATIVE_ALLERGEN_MODERATE = {
    "benzisothiazolinone", "octylisothiazolinone",
    "iodopropynyl butylcarbamate", "ipbc",
    "benzyl alcohol", "chlorphenesin",
}
_SUNSCREEN_ALLERGEN_LOW = {
    "zinc oxide", "titanium dioxide",
    "bis-ethylhexyloxyphenol methoxyphenyl triazine", "tinosorb s",
    "methylene bis-benzotriazolyl tetramethylbutylphenol", "tinosorb m",
    "diethylamino hydroxybenzoyl hexyl benzoate", "uvinul a plus",
    "ethylhexyl triazone", "uvinul t 150",
    "drometrizole trisiloxane", "mexoryl xl",
    "terephthalylidene dicamphor sulfonic acid", "mexoryl sx",
    "polysilicone-15",
}
_SUNSCREEN_ALLERGEN_MODERATE = {
    "octocrylene", "ethylhexyl salicylate", "octisalate",
    "homosalate", "phenylbenzimidazole sulfonic acid", "ensulizole",
    "benzophenone-4", "sulisobenzone", "benzophenone-5",
}
_SUNSCREEN_ALLERGEN_HIGH = {
    "oxybenzone", "benzophenone-3", "avobenzone", "butyl methoxydibenzoylmethane",
}
_COLORANT_ALLERGEN_MODERATE = {
    "carmine", "ci 75470", "annatto", "ci 75120", "beta-carotene", "ci 40800",
}
_EMOLLIENT_ALLERGEN_HIGH = {
    "lanolin", "lanolin alcohol", "acetylated lanolin",
    "peg-75 lanolin", "hydrogenated lanolin",
}
_EMOLLIENT_ALLERGEN_MODERATE_KW = [
    "butyrospermum parkii", "theobroma cacao", "mangifera indica",
    "prunus amygdalus", "prunus armeniaca", "argania spinosa",
    "simmondsia chinensis", "rosa canina", "olea europaea",
    "helianthus annuus", "cocos nucifera", "macadamia ternifolia",
    "sesamum indicum", "vitis vinifera", "persea gratissima",
]
_ANTIOXIDANT_ALLERGEN_HIGH_EXACT = {
    "limonene", "linalool", "eugenol", "citral", "geraniol",
    "benzyl salicylate", "benzyl benzoate", "cinnamal", "cinnamyl alcohol",
    "coumarin", "farnesol", "hexyl cinnamal", "isoeugenol",
    "amyl cinnamal", "hydroxycitronellal", "anise alcohol",
    "propolis extract", "royal jelly extract",
}
_ANTIOXIDANT_ALLERGEN_HIGH_KW = [
    "leaf oil", "peel oil", "flower oil", "bark oil", "root oil",
    "lavandula angustifolia", "melaleuca alternifolia",
    "rosmarinus officinalis", "eugenia caryophyllus",
    "cananga odorata", "citrus limon", "citrus aurantium",
    "citrus paradisi", "citrus aurantifolia",
]
_ANTIOXIDANT_ALLERGEN_MODERATE_KW = [
    "camellia sinensis", "vitis vinifera", "punica granatum",
    "vaccinium myrtillus", "vaccinium macrocarpon", "rubus idaeus",
    "curcuma longa", "glycyrrhiza glabra", "zingiber officinale",
    "thymus vulgaris", "ocimum basilicum", "centella asiatica",
    "ginkgo biloba", "chamomilla recutita", "calendula officinalis",
]
_ACTIVE_ALLERGEN_HIGH = {"propolis extract", "royal jelly extract"}
_LOW_ALLERGEN_ROLES = {
    "ph adjuster", "thickener", "humectant", "chelating agent",
    "stabilizer", "texture enhancer", "emulsifier", "solvent",
    "occlusive agent", "exfoliant", "penetration enhancer",
}
_EO_PATTERN = re.compile(r"\b(leaf|peel|flower|bark|root)\s+oil\b", re.IGNORECASE)



# ══════════════════════════════════════════════════════════════════════════════
# INGREDIENT-LEVEL OVERRIDES
# For ingredients where CosIng role doesn't match expected role
# Format: inci_name_lower -> (allergen, irritancy)
# ══════════════════════════════════════════════════════════════════════════════
_INGREDIENT_OVERRIDES = {
    # Lanolin — CosIng maps to Stabilizer but allergen/irritancy are Emollient-level
    "lanolin":                      ("High",     "Moderate"),
    "lanolin alcohol":              ("High",     "High"),
    "acetylated lanolin":           ("High",     "High"),
    "peg-75 lanolin":               ("High",     "High"),
    "hydrogenated lanolin":         ("High",     "Low"),
    # Octocrylene — CosIng maps to Stabilizer but is a Sunscreen
    "octocrylene":                  ("Moderate", "Moderate"),
    # Oxybenzone / Avobenzone
    "oxybenzone":                   ("High",     "High"),
    "benzophenone-3":               ("High",     "High"),
    "avobenzone":                   ("High",     "High"),
    "butyl methoxydibenzoylmethane":("High",     "High"),
    # Propylene Glycol — Humectant in CosIng but moderate irritant/penetration enhancer
    "propylene glycol":             (None,       "Moderate"),
    # Benzyl Alcohol — often listed as Fragrance or Solvent in CosIng
    "benzyl alcohol":               ("Moderate", "High"),
    # Phenoxyethanol — CosIng sometimes returns as Active not Preservative
    "phenoxyethanol":               ("Low",      "Moderate"),
    # Cocos Nucifera Oil — Active in CosIng but Emollient allergen logic
    "cocos nucifera oil":           ("Moderate", "Low"),
    # Limonene / Linalool — often listed as fragrance components
    "limonene":                     ("High",     "Moderate"),
    "linalool":                     ("High",     "Moderate"),
}

def _allergen(role: Optional[str], inci: str) -> Optional[str]:
    # Check ingredient-level override first
    override = _INGREDIENT_OVERRIDES.get(inci.strip().lower())
    if override and override[0] is not None:
        return override[0]
    if not role:
        if _EO_PATTERN.search(inci):
            return "High risk"
        return None
    primary = re.split(r"[,\n]", role.strip())[0].strip().lower()
    inci_l = inci.strip().lower()

    if primary == "preservative":
        if inci_l in _PRESERVATIVE_ALLERGEN_HIGH: return "High risk"
        if inci_l in _PRESERVATIVE_ALLERGEN_MODERATE: return "Moderate risk"
        return "Low risk"
    if primary in ("fragrance", "essential oil"):
        return "High risk"
    if primary == "sunscreen":
        if inci_l in _SUNSCREEN_ALLERGEN_HIGH: return "High risk"
        if inci_l in _SUNSCREEN_ALLERGEN_MODERATE: return "Moderate risk"
        return "Low risk"
    if primary == "colorant":
        if inci_l in _COLORANT_ALLERGEN_MODERATE: return "Moderate risk"
        return "Low risk"
    if primary == "emollient":
        if inci_l in _EMOLLIENT_ALLERGEN_HIGH: return "High risk"
        for kw in _EMOLLIENT_ALLERGEN_MODERATE_KW:
            if kw in inci_l: return "Moderate risk"
        return "Low risk"
    if primary == "active - antioxidant":
        if inci_l in _ANTIOXIDANT_ALLERGEN_HIGH_EXACT: return "High risk"
        for kw in _ANTIOXIDANT_ALLERGEN_HIGH_KW:
            if kw in inci_l: return "High risk"
        if _EO_PATTERN.search(inci): return "High risk"
        for kw in _ANTIOXIDANT_ALLERGEN_MODERATE_KW:
            if kw in inci_l: return "Moderate risk"
        return "Low risk"
    if primary == "active":
        if inci_l in _ACTIVE_ALLERGEN_HIGH: return "High risk"
        return "Low risk"
    if primary in _LOW_ALLERGEN_ROLES:
        return "Low risk"
    if _EO_PATTERN.search(inci):
        return "High risk"
    return None


# ══════════════════════════════════════════════════════════════════════════════
# IRRITATION POTENTIAL LOGIC
# ══════════════════════════════════════════════════════════════════════════════

# Emulsifier
_EMULSIFIER_IRR_HIGH = {
    "sodium lauryl sulfate", "ammonium lauryl sulfate",
    "sodium laureth sulfate", "ammonium laureth sulfate",
    "sodium myreth sulfate",
}
_EMULSIFIER_IRR_MODERATE = {
    "polysorbate 20", "polysorbate 60", "polysorbate 280",
    "peg-40 hydrogenated castor oil", "ppg-26-buteth-26",
    "oleth-10", "oleth-20", "laureth-4", "laureth-7",
}

# Sunscreen
_SUNSCREEN_IRR_HIGH = {"benzophenone-3", "oxybenzone"}
_SUNSCREEN_IRR_MODERATE = {
    "octocrylene", "benzophenone-5", "ethylhexyl salicylate",
    "homosalate", "benzophenone-4",
}

# Fragrance
_FRAGRANCE_IRR_HIGH = {
    "fragrance", "parfum",
    "cinnamomum zeylanicum bark oil", "cinnamon oil",
    "eugenia caryophyllus bud oil", "clove oil",
    "thymus vulgaris oil", "thyme oil",
    "origanum vulgare oil",
}
_FRAGRANCE_IRR_MODERATE = {
    "limonene", "linalool", "eugenol", "citral", "geraniol",
    "cinnamal", "cinnamyl alcohol", "coumarin", "farnesol",
    "hexyl cinnamal", "isoeugenol", "amyl cinnamal",
    "hydroxycitronellal", "anise alcohol",
    "benzyl salicylate", "benzyl benzoate",
    "citrus limon peel oil", "citrus bergamia peel oil",
    "citrus aurantifolia peel oil",
    "menthol", "camphor", "peppermint oil", "mentha piperita oil",
    "eucalyptus oil", "rosa damascena flower oil",
    "cananga odorata flower oil", "lavandula hybrida oil",
    "mentha spicata oil", "wintergreen oil", "jasmine oil",
    "ylang ylang oil", "rose oil", "spearmint oil",
    "tea tree oil", "melaleuca oil",
}

# Solvent
_SOLVENT_IRR_HIGH = {
    "alcohol denat", "sd alcohol", "ethanol",
    "isopropyl alcohol", "methanol", "benzyl alcohol",
}
_SOLVENT_IRR_MODERATE = {
    "propylene glycol", "butylene glycol", "pentylene glycol",
    "hexylene glycol", "caprylyl glycol", "ethoxydiglycol",
    "dimethyl isosorbide", "transcutol",
    "diethylene glycol monoethyl ether",
}

# Preservative
_PRESERVATIVE_IRR_HIGH = {
    "methylisothiazolinone", "methylchloroisothiazolinone",
    "formaldehyde", "dmdm hydantoin", "imidazolidinyl urea",
    "diazolidinyl urea", "quaternium-15", "bronopol",
    "benzalkonium chloride",
}
_PRESERVATIVE_IRR_MODERATE = {
    "phenoxyethanol", "benzyl alcohol", "chlorphenesin",
}

# Penetration Enhancer
_PENE_IRR_HIGH = {
    "isopropyl myristate", "isopropyl palmitate", "oleic acid",
    "dimethyl sulfoxide", "dmso", "azone", "laurocapram",
    "n-methyl-2-pyrrolidone",
}
_PENE_IRR_MODERATE = {"oleyl alcohol"}

# pH Adjuster
_PH_IRR_HIGH = {
    "sodium hydroxide", "potassium hydroxide", "ammonium hydroxide",
    "calcium hydroxide", "magnesium hydroxide", "phosphoric acid",
}
_PH_IRR_MODERATE = {
    "triethanolamine", "tea", "diethanolamine", "dea",
    "aminomethyl propanol", "tromethamine", "tris", "citric acid",
}

# Exfoliant
_EXFOLIANT_IRR_HIGH = {
    "glycolic acid", "lactic acid", "salicylic acid",
    "capryloyl salicylic acid", "lha", "resorcinol",
    "trichloroacetic acid",
}
_EXFOLIANT_IRR_MODERATE = {
    "mandelic acid", "tartaric acid", "malic acid",
    "willow bark extract", "salix alba extract", "betaine salicylate",
}

# Emollient
_EMOLLIENT_IRR_HIGH = {
    "lanolin alcohol", "acetylated lanolin", "peg-75 lanolin",
}
_EMOLLIENT_IRR_MODERATE = {"lanolin"}

# Humectant
_HUMECTANT_IRR_MODERATE = {"urea"}

# Active
_ACTIVE_IRR_HIGH = {
    "retinol", "retinal", "retinaldehyde", "tretinoin",
    "adapalene", "tazarotene", "benzoyl peroxide", "hydroquinone",
}
_ACTIVE_IRR_MODERATE = {"azelaic acid", "kojic acid"}

# Low irritation roles (always Low regardless of ingredient)
_LOW_IRR_ROLES = {
    "thickener", "chelating agent", "stabilizer", "texture enhancer",
    "occlusive agent", "colorant", "active - antioxidant",
}


def _irritancy(role: Optional[str], inci: str) -> str:
    """Returns High / Moderate / Low based on role + INCI name."""
    # Check ingredient-level override first
    override = _INGREDIENT_OVERRIDES.get(inci.strip().lower())
    if override and override[1] is not None:
        return override[1]
    if not role:
        return "Low risk"
    primary = re.split(r"[,\n]", role.strip())[0].strip().lower()
    inci_l = inci.strip().lower()

    if primary in _LOW_IRR_ROLES:
        return "Low risk"

    if primary == "emulsifier":
        if inci_l in _EMULSIFIER_IRR_HIGH: return "High risk"
        if inci_l in _EMULSIFIER_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "sunscreen":
        if inci_l in _SUNSCREEN_IRR_HIGH: return "High risk"
        if inci_l in _SUNSCREEN_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary in ("fragrance", "essential oil"):
        if inci_l in _FRAGRANCE_IRR_HIGH: return "High risk"
        if inci_l in _FRAGRANCE_IRR_MODERATE: return "Moderate risk"
        if _EO_PATTERN.search(inci): return "Moderate risk"
        return "Low risk"

    if primary == "solvent":
        if inci_l in _SOLVENT_IRR_HIGH: return "High risk"
        if inci_l in _SOLVENT_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "preservative":
        if inci_l in _PRESERVATIVE_IRR_HIGH: return "High risk"
        if inci_l in _PRESERVATIVE_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "penetration enhancer":
        if inci_l in _PENE_IRR_HIGH: return "High risk"
        if inci_l in _PENE_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "ph adjuster":
        if inci_l in _PH_IRR_HIGH: return "High risk"
        if inci_l in _PH_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "exfoliant":
        if inci_l in _EXFOLIANT_IRR_HIGH: return "High risk"
        if inci_l in _EXFOLIANT_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "emollient":
        if inci_l in _EMOLLIENT_IRR_HIGH: return "High risk"
        if inci_l in _EMOLLIENT_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "humectant":
        if inci_l in _HUMECTANT_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    if primary == "active":
        if inci_l in _ACTIVE_IRR_HIGH: return "High risk"
        if inci_l in _ACTIVE_IRR_MODERATE: return "Moderate risk"
        return "Low risk"

    return "Low risk"


# ══════════════════════════════════════════════════════════════════════════════
# CSV LOADER
# ══════════════════════════════════════════════════════════════════════════════

def _load_irritancy_db() -> Dict[str, str]:
    db: Dict[str, str] = {}
    csv_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "irritancy_db.csv")
    )
    if not os.path.exists(csv_path):
        print(f"[IrrirancyEnricher] WARNING: {csv_path} not found")
        return db
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # numeric header
        next(reader)  # column names
        for row in reader:
            if len(row) < 5:
                continue
            inci  = row[1].strip().lower()
            value = row[4].strip()
            if inci and value in ("Yes", "No"):
                db[inci] = value
            ing = row[0].strip().lower()
            if ing and value in ("Yes", "No") and ing not in db:
                db[ing] = value
    return db


IRRITANCY_DB = _load_irritancy_db()


# ══════════════════════════════════════════════════════════════════════════════
# ENRICHER
# ══════════════════════════════════════════════════════════════════════════════

class IrrirancyEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(
        self,
        ingredient_name: str,
        inci_name: str,
        role: Optional[str] = None,
    ) -> Dict[int, Any]:
        result: Dict[int, Any] = {}

        # Col 3: Allergen potential
        allergen = _allergen(role, inci_name)
        if allergen:
            result[3] = allergen

        # Col 4: Risk of irritation
        # Run logic first
        logic_val = _irritancy(role, inci_name)

        # If logic says High or Moderate — always trust logic (more accurate than binary CSV)
        if logic_val in ("High risk", "Moderate risk"):
            result[4] = logic_val
            return result

        # Otherwise check CSV — use it to upgrade Low to High if CSV says Yes
        for key in (inci_name.strip().lower(), ingredient_name.strip().lower()):
            if key in IRRITANCY_DB:
                csv_val = IRRITANCY_DB[key]
                result[4] = "High" if csv_val == "Yes" else "Low"
                return result

        # Fall back to logic
        result[4] = logic_val
        return result