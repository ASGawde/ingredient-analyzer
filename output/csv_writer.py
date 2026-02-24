"""
output/csv_writer.py — Writes enriched ingredient data to CSV in the exact
original format:
  Row 0: numeric index (0–89 for first 90 cols, blank for last 4)
  Row 1: column names
  Row 2+: data rows
"""

import csv
import os
from typing import List, Dict, Any

from schema import COLUMNS, COLUMN_NAMES, NUMERIC_INDEX


def _format_value(value: Any, col_type: str) -> str:
    """Convert a Python value to its CSV string representation."""
    if value is None or value == "":
        return ""
    if col_type == "bool":
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, str):
            return value.upper() if value.lower() in ("true", "false") else value
    if col_type == "float":
        try:
            f = float(value)
            # Drop unnecessary trailing zeros (e.g. 2.0 → "2", 2.5 → "2.5")
            return str(int(f)) if f == int(f) else str(f)
        except (ValueError, TypeError):
            return str(value)
    return str(value)


def write_csv(
    records: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """
    Write a list of enriched ingredient records to a CSV file matching
    the original two-row header format.

    Args:
        records:      List of dicts. Each dict maps column index (int) → value.
                      Use build_record() to create correctly shaped dicts.
        output_path:  Destination file path (will create parent dirs).

    Returns:
        Absolute path of the written file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Row 0: numeric index row (blank string where index is None)
        writer.writerow(
            ["" if idx is None else str(idx) for idx in NUMERIC_INDEX]
        )

        # Row 1: column names
        writer.writerow(COLUMN_NAMES)

        # Data rows
        for record in records:
            row = []
            for col_idx, (col_name, _, col_type, default) in enumerate(COLUMNS):
                raw_val = record.get(col_idx, default)
                row.append(_format_value(raw_val, col_type))
            writer.writerow(row)

    return os.path.abspath(output_path)


def build_record(data: Dict[str, Any]) -> Dict[int, Any]:
    """
    Helper: build a record dict (keyed by column position) from a plain dict
    keyed by column name. When duplicate column names exist (e.g. "Description"),
    you can also pass integer keys directly to target specific positions.

    Example:
        build_record({
            "Ingredient name": "Niacinamide",
            "INCI Name": "Niacinamide",
            "Vegan": True,
            56: "Helps with redness.",   # Rosacea Description (col 56)
        })
    """
    # Build a name → [list of col indices] map to handle duplicates
    name_to_indices: Dict[str, List[int]] = {}
    for i, name in enumerate(COLUMN_NAMES):
        name_to_indices.setdefault(name, []).append(i)

    record: Dict[int, Any] = {}

    # Track how many times each name has been used (for duplicate resolution)
    name_use_count: Dict[str, int] = {}

    for key, value in data.items():
        if isinstance(key, int):
            # Direct positional key — use as-is
            record[key] = value
        else:
            indices = name_to_indices.get(key)
            if indices is None:
                raise KeyError(
                    f"Unknown column name: {repr(key)}. "
                    f"Use an integer index for duplicate column names."
                )
            use = name_use_count.get(key, 0)
            if use >= len(indices):
                raise IndexError(
                    f"Column {repr(key)} appears {len(indices)} time(s), "
                    f"but you provided {use + 1} values for it."
                )
            record[indices[use]] = value
            name_use_count[key] = use + 1

    return record
