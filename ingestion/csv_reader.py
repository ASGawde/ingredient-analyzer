"""
ingestion/csv_reader.py — Read ingredient names from a CSV file.

Handles:
  - Standard single/multi-column CSVs with a header row
  - The Skingenius two-row header format (numeric index row + column name row)
  - A single column of ingredient names with or without a header
"""

import csv
from typing import List, Optional


# Values in the first cell that indicate a non-data row to skip
_SKIP_FIRST_CELL = {"ingredient name", "ingredient", "name", "inci name", "0"}


def _looks_like_index_row(row: List[str]) -> bool:
    """Return True if a row appears to be a numeric index row (e.g. '0','1','2',...)."""
    numeric = sum(1 for v in row if v.strip().isdigit())
    return numeric >= max(3, len(row) // 2)


def read_csv(filepath: str, name_col: Optional[str] = "Ingredient name") -> List[str]:
    """
    Read ingredient names from a CSV file.

    Args:
        filepath:  Path to the CSV file.
        name_col:  Name of the column containing ingredient names.
                   If None, uses the first column.

    Returns:
        List of ingredient name strings (stripped, non-empty).
    """
    ingredients: List[str] = []

    with open(filepath, newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        all_rows = list(csv.reader(f, dialect=dialect))

    if not all_rows:
        return ingredients

    # ── Detect and strip a leading numeric index row ──────────────────────────
    start = 0
    if _looks_like_index_row(all_rows[0]):
        start = 1

    if start >= len(all_rows):
        return ingredients

    header_row = all_rows[start]
    data_rows  = all_rows[start + 1:]

    # ── Resolve column index ──────────────────────────────────────────────────
    col_idx = 0
    if name_col:
        stripped_header = [h.strip() for h in header_row]
        if name_col in stripped_header:
            col_idx = stripped_header.index(name_col)
            # Header row is already consumed — don't add it to ingredients
        else:
            # No matching header found; treat header row as data if it's not a known label
            first = header_row[0].strip().lower()
            if first not in _SKIP_FIRST_CELL:
                data_rows = [header_row] + data_rows

    # ── Extract values ────────────────────────────────────────────────────────
    for row in data_rows:
        if col_idx >= len(row):
            continue
        val = row[col_idx].strip()
        if val:
            ingredients.append(val)

    return ingredients
