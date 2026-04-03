"""
config.py — Central configuration for the ingredient analyzer pipeline.
"""

# ── Output ────────────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR  = "output"
DEFAULT_OUTPUT_FILE = "ingredients_analyzed.csv"

# ── Scraping (used by scrapers/cosing.py, scrapers/cosdna.py) ─────────────────
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS   = 1.0
MAX_RETRIES             = 3

USER_AGENT = (
    "Mozilla/5.0 (compatible; IngredientAnalyzer/1.0; "
    "+https://github.com/your-org/ingredient-analyzer)"
)

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_WORKERS = 4
