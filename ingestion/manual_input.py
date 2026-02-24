"""
ingestion/manual_input.py — Accept a list of ingredient names directly.
"""

from typing import List


def read_manual(ingredients: List[str]) -> List[str]:
    """
    Validate and clean a manually provided list of ingredient names.

    Args:
        ingredients: Raw list of ingredient name strings.

    Returns:
        Cleaned list (stripped, non-empty, deduplicated while preserving order).
    """
    seen = set()
    result: List[str] = []
    for name in ingredients:
        cleaned = str(name).strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            result.append(cleaned)
    return result
