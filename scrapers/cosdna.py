"""
scrapers/cosdna.py — Scrape INCIDecoder for comedogenic and irritancy ratings.

Extracts:
  - Comedogenicity → col 8  (Comedogenic Rating, 0-5)
  - Irritancy      → col 4  (Risk of irritation, 0-3)

Source: INCIDecoder (incidecoder.com/ingredients/<slug>)
Data sourced from Fulton 1989 study — the gold standard comedogenic scale.

URL pattern: incidecoder.com/ingredients/<inci-name-lowercased-hyphenated>
e.g. Salicylic Acid → salicylic-acid
     Cetearyl Alcohol → cetearyl-alcohol

If ingredient not found or scores not present → cols stay blank.
"""

import asyncio
import re
from typing import Optional
from dataclasses import dataclass

INCIDECODER_BASE = "https://incidecoder.com/ingredients"


@dataclass
class CosdnaResult:
    ingredient_name: str
    found:           bool          = False
    acne_risk:       Optional[str] = None   # Comedogenicity 0-5
    irritant:        Optional[str] = None   # Irritancy 0-3
    safety:          Optional[str] = None   # not used from INCIDecoder
    url:             Optional[str] = None
    error:           Optional[str] = None


def _to_slug(name: str) -> str:
    """Convert INCI name to INCIDecoder URL slug."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


async def _scrape_one(ingredient: str, inci_name: Optional[str] = None) -> CosdnaResult:
    from playwright.async_api import async_playwright

    result = CosdnaResult(ingredient_name=ingredient)
    search_term = inci_name or ingredient

    # Try INCI name first, then original ingredient name
    slugs_to_try = list(dict.fromkeys([
        _to_slug(search_term),
        _to_slug(ingredient),
    ]))

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()

            for slug in slugs_to_try:
                url = f"{INCIDECODER_BASE}/{slug}"
                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=30_000)
                    await asyncio.sleep(1)

                    # Check if page exists (404 redirects to homepage)
                    current_url = page.url
                    if "ingredients" not in current_url or slug not in current_url:
                        continue

                    page_text = await page.inner_text("body")

                    # Check for valid ingredient page
                    if "Irritancy:" not in page_text and "Comedogenicity:" not in page_text:
                        continue

                    result.found = True
                    result.url   = url

                    # Parse Irritancy
                    irritancy_match = re.search(r"Irritancy:\s*([\d\-]+)", page_text)
                    if irritancy_match:
                        result.irritant = irritancy_match.group(1).strip()

                    # Parse Comedogenicity
                    comedogenic_match = re.search(r"Comedogenicity:\s*([\d\-]+)", page_text)
                    if comedogenic_match:
                        result.acne_risk = comedogenic_match.group(1).strip()

                    break

                except Exception:
                    continue

            await browser.close()

    except Exception as e:
        result.error = str(e)

    return result


_cache: dict = {}


def scrape_cosdna(ingredient: str, inci_name: Optional[str] = None) -> CosdnaResult:
    """Synchronous wrapper. Results cached per ingredient name."""
    key = (inci_name or ingredient).strip().lower()
    if key not in _cache:
        _cache[key] = asyncio.run(_scrape_one(ingredient, inci_name))
    return _cache[key]


def clear_cache() -> None:
    _cache.clear()