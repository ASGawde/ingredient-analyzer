"""
ingestion/xlsx_reader.py — Read ingredient names from an Excel (.xlsx) file.
"""

from typing import List, Optional


def read_xlsx(filepath: str, name_col: Optional[str] = "Ingredient name", sheet: int = 0) -> List[str]:
    """
    Read ingredient names from an Excel file.

    Args:
        filepath:  Path to the .xlsx file.
        name_col:  Column header name. If None, uses the first column.
        sheet:     Sheet index (0-based) or sheet name string.

    Returns:
        List of ingredient name strings (stripped, non-empty).
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required for XLSX reading. Run: pip install openpyxl")

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)

    if isinstance(sheet, int):
        ws = wb.worksheets[sheet]
    else:
        ws = wb[sheet]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header = [str(h).strip() if h is not None else "" for h in rows[0]]

    if name_col and name_col in header:
        col_idx = header.index(name_col)
        data_rows = rows[1:]
    else:
        col_idx = 0
        # Check if first row looks like a header
        first_val = str(rows[0][0]).strip().lower() if rows[0][0] else ""
        if first_val in ("ingredient name", "ingredient", "name", "inci name"):
            data_rows = rows[1:]
        else:
            data_rows = rows

    ingredients: List[str] = []
    for row in data_rows:
        if col_idx >= len(row):
            continue
        val = row[col_idx]
        if val is None:
            continue
        val = str(val).strip()
        if val:
            ingredients.append(val)

    wb.close()
    return ingredients
