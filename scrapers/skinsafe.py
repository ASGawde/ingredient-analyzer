"""
scrapers/skinsafe.py — Scrape SkinSafe for ingredient badge data.

Approach:
  1. Call JSON search API to get the ingredient page URL
  2. Load that URL with Playwright to get badge data
"""

import asyncio
import requests
from typing import Optional
from dataclasses import dataclass

SKINSAFE_BASE    = "https://www.skinsafeproducts.com"
SKINSAFE_API     = "https://www.skinsafeproducts.com/users/search"

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

_UI_SKIP = {
    "sign in", "register", "brands", "category", "premium",
    "explore", "trial", "subscribe", "log in", "search",
    "home", "ingredients", "products", "contact", "about",
    "teen safe", "vegan", "vegetarian", "paraben", "gluten",
    "sulfate", "silicone", "fragrance", "view all", "show more",
}


def _lookup_ingredient_url(ingredient: str) -> Optional[str]:
    """
    Call the SkinSafe search API and return the URL of the first
    ingredient suggestion. Returns None if not found.
    """
    try:
        resp = requests.get(
            SKINSAFE_API,
            params={"query": ingredient},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        for suggestion in data.get("suggestions", []):
            if suggestion.get("landing_page") == "ingredient":
                return SKINSAFE_BASE + suggestion["url"]

    except Exception as e:
        print(f"  [SkinSafe API] lookup failed for '{ingredient}': {e}")

    return None


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
    lines = [l.strip() for l in page_text.split("\n") if l.strip()]
    ing_upper = ingredient.upper()

    heading_idx = None
    for i, line in enumerate(lines):
        if line.upper() == ing_upper or line.upper().startswith(ing_upper):
            heading_idx = i
            break

    search_lines = lines[heading_idx + 1:] if heading_idx is not None else lines

    for line in search_lines:
        if len(line) < 60:
            continue
        if any(skip in line.lower() for skip in _UI_SKIP):
            continue
        if sum(1 for c in line if c.isupper()) > len(line) * 0.5:
            continue
        return line[:500]

    return None


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


async def _scrape_one_with_browser(browser, ingredient: str) -> SkinsafeResult:
    result = SkinsafeResult(ingredient_name=ingredient)

    # ── Step 1: get URL from API (no browser needed) ──────────────────────────
    url = _lookup_ingredient_url(ingredient)
    if not url:
        for field_name in _BADGE_KEYWORDS:
            setattr(result, field_name, "Not found")
        return result

    # ── Step 2: load ingredient page with Playwright ──────────────────────────
    try:
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(2)

        page_text = await page.inner_text("body")
        await page.close()

        result.found = True
        text_lower = page_text.lower()

        result.description = _extract_description(page_text, ingredient)

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
        try:
            await page.close()
        except Exception:
            pass
        result.error = str(e)
        for field_name in _BADGE_KEYWORDS:
            setattr(result, field_name, "Not found")

    return result


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


_cache: dict = {}


def scrape_skinsafe(ingredient: str) -> SkinsafeResult:
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
    to_scrape = [i for i in ingredients if i.strip().lower() not in _cache]

    if to_scrape:
        fresh = asyncio.run(_scrape_batch(to_scrape, delay_seconds))
        for r in fresh:
            _cache[r.ingredient_name.strip().lower()] = r

    return [_cache[i.strip().lower()] for i in ingredients]


def clear_cache() -> None:
    _cache.clear()