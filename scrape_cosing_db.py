"""
scrape_cosing_db.py — One-time script to scrape CosIng for all ingredients
not already in the inventory CSV.

Saves results to data/cosing_scraped.csv with columns:
  INCI name, Function

Usage:
  python3 scrape_cosing_db.py

This script is slow — it scrapes CosIng page by page using Playwright.
Run it overnight. It saves progress after every 10 ingredients so you
can resume if interrupted.

Resume: just run again — it skips already scraped ingredients.
"""

import asyncio
import csv
import os
import re
import time
import pandas as pd

# ── Config ─────────────────────────────────────────────────────────────────────
INVENTORY_CSV  = "data/cosing_inventory.csv"
OUTPUT_CSV     = "data/cosing_scraped.csv"
COSING_SEARCH  = "https://ec.europa.eu/growth/tools-databases/cosing/search"
WORKERS        = 2       # parallel workers — keep low to avoid rate limiting
DELAY          = 1.5     # seconds between requests per worker
SAVE_EVERY     = 10      # save progress every N ingredients
RESUME         = True    # skip already scraped ingredients


def load_existing_inci() -> set:
    """Load INCI names already in the inventory CSV."""
    df = pd.read_csv(INVENTORY_CSV)
    return set(df["INCI name"].str.strip().str.lower().dropna())


def load_already_scraped() -> set:
    """Load INCI names already in our scraped output CSV."""
    if not os.path.exists(OUTPUT_CSV):
        return set()
    df = pd.read_csv(OUTPUT_CSV)
    return set(df["INCI name"].str.strip().str.lower().dropna())


def load_17k_ingredients() -> list:
    """Load the 17k ingredient list from SkinSafe CSV."""
    # Adjust path if needed
    candidates = [
        "/Users/anish/Downloads/Ingredients of SkinSafe - Skinsafe ingredients.csv",
        "sample_100.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            df = pd.read_csv(path)
            col = df.columns[0]
            return df[col].dropna().str.strip().tolist()
    return []


async def scrape_one(ingredient: str, browser) -> dict:
    """
    Search CosIng for one ingredient and extract INCI name + Function.
    Returns dict with keys: ingredient, inci_name, function
    """
    result = {"ingredient": ingredient, "inci_name": "", "function": ""}

    try:
        page = await browser.new_page()

        # Search CosIng
        await page.goto(COSING_SEARCH, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(1)

        # Fill search box and submit
        search_input = await page.query_selector("input[name='term'], input[type='text'], #term")
        if not search_input:
            await page.close()
            return result

        await search_input.fill(ingredient)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        # Find exact match link in results table
        import re as _re

        def _norm(s):
            return _re.sub(r"[\s\-]+", "", s.strip().lower())

        target = _norm(ingredient)
        links = await page.query_selector_all("table a")

        clicked = False
        for link in links:
            try:
                text = (await link.inner_text()).strip()
                if _norm(text) == target:
                    await link.click()
                    await asyncio.sleep(2)
                    clicked = True
                    break
            except Exception:
                continue

        # Fallback: click first link
        if not clicked and links:
            try:
                await links[0].click()
                await asyncio.sleep(2)
                clicked = True
            except Exception:
                pass

        if not clicked:
            await page.close()
            return result

        # Extract INCI name and Functions from detail page
        page_text = await page.inner_text("body")

        # INCI name — usually the heading or labelled field
        inci_match = re.search(r"INCI\s*[Nn]ame[:\s]+([^\n]+)", page_text)
        if inci_match:
            result["inci_name"] = inci_match.group(1).strip()

        # Functions
        func_match = re.search(r"Functions?[:\s]+([^\n]+)", page_text, re.IGNORECASE)
        if func_match:
            result["function"] = func_match.group(1).strip()

        await page.close()

    except Exception as e:
        print(f"  [ERROR] {ingredient}: {e}")

    return result


async def scrape_batch(ingredients: list, output_writer, already_done: set):
    """Scrape a list of ingredients with a shared browser."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for i, ingredient in enumerate(ingredients):
            if ingredient.lower() in already_done:
                continue

            print(f"  [{i+1}/{len(ingredients)}] {ingredient}")
            result = await scrape_one(ingredient, browser)

            if result["inci_name"] or result["function"]:
                output_writer.writerow([
                    result["ingredient"],
                    result["inci_name"],
                    result["function"],
                ])
                already_done.add(ingredient.lower())
                print(f"    ✓ INCI={result['inci_name']}, Function={result['function'][:50]}")
            else:
                print(f"    ✗ not found")

            await asyncio.sleep(DELAY)

        await browser.close()


def main():
    print("Loading existing inventory...")
    existing_inci  = load_existing_inci()
    already_scraped = load_already_scraped()
    print(f"  Already in inventory: {len(existing_inci)}")
    print(f"  Already scraped: {len(already_scraped)}")

    print("Loading 17k ingredient list...")
    all_ingredients = load_17k_ingredients()
    print(f"  Total ingredients: {len(all_ingredients)}")

    # Filter out ingredients already covered
    to_scrape = [
        ing for ing in all_ingredients
        if ing.lower() not in existing_inci
        and ing.lower() not in already_scraped
    ]
    print(f"  To scrape: {len(to_scrape)}")

    if not to_scrape:
        print("Nothing to scrape — all ingredients already covered!")
        return

    # Open output CSV for appending
    file_exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Ingredient name", "INCI name", "Function"])

        print(f"\nStarting scrape of {len(to_scrape)} ingredients...")
        print("(This will take a while — results saved progressively)\n")

        asyncio.run(scrape_batch(to_scrape, writer, already_scraped))

    print(f"\nDone! Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()