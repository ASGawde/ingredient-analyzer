"""
ingestion/csv_reader.py — Read ingredient names (and optional pre-filled fields)
from a CSV file.

Returns a list of dicts with at minimum:
  {"name": "Niacinamide"}

If the CSV has additional columns like "Role in formulation", they are included:
  {"name": "Niacinamide", "role": "Texture Enhancer"}
"""

import csv
from typing import List, Dict, Optional


_SKIP_FIRST_CELL = {"ingredient name", "ingredient", "name", "inci name", "0"}

# Columns we optionally read if present
_OPTIONAL_COLS = {
    "Role in formulation": "role",
    "INCI Name":           "inci",
    "Allergen potential":  "allergen",
    "Risk of irritation":  "irritation",
}


def _looks_like_index_row(row: List[str]) -> bool:
    numeric = sum(1 for v in row if v.strip().isdigit())
    return numeric >= max(3, len(row) // 2)


def read_csv(
    filepath: str,
    name_col: Optional[str] = "Ingredient name",
) -> List[Dict]:
    """
    Read ingredient data from a CSV file.

    Returns a list of dicts, each with at minimum {"name": "..."}.
    Additional columns (role, inci etc.) are included if present.
    """
    results: List[Dict] = []

    with open(filepath, newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        all_rows = list(csv.reader(f, dialect=dialect))

    if not all_rows:
        return results

    # Strip numeric index row
    start = 0
    if _looks_like_index_row(all_rows[0]):
        start = 1

    if start >= len(all_rows):
        return results

    header_row = all_rows[start]
    data_rows  = all_rows[start + 1:]

    stripped_header = [h.strip() for h in header_row]

    # Resolve name column index
    name_idx = 0
    if name_col and name_col in stripped_header:
        name_idx = stripped_header.index(name_col)
    else:
        first = header_row[0].strip().lower()
        if first not in _SKIP_FIRST_CELL:
            data_rows = [header_row] + data_rows

    # Resolve optional column indices
    optional_indices = {}
    for col_name, key in _OPTIONAL_COLS.items():
        if col_name in stripped_header:
            optional_indices[key] = stripped_header.index(col_name)

    # Build result dicts
    for row in data_rows:
        if name_idx >= len(row):
            continue
        name = row[name_idx].strip()
        if not name:
            continue

        entry = {"name": name}
        for key, idx in optional_indices.items():
            if idx < len(row) and row[idx].strip():
                entry[key] = row[idx].strip()

        results.append(entry)

    return results