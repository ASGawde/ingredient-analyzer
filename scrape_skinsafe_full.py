"""
scrape_skinsafe_full.py — One-time script to scrape ALL ingredients from SkinSafe.

Phase 1: Scrape all letter/pagination pages to collect ingredient names + URLs
Phase 2: Visit each ingredient page and scrape badge data

Output: data/skinsafe_db.csv
Columns:
    ingredient_name, url,
    irritant_free, teen_safe, fragrance_free, paraben_free, gluten_free,
    soy_free, nut_free, dairy_free, dye_free, silicon_free, sulphate_free,
    latex_free, sesame_free, citrus_free, seafood_free, vegan, vegetarian,
    paleo, unscented, scent_free

Usage:
    python3 scrape_skinsafe_full.py

Resume: safe to re-run — skips already scraped ingredients via checkpoint.
Checkpoints every 50 ingredients.
"""

import asyncio
import csv
import os
import re

SKINSAFE_BASE    = "https://www.skinsafeproducts.com"
OUTPUT_CSV       = "data/skinsafe_db.csv"
CHECKPOINT_FILE  = "data/skinsafe_checkpoint.txt"
LETTERS          = ["#"] + list("abcdefghijklmnopqrstuvwxyz")
PAGE_DELAY       = 1.0
BADGE_DELAY      = 3.0
MAX_PAGES        = 300
CHECKPOINT_EVERY = 50

# Active badge detection — image URLs contain these strings when badge is ON
BADGE_MAP = {
    "irritant_free":  ["irr-on"],
    "teen_safe":      ["teen-safe-on"],
    "fragrance_free": ["fragrance-on"],
    "paraben_free":   ["paraben-on"],
    "gluten_free":    ["gluten-on"],
    "soy_free":       ["soy-on"],
    "nut_free":       ["nut-free-on", "/nut-free"],
    "dairy_free":     ["dairy-on", "milk-free-on"],
    "dye_free":       ["dye-on"],
    "silicon_free":   ["silicone-on", "silicon-on"],
    "sulphate_free":  ["sls-on", "sulfate-on"],
    "latex_free":     ["latex-on"],
    "sesame_free":    ["sesame-on"],
    "citrus_free":    ["citrus-on"],
    "seafood_free":   ["seafood-on", "fish-free-on"],
    "vegan":          ["vegan-on"],
    "vegetarian":     ["vegetarian-on"],
    "paleo":          ["paleo-on"],
    "unscented":      ["unscented-on"],
    "scent_free":     ["scent-free-on"],
}

CSV_COLUMNS = [
    "ingredient_name", "url",
    "irritant_free", "teen_safe", "fragrance_free", "paraben_free",
    "gluten_free", "soy_free", "nut_free", "dairy_free", "dye_free",
    "silicon_free", "sulphate_free", "latex_free", "sesame_free",
    "citrus_free", "seafood_free", "vegan", "vegetarian", "paleo",
    "unscented", "scent_free",
]


def load_checkpoint() -> set:
    if not os.path.exists(CHECKPOINT_FILE):
        return set()
    with open(CHECKPOINT_FILE, encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_checkpoint_batch(slugs: list):
    with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f:
        for slug in slugs:
            f.write(slug + "\n")


async def scrape_listing_page(page, letter: str, page_num: int) -> tuple:
    letter_enc = "%23" if letter == "#" else letter
    url = f"{SKINSAFE_BASE}/ingredients?letter={letter_enc}"
    if page_num > 1:
        url += f"&page={page_num}"

    try:
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(1.5)
        content = await page.content()

        links = re.findall(
            r'href="/ingredients/([^"?#\s]+)"[^>]*>\s*([^<]{2,}?)\s*<',
            content
        )

        ingredients = []
        seen = set()
        for slug, name in links:
            slug = slug.strip()
            name = name.strip()
            if not slug or not name or slug in seen:
                continue
            if any(s in slug.lower() for s in ["letter=", "page=", "javascript"]):
                continue
            if len(name) < 2:
                continue
            seen.add(slug)
            ingredients.append((name, f"{SKINSAFE_BASE}/ingredients/{slug}", slug))

        has_next = (
            f"letter={letter_enc}&page={page_num + 1}" in content or
            f"letter={letter}&page={page_num + 1}" in content or
            "Next ›" in content
        )
        return ingredients, has_next

    except Exception as e:
        print(f"  [LISTING ERROR] letter={letter} page={page_num}: {e}")
        return [], False


async def collect_all_urls() -> list:
    from playwright.async_api import async_playwright

    all_ingredients = []
    seen = set()

    print("=== Phase 1: Collecting ingredient URLs ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()
        # Hide automation fingerprints
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for letter in LETTERS:
            print(f"  Letter {letter.upper()}:", end=" ", flush=True)
            page_num = 1
            count = 0

            while page_num <= MAX_PAGES:
                ingredients, has_next = await scrape_listing_page(page, letter, page_num)
                for name, url, slug in ingredients:
                    if slug not in seen:
                        seen.add(slug)
                        all_ingredients.append((name, url, slug))
                        count += 1

                if not has_next or not ingredients:
                    break
                page_num += 1
                await asyncio.sleep(PAGE_DELAY + random.uniform(0, 1))

            print(f"{count} ingredients, {page_num} pages")

        await browser.close()

    print(f"\nPhase 1 done: {len(all_ingredients)} total ingredients\n")
    return all_ingredients


def parse_badges(html: str) -> dict:
    html_lower = html.lower()
    badges = {}
    for key, keywords in BADGE_MAP.items():
        badges[key] = "Yes" if any(kw in html_lower for kw in keywords) else "No"
    return badges


async def scrape_ingredient_page(page, name: str, url: str) -> dict | None:
    result = {col: "" for col in CSV_COLUMNS}
    result["ingredient_name"] = name
    result["url"] = url

    try:
        await page.goto(url, wait_until="networkidle", timeout=25_000)
        await asyncio.sleep(1.5)
        html = await page.content()

        if "429" in html or "rate limit" in html.lower():
            return None  # Rate limited

        result.update(parse_badges(html))

    except Exception as e:
        print(f"  [ERROR] {name}: {e}")

    return result


async def scrape_all_badges(all_ingredients, done_slugs, writer, out_file):
    from playwright.async_api import async_playwright

    to_scrape = [(n, u, s) for n, u, s in all_ingredients if s not in done_slugs]
    total = len(to_scrape)
    print(f"=== Phase 2: Scraping badges for {total} ingredients ({len(done_slugs)} already done) ===\n")

    completed = 0
    consecutive_failures = 0
    batch_results = []
    batch_slugs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()
        # Hide automation fingerprints
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for name, url, slug in to_scrape:
            result = await scrape_ingredient_page(page, name, url)

            if result is None:
                consecutive_failures += 1
                wait = 30 * consecutive_failures
                print(f"  [RATE LIMITED] Waiting {wait}s...")
                await asyncio.sleep(wait)

                if consecutive_failures >= 3:
                    print("  [ABORT] Too many rate limits — saving and stopping. Re-run to resume.")
                    break

                result = await scrape_ingredient_page(page, name, url)
                if result is None:
                    print(f"  [SKIP] {name}")
                    continue
            else:
                consecutive_failures = 0

            batch_results.append(result)
            batch_slugs.append(slug)
            completed += 1
            print(f"  [{completed}/{total}] ✓ {name}")

            if len(batch_results) >= CHECKPOINT_EVERY:
                for r in batch_results:
                    writer.writerow([r.get(col, "") for col in CSV_COLUMNS])
                out_file.flush()
                save_checkpoint_batch(batch_slugs)
                done_slugs.update(batch_slugs)
                print(f"  [CHECKPOINT] {completed}/{total} saved\n")
                batch_results = []
                batch_slugs = []

            await asyncio.sleep(BADGE_DELAY + random.uniform(0, 2))

        # Final flush
        if batch_results:
            for r in batch_results:
                writer.writerow([r.get(col, "") for col in CSV_COLUMNS])
            out_file.flush()
            save_checkpoint_batch(batch_slugs)

        await browser.close()

    print(f"\nPhase 2 done: {completed}/{total} ingredients scraped")


async def main():
    os.makedirs("data", exist_ok=True)

    done_slugs = load_checkpoint()
    print(f"Resuming from checkpoint: {len(done_slugs)} already done\n")

    all_ingredients = await collect_all_urls()

    file_exists = os.path.exists(OUTPUT_CSV)
    out_file = open(OUTPUT_CSV, "a", newline="", encoding="utf-8")
    writer = csv.writer(out_file)
    if not file_exists:
        writer.writerow(CSV_COLUMNS)

    await scrape_all_badges(all_ingredients, done_slugs, writer, out_file)
    out_file.close()

    count = sum(1 for _ in open(OUTPUT_CSV, encoding="utf-8")) - 1
    print(f"\n✓ Complete! {count} ingredients in {OUTPUT_CSV}")


import sys
import random

if __name__ == "__main__":
    if "--test" in sys.argv:
        async def test():
            os.makedirs("data", exist_ok=True)
            test_slugs = [
                "niacinamide", "glycerin", "salicylic-acid", "retinol", "lanolin"
            ]
            test_ingredients = [
                (slug.replace("-", " ").title(),
                 f"{SKINSAFE_BASE}/ingredients/{slug}",
                 slug)
                for slug in test_slugs
            ]
            out_file = open("data/skinsafe_db_test.csv", "w", newline="", encoding="utf-8")
            writer = csv.writer(out_file)
            writer.writerow(CSV_COLUMNS)
            await scrape_all_badges(test_ingredients, set(), writer, out_file)
            out_file.close()
            print("Done — check data/skinsafe_db_test.csv")
        asyncio.run(test())
    else:
        asyncio.run(main())