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
from ingestion.csv_reader import read_csv
from ingestion.xlsx_reader import read_xlsx
from ingestion.manual_input import read_manual

# ── Enrichers ─────────────────────────────────────────────────────────────────
from enrichers.cosing_inventory_enricher import CosingInventoryEnricher
from enrichers.identity_enricher import IdentityEnricher
from enrichers.safety_enricher import SafetyEnricher
from enrichers.skin_type_enricher import SkinTypeEnricher
from enrichers.age_group_enricher import AgeGroupEnricher
from enrichers.dietary_enricher import DietaryEnricher
from enrichers.skinsafe_db_enricher import SkinSafeDBEnricher
from enrichers.concern_enricher import ConcernEnricher
from enrichers.benefits_enricher import BenefitsEnricher
from enrichers.concentration_enricher import ConcentrationEnricher
from enrichers.cosdna_enricher import CosdnaEnricher
from enrichers.irritancy_enricher import IrrirancyEnricher
from enrichers.model_enricher import ModelEnricher

# ── Output ────────────────────────────────────────────────────────────────────
from output.csv_writer import build_record

# ── Config ────────────────────────────────────────────────────────────────────
from config import DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE, MAX_WORKERS


# CosIng inventory check — runs before scraper for fast lookup
INVENTORY_ENRICHER = CosingInventoryEnricher()

# Identity runs first (solo) so its INCI name is available to logic enrichers
IDENTITY_ENRICHER = IdentityEnricher()

# Model enricher runs last — needs the full merged record
MODEL_ENRICHER = ModelEnricher(model_path="model.pkl")

# Remaining enrichers — all support enrich_with_inci(ingredient_name, inci_name)
ENRICHERS = [
    SafetyEnricher(),
    SkinTypeEnricher(),
    AgeGroupEnricher(),
    DietaryEnricher(),
    SkinSafeDBEnricher(),
    ConcernEnricher(),
    BenefitsEnricher(),
    ConcentrationEnricher(),
    CosdnaEnricher(),
    IrrirancyEnricher(),
]


def process_ingredient(ingredient_name: str, prefilled_role: str = None) -> Dict[int, Any]:
    """
    Run the full pipeline for one ingredient:
      1. IdentityEnricher first → scrapes INCI name from CosIng
      2. All other enrichers    → receive inci_name so logic modules can use it
      3. ModelEnricher last     → reads full merged record, predicts skin type
                                  and skin concern columns
    """
    merged: Dict[int, Any] = {}

    # Always write ingredient name to col 0
    merged[0] = ingredient_name

    # Pre-fill role if provided from input CSV — run through role mapping first
    if prefilled_role:
        from enrichers.safety_enricher import _map_cosing_role
        mapped = _map_cosing_role(prefilled_role)
        merged[5] = mapped if mapped else prefilled_role
        merged[94] = prefilled_role.upper()

    # Step 0: CosIng inventory lookup (fast CSV, 30k ingredients)
    inventory = INVENTORY_ENRICHER.enrich_with_inci(ingredient_name, ingredient_name)
    merged.update(inventory)
    inci_name = merged.get(1) or ingredient_name

    # Step 1: identity scraper — only if inventory didn't find INCI name
    # Skip CosIng scraping entirely if role is already known (from input CSV)
    if not merged.get(1) and not merged.get(5):
        identity = IDENTITY_ENRICHER.safe_enrich(ingredient_name)
        merged.update(identity)
        inci_name = merged.get(1) or ingredient_name   # col 1 = INCI Name

    # Step 2: remaining enrichers with inci_name context
    for enricher in ENRICHERS:
        try:
            if isinstance(enricher, (ConcentrationEnricher, IrrirancyEnricher)):
                # Pass role from col 5 for role-based logic
                partial = enricher.enrich_with_inci(ingredient_name, inci_name, role=merged.get(5))
            else:
                partial = enricher.enrich_with_inci(ingredient_name, inci_name)
        except Exception as e:
            print(f"[{enricher.__class__.__name__}] enrich_with_inci failed: {e}")
            try:
                partial = enricher.safe_enrich(ingredient_name)
            except Exception as e2:
                print(f"[{enricher.__class__.__name__}] safe_enrich also failed: {e2}")
                partial = {}
        merged.update(partial)

    # Step 3: model enricher — runs on fully populated merged record
    try:
        model_predictions = MODEL_ENRICHER.enrich_with_record(merged)
        merged.update(model_predictions)
    except Exception as e:
        print(f"[ModelEnricher] failed: {e}")

    # Write raw CosIng role to the named column at the end
    from schema import COLUMN_NAMES
    raw_role = merged.get(94)
    if raw_role:
        try:
            raw_role_idx = len(COLUMN_NAMES) - 1  # last column
            merged[raw_role_idx] = raw_role
        except Exception:
            pass

    return build_record(merged)


def run_pipeline(
    ingredients: List,
    output_path: str,
    workers: int = MAX_WORKERS,
    checkpoint_every: int = 100,
) -> str:
    if not ingredients:
        print("No ingredients to process.")
        return ""

    # ── Checkpoint support ────────────────────────────────────────────────────
    checkpoint_path = output_path + ".checkpoint"
    done_names: set = set()

    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                done_names = set(line.strip().lower() for line in f if line.strip())
            print(f"  Resuming from checkpoint — {len(done_names)} already done")
        except Exception as e:
            print(f"  Could not load checkpoint: {e}")

    # Filter out already done
    remaining = [
        ing for ing in ingredients
        if (ing["name"] if isinstance(ing, dict) else ing).strip().lower()
        not in done_names
    ]

    print(f"Processing {len(remaining)} ingredient(s) ({len(done_names)} already done) with {workers} worker(s)...")

    all_records: List = []
    batch: List = []
    completed = 0

    # Write headers if fresh start
    if not done_names:
        from schema import COLUMN_NAMES, NUMERIC_INDEX
        import csv as _csv
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            writer.writerow(["" if idx is None else str(idx) for idx in NUMERIC_INDEX])
            writer.writerow(COLUMN_NAMES)

    def _flush_batch(batch_records):
        """Append batch records to output CSV and update checkpoint."""
        import csv as _csv
        from schema import COLUMNS
        valid = [r for r in batch_records if r is not None]
        if not valid:
            return
        with open(output_path, "a", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            for record in valid:
                row = []
                for col_idx, (col_name, _, col_type, default) in enumerate(COLUMNS):
                    raw_val = record.get(col_idx, default)
                    if raw_val is None or raw_val == "":
                        row.append("")
                    elif col_type == "float":
                        try:
                            fv = float(raw_val)
                            row.append(str(int(fv)) if fv == int(fv) else str(fv))
                        except (ValueError, TypeError):
                            row.append(str(raw_val))
                    else:
                        row.append(str(raw_val))
                writer.writerow(row)
        # Update checkpoint file
        with open(checkpoint_path, "a", encoding="utf-8") as f:
            for record in valid:
                name = record.get(0, "")
                if name:
                    f.write(name.strip() + "\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_ing = {
            executor.submit(
                process_ingredient,
                ing["name"] if isinstance(ing, dict) else ing,
                ing.get("role") if isinstance(ing, dict) else None,
            ): ing
            for ing in remaining
        }
        for future in as_completed(future_to_ing):
            ing = future_to_ing[future]
            ing_name = ing["name"] if isinstance(ing, dict) else ing
            try:
                record = future.result()
                batch.append(record)
                print(f"  ✓ {ing_name}")
            except Exception as e:
                print(f"  ✗ {ing_name}: {e}")
                batch.append(build_record({0: ing_name}))

            completed += 1
            if completed % checkpoint_every == 0:
                _flush_batch(batch)
                batch = []
                print(f"  [Checkpoint] {completed}/{len(remaining)} saved")

    # Flush remaining
    if batch:
        _flush_batch(batch)

    # Clean up checkpoint on success
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    output = os.path.abspath(output_path)
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
    parser.add_argument("--no-scrape", action="store_true",
                        help="Disable live CosIng Playwright scraper")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.no_scrape:
        import enrichers.identity_enricher as _id_mod
        import enrichers.safety_enricher as _safety_mod
        _id_mod._scraping_disabled = True
        _safety_mod._scraping_disabled = True
        print("Live scrapers disabled (--no-scrape)")

    if args.csv:
        if not os.path.exists(args.csv):
            print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
            sys.exit(1)
        ingredients = read_csv(args.csv, name_col=args.col)
        # Handle both old (list of strings) and new (list of dicts) format
        if ingredients and isinstance(ingredients[0], str):
            ingredients = [{"name": i} for i in ingredients]

    elif args.xlsx:
        if not os.path.exists(args.xlsx):
            print(f"Error: XLSX file not found: {args.xlsx}", file=sys.stderr)
            sys.exit(1)
        ingredients = read_xlsx(args.xlsx, name_col=args.col)
        if ingredients and isinstance(ingredients[0], str):
            ingredients = [{"name": i} for i in ingredients]

    else:
        ingredients = [{"name": i} for i in read_manual(args.ingredients)]

    if not ingredients:
        print("Error: No ingredient names found in the provided input.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(ingredients)} ingredient(s).")
    run_pipeline(ingredients, output_path=args.output, workers=args.workers)


if __name__ == "__main__":
    main()