"""
Stock universe providers.

Provides ticker lists for screening. Supports S&P 500 via Wikipedia
scraping and custom ticker lists from local files.
"""

from pathlib import Path
import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SP500_CACHE = _CACHE_DIR / "sp500_tickers.json"
_WIKIPEDIA_SP500_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
)


def get_sp500_tickers(use_cache: bool = True) -> list[str]:
    """
    Fetch S&P 500 ticker symbols.

    Scrapes Wikipedia's S&P 500 list. Results cached locally
    in data/sp500_tickers.json to avoid repeated network calls.
    """
    if use_cache and _SP500_CACHE.exists():
        logger.info("Loading S&P 500 tickers from cache: %s", _SP500_CACHE)
        with open(_SP500_CACHE) as f:
            return json.load(f)

    logger.info("Fetching S&P 500 tickers from Wikipedia...")
    tables = pd.read_html(_WIKIPEDIA_SP500_URL)
    df = tables[0]
    tickers = sorted(df["Symbol"].tolist())
    # Normalize: BRK.B -> BRK-B (yfinance format)
    tickers = [t.replace(".", "-") for t in tickers]

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_SP500_CACHE, "w") as f:
        json.dump(tickers, f, indent=2)
    logger.info("Cached %d tickers to %s", len(tickers), _SP500_CACHE)

    return tickers


def get_tickers_from_file(filepath: str | Path) -> list[str]:
    """Load tickers from a JSON file (list of strings)."""
    with open(filepath) as f:
        tickers = json.load(f)
    if not isinstance(tickers, list):
        raise ValueError(f"Expected a JSON list in {filepath}")
    return [str(t).upper().strip() for t in tickers]
