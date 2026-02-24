"""
config.py — Central configuration for the ingredient analyzer pipeline.
"""

import os

# ── Output ────────────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR  = "output"
DEFAULT_OUTPUT_FILE = "ingredients_analyzed.csv"

# ── Scraping ──────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS   = 1.0   # Polite delay between requests to same domain
MAX_RETRIES             = 3

USER_AGENT = (
    "Mozilla/5.0 (compatible; IngredientAnalyzer/1.0; "
    "+https://github.com/your-org/ingredient-analyzer)"
)

# ── LLM (optional / future) ───────────────────────────────────────────────────
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL   = "claude-sonnet-4-6"
LLM_ENABLED = False   # Set to True to activate LLM fallback enrichers

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_WORKERS = 4   # Parallel threads for processing multiple ingredients
