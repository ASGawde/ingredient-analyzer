"""
enrichers/cosing_inventory_enricher.py

Fast CSV lookup against the 30k-ingredient CosIng inventory.

Populates:
  Col  1 — INCI Name
  Col  5 — Role in formulation (mapped via _map_cosing_role)
  Col  6 — Note/Description
  Col  7 — Source → "CosIng Inventory"
  Col 94 — Raw CosIng function string (for model binary flags)
"""

import os
import csv
import re
from typing import Dict, Any, Optional

from .base_enricher import BaseEnricher


def _load_inventory() -> Dict[str, Dict]:
    """Load CosIng inventory CSV into a dict keyed by normalized INCI name."""
    db = {}
    csv_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "cosing_inventory.csv")
    )
    if not os.path.exists(csv_path):
        print(f"[CosingInventoryEnricher] WARNING: {csv_path} not found")
        return db

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inci = (row.get("INCI name") or row.get("Ingredient name") or "").strip()
            if not inci:
                continue
            key = inci.lower()
            db[key] = {
                "inci":        inci,
                "function":    (row.get("Function") or row.get("Role in formulation") or "").strip(),
                "description": row.get("Chem/IUPAC Name / Description", "").strip(),
            }
    print(f"[CosingInventoryEnricher] Loaded {len(db)} ingredients")
    return db


INVENTORY_DB = _load_inventory()


def _norm(name: str) -> str:
    """Normalize for lookup — lowercase, collapse spaces/hyphens."""
    return re.sub(r"[\s\-]+", " ", name.strip().lower())


class CosingInventoryEnricher(BaseEnricher):

    def enrich(self, ingredient_name: str) -> Dict[int, Any]:
        return self.enrich_with_inci(ingredient_name, ingredient_name)

    def enrich_with_inci(
        self,
        ingredient_name: str,
        inci_name: str,
        role: Optional[str] = None,
    ) -> Dict[int, Any]:
        from enrichers.safety_enricher import _map_cosing_role

        # Try lookup by INCI name first, then ingredient name
        record = None
        for key in [
            _norm(inci_name),
            _norm(ingredient_name),
            inci_name.strip().lower(),
            ingredient_name.strip().lower(),
        ]:
            if key in INVENTORY_DB:
                record = INVENTORY_DB[key]
                break

        if not record:
            return {}

        result: Dict[int, Any] = {}

        # Col 1: INCI Name
        if record["inci"]:
            result[1] = record["inci"]

        # Col 5: Role — map function through our vocabulary
        if record["function"]:
            mapped = _map_cosing_role(record["function"])
            if mapped:
                result[5] = mapped
            # Store raw function for model binary flags
            result[94] = record["function"]

        # Col 6: Description
        if record["description"]:
            result[6] = record["description"][:300]

        # Col 7: Source
        result[7] = "CosIng Inventory"

        return result