"""
scrapers/skinsafe.py — Scrape SkinSafe for ingredient badge data.

Extracts:
  - Teen safe        → col 31
  - Vegetarian       → col 37
  - Vegan            → col 38
  - Gluten-free      → col 39
  - Paleo            → col 40
  - Unscented        → col 41
  - Paraben-free     → col 42
  - Sulphate-free    → col 43
  - Silicon-free     → col 44
  - Nut-free         → col 45
  - Soy-free         → col 46
  - Latex-free       → col 47
  - Sesame-free      → col 48
  - Citrus-free      → col 49
  - Dye-free         → col 50
  - Fragrance-free   → col 51
  - Scent-free       → col 52
  - Seafood-free     → col 53
  - Dairy-free       → col 54
  - Description      → col 6 (fallback when CosIng has none)

Badge values:
  "Yes"       — badge present on SkinSafe page
  "No"        — ingredient name contains a known keyword for that category
  "Not found" — ingredient not found on SkinSafe at all
  None        — found on SkinSafe but no signal either way

Uses Playwright (single shared browser across batch for efficiency).
Install: pip install playwright && playwright install chromium
"""

import asyncio
from typing import Optional
from dataclasses import dataclass


SKINSAFE_BASE = "https://www.skinsafeproducts.com/ingredients"

# Badge keyword checks against page text
_BADGE_KEYWORDS: dict = {
    "teen":           ["teen safe"],
    "vegetarian":     ["vegetarian"],
    "vegan":          ["vegan"],
    "gluten_free":    ["gluten free", "gluten-free"],
    "paleo":          ["paleo"],
    "unscented":      ["unscented"],
    "paraben_free":   ["paraben free", "paraben-free"],
    "sulphate_free":  ["sulfate free", "sulphate free", "sls free"],
    "silicon_free":   ["silicone free", "silicon free"],
    "nut_free":       ["nut free", "nut-free"],
    "soy_free":       ["soy free", "soy-free"],
    "latex_free":     ["latex free", "latex-free"],
    "sesame_free":    ["sesame free", "sesame-free"],
    "citrus_free":    ["citrus free", "citrus-free"],
    "dye_free":       ["dye free", "dye-free"],
    "fragrance_free": ["fragrance free", "fragrance-free"],
    "scent_free":     ["scent free", "scent-free"],
    "seafood_free":   ["seafood free", "fish free"],
    "dairy_free":     ["dairy free", "lactose free", "milk free"],
}

# If ingredient name contains these → mark field as "No"
_NAME_CONTAINS_NO: dict = {
    "gluten_free":    ["wheat", "barley", "gluten", "triticum"],
    "nut_free":       ["almond", "walnut", "hazelnut", "cashew", "pistachio",
                       "macadamia", "jojoba"],
    "soy_free":       ["soy", "soja", "glycine soja"],
    "dairy_free":     ["milk", "lactose", "casein", "whey"],
    "sesame_free":    ["sesame", "sesamum"],
    "citrus_free":    ["citrus", "lemon", "orange", "grapefruit", "lime",
                       "bergamot", "tangerine", "reticulata", "limon"],
    "seafood_free":   ["fish", "marine", "seaweed", "algae"],
    "fragrance_free": ["fragrance", "parfum", "perfume"],
    "silicon_free":   ["silicone", "dimethicone", "cyclomethicone", "siloxane"],
}

# Lines containing these strings are UI chrome, not descriptions
_UI_SKIP = {
    "sign in", "register", "brands", "category", "premium",
    "explore", "trial", "subscribe", "log in", "search",
    "home", "ingredients", "products", "contact", "about",
    "teen safe", "vegan", "vegetarian", "paraben", "gluten",
    "sulfate", "silicone", "fragrance", "view all", "show more",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ingredient_to_slug(ingredient: str) -> str:
    return (
        ingredient.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
    )


def _apply_name_based_nos(ingredient: str, badges: dict) -> dict:
    ing_lower = ingredient.lower()
    for field_name, keywords in _NAME_CONTAINS_NO.items():
        if badges.get(field_name) is None:
            for kw in keywords:
                if kw in ing_lower:
                    badges[field_name] = "No"
                    break
    return badges


def _extract_description(page_text: str, ingredient: str) -> Optional[str]:
    """
    Find the first substantial plain-text paragraph after the ingredient
    name heading on the SkinSafe page.
    """
    lines = [l.strip() for l in page_text.split("\n") if l.strip()]
    ing_upper = ingredient.upper()

    # Find the heading line
    heading_idx = None
    for i, line in enumerate(lines):
        if line.upper() == ing_upper or line.upper().startswith(ing_upper):
            heading_idx = i
            break

    search_lines = lines[heading_idx + 1:] if heading_idx is not None else lines

    for line in search_lines:
        if len(line) < 60:
            continue
        line_lower = line.lower()
        if any(skip in line_lower for skip in _UI_SKIP):
            continue
        # Skip lines that are mostly uppercase (badges/labels)
        if sum(1 for c in line if c.isupper()) > len(line) * 0.5:
            continue
        return line[:500]

    return None


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class SkinsafeResult:
    ingredient_name: str
    found:           bool = False
    description:     Optional[str] = None
    teen:            Optional[str] = None
    vegetarian:      Optional[str] = None
    vegan:           Optional[str] = None
    gluten_free:     Optional[str] = None
    paleo:           Optional[str] = None
    unscented:       Optional[str] = None
    paraben_free:    Optional[str] = None
    sulphate_free:   Optional[str] = None
    silicon_free:    Optional[str] = None
    nut_free:        Optional[str] = None
    soy_free:        Optional[str] = None
    latex_free:      Optional[str] = None
    sesame_free:     Optional[str] = None
    citrus_free:     Optional[str] = None
    dye_free:        Optional[str] = None
    fragrance_free:  Optional[str] = None
    scent_free:      Optional[str] = None
    seafood_free:    Optional[str] = None
    dairy_free:      Optional[str] = None
    error:           Optional[str] = None


# ── Core scraper ──────────────────────────────────────────────────────────────

async def _scrape_one_with_browser(browser, ingredient: str) -> SkinsafeResult:
    """Scrape a single ingredient using an already-open browser instance."""
    result = SkinsafeResult(ingredient_name=ingredient)
    slug = _ingredient_to_slug(ingredient)
    url = f"{SKINSAFE_BASE}/{slug}"

    try:
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(2)

        page_text = await page.inner_text("body")
        await page.close()

        # Not found
        if "not found" in page_text.lower() or "404" in page_text:
            for field_name in _BADGE_KEYWORDS:
                setattr(result, field_name, "Not found")
            return result

        result.found = True
        text_lower = page_text.lower()

        # Description
        result.description = _extract_description(page_text, ingredient)

        # Badge checks
        badges: dict = {}
        for field_name, keywords in _BADGE_KEYWORDS.items():
            badges[field_name] = None
            for kw in keywords:
                if kw in text_lower:
                    badges[field_name] = "Yes"
                    break

        badges = _apply_name_based_nos(ingredient, badges)

        for field_name, value in badges.items():
            setattr(result, field_name, value)

    except Exception as e:
        result.error = str(e)
        for field_name in _BADGE_KEYWORDS:
            setattr(result, field_name, "Not found")

    return result


# ── Batch scraper ─────────────────────────────────────────────────────────────

async def _scrape_batch(ingredients: list, delay_seconds: float = 1.0) -> list:
    from playwright.async_api import async_playwright

    results = []
    total = len(ingredients)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for i, ingredient in enumerate(ingredients):
            print(f"  [{i+1}/{total}] SkinSafe: {ingredient[:60]}...")
            result = await _scrape_one_with_browser(browser, ingredient)

            if result.found:
                print(f"           ✓ found")
            elif result.error:
                print(f"           ✗ error — {result.error}")
            else:
                print(f"           ✗ not found")

            results.append(result)
            await asyncio.sleep(delay_seconds)

        await browser.close()

    return results


# ── Cache + public API ────────────────────────────────────────────────────────

_cache: dict = {}


def scrape_skinsafe(ingredient: str) -> SkinsafeResult:
    """Sync, cached. Opens its own browser."""
    key = ingredient.strip().lower()
    if key in _cache:
        return _cache[key]

    async def _run():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            r = await _scrape_one_with_browser(browser, ingredient)
            await browser.close()
            return r

    result = asyncio.run(_run())
    _cache[key] = result
    return result


def scrape_skinsafe_batch_sync(ingredients: list, delay_seconds: float = 1.0) -> list:
    """Sync batch — shares one browser. Updates cache."""
    to_scrape = [i for i in ingredients if i.strip().lower() not in _cache]

    if to_scrape:
        fresh = asyncio.run(_scrape_batch(to_scrape, delay_seconds))
        for r in fresh:
            _cache[r.ingredient_name.strip().lower()] = r

    return [_cache[i.strip().lower()] for i in ingredients]


def clear_cache() -> None:
    _cache.clear()