"""
enrichers/model_enricher.py

Loads model.pkl and predicts 25 target variables:
  4 skin types, 12 skin concerns, 9 benefit tags.
Runs last after all other enrichers populate the feature columns.
"""

import os
import pickle
import warnings
from typing import Any, Dict, Optional

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

from .base_enricher import BaseEnricher

# Exact feature order as trained — must match exactly
FEATURE_ORDER = [
    "Allergen potential", "Risk of irritation",
    "Active", "Humectant", "Emollient", "Fragrance", "Essential Oil",
    "ph Adjuster", "Texture Enhancer", "Occlusive agent", "Stabilizer",
    "Sunscreen", "Solvent", "Preservative", "Colorant", "Thickener",
    "Emulsifier", "Chelating agent", "Penetration enhancer", "Exfoliant",
    "Film former", "Anti-acne",
    "Comedogenic Rating",
    "Not sensitive", "A little sensitive", "Moderately sensitive", "Sensitive",
    "Very sensitive", "Extremely sensitive", "Not acne prone", "A little acne-prone",
    "Moderately acne-prone", "Acne-prone", "Very acne-prone", "Extremely acne-prone",
    "Teen", "20s", "30s", "40s", "50s", "60+",
    "Vegetarian", "Vegan", "Gluten-free", "Paleo", "Nut-free", "Soy-free",
    "Latex-free", "Sesame-free", "Citrus-free", "Dye-free", "Fragrance-free",
]

# Target variable -> output column index
TARGET_COL_MAP = {
    "Normal":                               15,
    "Dry":                                  16,
    "Oily":                                 17,
    "Combination":                          18,
    "Rosacea":                              55,
    "Hyperpigmentation & Uneven skin tone": 57,
    "Acne":                                 59,
    "Dryness/Dehydration":                  61,
    "Oiliness & Shine":                     63,
    "Fine lines & Wrinkles":                65,
    "Loss of Elasticity/firmness":          67,
    "Visible pores & Uneven texture":       69,
    "Clogged pores, blackheads":            71,
    "Dullness":                             73,
    "Dark circles":                         75,
    "Blemishes":                            77,
    # ── Benefit targets (predicted by model) ──
    "Moisturizing":                         79,
    "Nourishing":                           80,
    "Exfoliating":                          81,
    "Soothing":                             82,
    "Healing":                              83,
    "Smoothing":                            84,
    "Brightening":                          85,
    "Minimizes pores":                      86,
    "Firming":                              87,
}

# Our role vocabulary -> model binary flag column
ROLE_TO_FLAG = {
    "active":                "Active",
    "active - antioxidant":  "Active",
    "humectant":             "Humectant",
    "emollient":             "Emollient",
    "fragrance":             "Fragrance",
    "essential oil":         "Essential Oil",
    "ph adjuster":           "ph Adjuster",
    "texture enhancer":      "Texture Enhancer",
    "occlusive agent":       "Occlusive agent",
    "stabilizer":            "Stabilizer",
    "sunscreen":             "Sunscreen",
    "solvent":               "Solvent",
    "preservative":          "Preservative",
    "colorant":              "Colorant",
    "thickener":             "Thickener",
    "emulsifier":            "Emulsifier",
    "chelating agent":       "Chelating agent",
    "penetration enhancer":  "Penetration enhancer",
    "exfoliant":             "Exfoliant",
}

ALL_ROLE_FLAGS = [
    "Active", "Humectant", "Emollient", "Fragrance", "Essential Oil",
    "ph Adjuster", "Texture Enhancer", "Occlusive agent", "Stabilizer",
    "Sunscreen", "Solvent", "Preservative", "Colorant", "Thickener",
    "Emulsifier", "Chelating agent", "Penetration enhancer", "Exfoliant",
    "Film former", "Anti-acne",
]


# Pipeline col index -> feature name
COL_TO_FEATURE = {
    19: "Not sensitive",
    20: "A little sensitive",
    21: "Moderately sensitive",
    22: "Sensitive",
    23: "Very sensitive",
    24: "Extremely sensitive",
    25: "Not acne prone",
    26: "A little acne-prone",
    27: "Moderately acne-prone",
    28: "Acne-prone",
    29: "Very acne-prone",
    30: "Extremely acne-prone",
    31: "Teen",
    32: "20s",
    33: "30s",
    34: "40s",
    35: "50s",
    36: "60+",
    37: "Vegetarian",
    38: "Vegan",
    39: "Gluten-free",
    40: "Paleo",
    45: "Nut-free",
    46: "Soy-free",
    47: "Latex-free",
    48: "Sesame-free",
    49: "Citrus-free",
    50: "Dye-free",
    51: "Fragrance-free",
}



def _normalise_risk(val: Optional[Any]) -> str:
    if not val:
        return "low risk"
    return str(val).strip().lower()


class ModelEnricher(BaseEnricher):

    def __init__(self, model_path: str = "model.pkl"):
        self.model_path = model_path
        self._bundle    = None

    def _get_bundle(self):
        if self._bundle is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"model.pkl not found at '{self.model_path}'."
                )
            with open(self.model_path, "rb") as f:
                self._bundle = pickle.load(f)
        return self._bundle

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return {}

    def enrich_with_inci(self, ingredient_name: str, inci_name: str) -> Dict[int, Any]:
        return {}

    def enrich_with_record(self, merged: Dict[int, Any]) -> Dict[int, Any]:
        bundle         = self._get_bundle()
        models         = bundle["models"]
        label_encoders = bundle["label_encoders"]
        feature_encoder= bundle["feature_encoder"]
        target_vars    = bundle["target_vars"]

        row = {}

        # Allergen + irritation — lowercase
        row["Allergen potential"] = _normalise_risk(merged.get(3))
        row["Risk of irritation"] = _normalise_risk(merged.get(4))

        # Role flags — set all matching roles from full CosIng role string (col 94)
        for flag in ALL_ROLE_FLAGS:
            row[flag] = 0

        # Get all roles from col 94 (raw CosIng string), fallback to col 5
        raw_roles = str(merged.get(94, "") or merged.get(5, "") or "")
        all_roles = [r.strip().lower() for r in raw_roles.split(",") if r.strip()]

        # Set binary flag for every matched role
        for r in all_roles:
            for keyword, flag in ROLE_TO_FLAG.items():
                if keyword in r:
                    row[flag] = 1
                    break

        # Comedogenic Rating
        try:
            row["Comedogenic Rating"] = int(merged.get(8, 0) or 0)
        except (ValueError, TypeError):
            row["Comedogenic Rating"] = 0

        # Sensitivity / acne / age / dietary cols
        for col_idx, feat_name in COL_TO_FEATURE.items():
            row[feat_name] = merged.get(col_idx, None)

        # Build DataFrame in exact training column order
        X = pd.DataFrame([row])[FEATURE_ORDER]
        X_encoded = feature_encoder.transform(X)

        # Convert to numpy to bypass sklearn version feature name checks
        X_numpy = X_encoded.to_numpy() if hasattr(X_encoded, "to_numpy") else X_encoded

        result: Dict[int, Any] = {}
        for variable in target_vars:
            if variable not in models:
                continue
            pred_encoded = models[variable].predict(X_numpy)
            pred_label   = label_encoders[variable].inverse_transform(pred_encoded)[0]
            col_idx = TARGET_COL_MAP.get(variable)
            if col_idx is not None:
                result[col_idx] = pred_label

        return result