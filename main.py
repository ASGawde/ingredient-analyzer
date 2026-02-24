"""
main.py — Entry point for the ingredient analyzer pipeline.

Usage examples:
  # From a CSV file
  python main.py --csv path/to/ingredients.csv

  # From an XLSX file
  python main.py --xlsx path/to/ingredients.xlsx

  # Manual list
  python main.py --ingredients "Niacinamide" "Retinol" "Hyaluronic Acid"

  # Custom output path
  python main.py --csv input.csv --output results/my_output.csv
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# ── Ingestion ─────────────────────────────────────────────────────────────────
from ingestion.csv_reader    import read_csv
from ingestion.xlsx_reader   import read_xlsx
from ingestion.manual_input  import read_manual

# ── Enrichers ─────────────────────────────────────────────────────────────────
from enrichers.identity_enricher  import IdentityEnricher
from enrichers.safety_enricher    import SafetyEnricher
from enrichers.skin_type_enricher import SkinTypeEnricher
from enrichers.age_group_enricher import AgeGroupEnricher
from enrichers.dietary_enricher   import DietaryEnricher
from enrichers.concern_enricher   import ConcernEnricher
from enrichers.benefits_enricher  import BenefitsEnricher

# ── Output ────────────────────────────────────────────────────────────────────
from output.csv_writer import write_csv, build_record

# ── Config ────────────────────────────────────────────────────────────────────
from config import DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE, MAX_WORKERS


# Active enrichers — add/remove/reorder here as logic is implemented
ENRICHERS = [
    IdentityEnricher(),
    SafetyEnricher(),
    SkinTypeEnricher(),
    AgeGroupEnricher(),
    DietaryEnricher(),
    ConcernEnricher(),
    BenefitsEnricher(),
]


def process_ingredient(ingredient_name: str) -> Dict[int, Any]:
    """Run all enrichers on a single ingredient and merge the results."""
    merged: Dict[int, Any] = {}
    for enricher in ENRICHERS:
        partial = enricher.safe_enrich(ingredient_name)
        merged.update(partial)   # Later enrichers can override earlier ones
    return build_record(merged)


def run_pipeline(
    ingredients: List[str],
    output_path: str,
    workers: int = MAX_WORKERS,
) -> str:
    """
    Process a list of ingredients through all enrichers and write the output CSV.

    Args:
        ingredients:  List of ingredient name strings.
        output_path:  Destination CSV path.
        workers:      Number of parallel threads.

    Returns:
        Path to the written CSV file.
    """
    if not ingredients:
        print("No ingredients to process.")
        return ""

    print(f"Processing {len(ingredients)} ingredient(s) with {workers} worker(s)...")

    records: List[Dict[int, Any]] = [None] * len(ingredients)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {
            executor.submit(process_ingredient, name): i
            for i, name in enumerate(ingredients)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            ingredient = ingredients[idx]
            try:
                records[idx] = future.result()
                print(f"  ✓ {ingredient}")
            except Exception as e:
                print(f"  ✗ {ingredient}: {e}")
                records[idx] = build_record({0: ingredient})   # empty record with name

    output = write_csv(records, output_path)
    print(f"\nOutput written to: {output}")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingredient Analyzer — enrich cosmetic ingredient data into a structured CSV."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv",         metavar="FILE", help="Input CSV file path")
    source.add_argument("--xlsx",        metavar="FILE", help="Input XLSX file path")
    source.add_argument("--ingredients", metavar="NAME", nargs="+",
                        help="Ingredient names as positional arguments")

    parser.add_argument("--output",  metavar="FILE",
                        default=os.path.join(DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE),
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT_DIR}/{DEFAULT_OUTPUT_FILE})")
    parser.add_argument("--col",     metavar="COLNAME", default="Ingredient name",
                        help="Column name for ingredient names in CSV/XLSX input")
    parser.add_argument("--workers", metavar="N", type=int, default=MAX_WORKERS,
                        help=f"Parallel workers (default: {MAX_WORKERS})")

    return parser.parse_args()


def main():
    args = parse_args()

    # ── Load ingredients ──────────────────────────────────────────────────────
    if args.csv:
        if not os.path.exists(args.csv):
            print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
            sys.exit(1)
        ingredients = read_csv(args.csv, name_col=args.col)

    elif args.xlsx:
        if not os.path.exists(args.xlsx):
            print(f"Error: XLSX file not found: {args.xlsx}", file=sys.stderr)
            sys.exit(1)
        ingredients = read_xlsx(args.xlsx, name_col=args.col)

    else:
        ingredients = read_manual(args.ingredients)

    if not ingredients:
        print("Error: No ingredient names found in the provided input.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(ingredients)} ingredient(s).")

    run_pipeline(ingredients, output_path=args.output, workers=args.workers)


if __name__ == "__main__":
    main()
