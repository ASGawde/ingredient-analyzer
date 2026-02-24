"""
scrapers/cosing.py — Scrape the EU CosIng database for ingredient data.

Extracts:
  - INCI Name        → col 1
  - INN name/Aliases → col 2
  - Functions        → col 5  (Role in formulation)
  - Description      → col 6  (Note)

Uses Playwright for JS-rendered pages.
Install: pip install playwright && playwright install chromium
"""

import asyncio
from typing import Optional
from dataclasses import dataclass

COSING_URL = "https://ec.europa.eu/growth/tools-databases/cosing/"


@dataclass
class CosingResult:
    ingredient_name: str
    inci_name:        Optional[str] = None
    aliases:          Optional[str] = None   # INN name
    role:             Optional[str] = None   # Functions
    description:      Optional[str] = None
    cas_no:           Optional[str] = None
    ec_no:            Optional[str] = None
    restriction:      Optional[str] = None
    found:            bool = False
    error:            Optional[str] = None


def _clean_search_term(ingredient: str) -> str:
    """Strip parenthetical content for better CosIng search matching."""
    return ingredient.split("(")[0].strip()


async def _parse_detail_page(page) -> dict:
    """
    Parse the CosIng detail page by reading each table row as a label/value pair.
    Reading table cells directly (rather than inner_text of the whole body) means
    empty cells stay empty — no bleed-through from adjacent rows.
    """
    data = {}

    rows = await page.query_selector_all("table tr")
    for row in rows:
        cells = await row.query_selector_all("td, th")
        if not cells:
            continue

        label = (await cells[0].inner_text()).strip().lower()
        raw_value = (await cells[1].inner_text()).strip() if len(cells) >= 2 else ""

        if not label:
            continue

        if label == "inci name":
            data["inci_name"] = raw_value or None

        elif label == "description":
            data["description"] = raw_value or None

        elif label == "cas #":
            data["cas_no"] = raw_value or None

        elif label == "ec #":
            data["ec_no"] = raw_value or None

        elif label == "inn name":
            data["aliases"] = raw_value or None

        elif label == "functions":
            # Functions render as bullet <li> items inside the cell
            items = await cells[1].query_selector_all("li") if len(cells) >= 2 else []
            if items:
                texts = [(await li.inner_text()).strip() for li in items]
                data["role"] = ", ".join(t for t in texts if t)
            elif raw_value:
                data["role"] = raw_value

        elif "cosmetics regulation provisions" in label:
            data["restriction"] = raw_value or None

    return data


async def _scrape_one(ingredient: str) -> CosingResult:
    """Async scrape of a single ingredient from CosIng."""
    from playwright.async_api import async_playwright

    result = CosingResult(ingredient_name=ingredient)
    search_term = _clean_search_term(ingredient)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(COSING_URL, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)

            # ── Search ────────────────────────────────────────────────────────
            await page.fill('input[type="text"]', search_term)
            await asyncio.sleep(1)
            await page.click('button[type="submit"]')
            await asyncio.sleep(3)

            page_text = await page.inner_text("body")

            if "Total: 0" in page_text:
                await browser.close()
                return result  # Not found

            # ── Click first exact-match result link ───────────────────────────
            # Target the INCI Name column links in the results table only,
            # matching the full search term (uppercased) to avoid partial matches
            # like "NIACINAMIDE/YEAST POLYPEPTIDE" when searching "niacinamide"
            target = search_term.upper()
            links = await page.query_selector_all("table a")
            clicked = False

            for link in links:
                try:
                    link_text = (await link.inner_text()).strip().upper()
                    if link_text == target:
                        await link.click()
                        await asyncio.sleep(3)
                        clicked = True
                        break
                except Exception:
                    continue

            # Fallback: first link that starts with the first word
            if not clicked:
                first_word = target.split()[0]
                links = await page.query_selector_all("table a")
                for link in links:
                    try:
                        link_text = (await link.inner_text()).strip().upper()
                        if link_text.startswith(first_word):
                            await link.click()
                            await asyncio.sleep(3)
                            clicked = True
                            break
                    except Exception:
                        continue

            if not clicked:
                await browser.close()
                return result

            # ── Parse detail page via table cells ─────────────────────────────
            parsed = await _parse_detail_page(page)

            result.found       = True
            result.inci_name   = parsed.get("inci_name")
            result.aliases     = parsed.get("aliases")
            result.role        = parsed.get("role")
            result.description = parsed.get("description")
            result.cas_no      = parsed.get("cas_no")
            result.ec_no       = parsed.get("ec_no")
            result.restriction = parsed.get("restriction")

            await browser.close()

    except Exception as e:
        result.error = str(e)

    return result


_cache: dict = {}


def scrape_cosing(ingredient: str) -> CosingResult:
    """
    Synchronous wrapper — call this from enrichers.
    Results are cached by ingredient name so multiple enrichers sharing
    the same ingredient never trigger more than one browser session.
    """
    key = ingredient.strip().lower()
    if key not in _cache:
        _cache[key] = asyncio.run(_scrape_one(ingredient))
    return _cache[key]


def clear_cache() -> None:
    """Clear the in-memory scrape cache (useful between pipeline runs)."""
    _cache.clear()


async def scrape_cosing_batch(
    ingredients: list,
    delay_seconds: float = 2.0,
) -> list:
    """
    Scrape multiple ingredients sequentially with a polite delay.
    Returns results in the same order as the input list.
    """
    results = []
    total = len(ingredients)

    for i, ingredient in enumerate(ingredients):
        print(f"  [{i+1}/{total}] CosIng: {ingredient[:60]}...")
        result = await _scrape_one(ingredient)

        if result.found:
            role_preview = (result.role or "")[:50]
            print(f"         ✓ found — {role_preview}")
        elif result.error:
            print(f"         ✗ error — {result.error}")
        else:
            print(f"         ✗ not found")

        results.append(result)
        await asyncio.sleep(delay_seconds)

    return results


def scrape_cosing_batch_sync(
    ingredients: list,
    delay_seconds: float = 2.0,
) -> list:
    """Synchronous wrapper for batch scraping."""
    return asyncio.run(scrape_cosing_batch(ingredients, delay_seconds))