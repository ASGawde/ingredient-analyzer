"""
enrichers/concentration_enricher.py

Populates:
  Col  9  — Known concentration Rinse-off
  Col 10  — Known concentration Leave-on
  Col 11  — Concentration Sensitive/eye area
  Col 91  — Predicted or manual

Source priority:
  1. Regulatory DB from data/concentration_db.csv (EU Annex III, SCCS, IFRA 51st)
  2. Formulation role → concentration band lookup
  3. "Manual" to col 91
"""

from __future__ import annotations

import csv
import os
import re
from typing import Any, Dict, Optional, Tuple

from .base_enricher import BaseEnricher

def _load_concentration_db() -> Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]:
    db: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "concentration_db.csv")
    csv_path = os.path.normpath(csv_path)
    if not os.path.exists(csv_path):
        print(f"[ConcentrationEnricher] WARNING: {csv_path} not found — DB will be empty")
        return db
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["inci_name"].strip().lower()
            rinse = row["rinse_off"].strip() or None
            leave = row["leave_on"].strip() or None
            eye   = row["eye_area"].strip() or None
            db[key] = (rinse, leave, eye)
    return db

CONCENTRATION_DB = _load_concentration_db()

ROLE_CONCENTRATION_BANDS: Dict[str, Tuple[Optional[str], Optional[str], Optional[str], bool]] = {
    "Preservative":         ("0.05-1%",   "0.05-1%",   "0.05-0.5%",    False),
    "Active":               (None,        None,        None,           True),
    "Active - Antioxidant": (None,        None,        None,           True),
    "pH Adjuster":          ("0.01-0.5%", "0.01-0.5%", "0.01-0.25%",  False),
    "Thickener":            ("0.1-3%",    "0.1-3%",    "0.1-1%",       False),
    "Emollient":            ("1-100%",    "1-100%",    "1-50%",        False),
    "Humectant":            ("1-20%",     "1-20%",     "1-10%",        False),
    "Fragrance":            ("0.05-2%",   "0.05-2%",   "Not approved", False),
    "Emulsifier":           ("1-8%",      "1-8%",      "1-4%",         False),
    "Colorant":             ("0.001-5%",  "0.001-5%",  "0.001-2%",     False),
    "Solvent":              ("1-100%",    "1-100%",    "1-50%",        False),
    "Chelating Agent":      ("0.05-0.5%", "0.05-0.5%", "0.05-0.25%",  False),
    "Stabilizer":           ("0.05-1%",   "0.05-1%",   "0.05-0.5%",   False),
    "Texture Enhancer":     ("0.5-5%",    "0.5-5%",    "0.5-2%",       False),
    "Occlusive Agent":      ("1-50%",     "1-50%",     "1-20%",        False),
    "Penetration Enhancer": ("0.1-10%",   "0.1-10%",   "Not approved", False),
    "Exfoliant":            (None,        None,        None,           True),
    "Sunscreen":            (None,        None,        None,           True),
}


def _normalise(name: str) -> str:
    return name.strip().lower()


def _apply_band(mapped_role: str) -> Optional[Dict[int, Any]]:
    """Return concentration result dict for a formulation role."""
    band = ROLE_CONCENTRATION_BANDS.get(mapped_role)
    if band is None:
        return None
    rinse, leave, eye, needs_manual = band
    if needs_manual:
        return {91: "Manual"}
    result: Dict[int, Any] = {}
    if rinse:
        result[9]  = rinse
    if leave:
        result[10] = leave
    if eye:
        result[11] = eye
    return result


def _derive_eye_area(rinse: Optional[str], leave: Optional[str]) -> Optional[str]:
    for v in (rinse, leave):
        if v and "not approved" in v.lower():
            return "Not approved"
    for v in (leave, rinse):
        if not v:
            continue
        m = re.search(r"([\d.]+)\s*%", v)
        if m:
            pct = float(m.group(1))
            derived = pct * 0.5
            if derived < 0.01:
                return f"{derived:.3f}%"
            elif derived < 0.1:
                return f"{derived:.2f}%"
            else:
                return f"{derived:.1f}%"
    return None


class ConcentrationEnricher(BaseEnricher):
    """
    Priority:
      1. Regulatory DB   — exact ingredient-specific limits
      2. CosIng role → formulation role → concentration band
      3. "Manual" to col 91
    """

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(
        self,
        ingredient_name: str,
        inci_name: str,
        role: Optional[str] = None,
    ) -> Dict[int, Any]:

        # 1. Regulatory DB
        for key in (_normalise(inci_name), _normalise(ingredient_name)):
            if key in CONCENTRATION_DB:
                rinse, leave, eye = CONCENTRATION_DB[key]
                result: Dict[int, Any] = {}
                if rinse is not None:
                    result[9]  = rinse
                if leave is not None:
                    result[10] = leave
                if eye is not None:
                    result[11] = eye
                elif rinse is not None or leave is not None:
                    derived = _derive_eye_area(rinse, leave)
                    if derived:
                        result[11] = derived
                return result

        # 2. Role-based fallback — role comes from col 5 (CosIng scrape)
        if role:
            # Role is already in our vocabulary — mapped by SafetyEnricher
            # Primary role = first listed before comma/newline
            primary_role = re.split(r"[\n,]", role.strip())[0].strip()
            band_result = _apply_band(primary_role)
            if band_result is not None:
                return band_result

        # 3. Nothing found
        return {91: "Manual"}