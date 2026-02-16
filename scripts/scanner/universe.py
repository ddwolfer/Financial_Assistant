"""
股票清單載入器。

提供篩選用的股票代碼清單。支援從 Wikipedia 抓取 S&P 500/400/600 成分股，
合併為 S&P 1500，以及從本地 JSON 檔案載入自訂清單。
"""

from io import StringIO
from pathlib import Path
import json
import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# S&P 500 大型股
_SP500_CACHE = _CACHE_DIR / "sp500_tickers.json"
_WIKIPEDIA_SP500_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
)

# S&P MidCap 400 中型股
_SP400_CACHE = _CACHE_DIR / "sp400_tickers.json"
_WIKIPEDIA_SP400_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
)

# S&P SmallCap 600 小型股
_SP600_CACHE = _CACHE_DIR / "sp600_tickers.json"
_WIKIPEDIA_SP600_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
)


def _fetch_wikipedia_tickers(
    url: str,
    cache_path: Path,
    label: str,
    use_cache: bool = True,
) -> list[str]:
    """
    從 Wikipedia 抓取股票代碼清單的共用邏輯。

    透過 requests（內建 certifi）避免 macOS SSL 憑證問題，
    結果快取至指定的 JSON 檔案。
    """
    if use_cache and cache_path.exists():
        logger.info("從快取載入 %s 清單: %s", label, cache_path)
        with open(cache_path) as f:
            return json.load(f)

    logger.info("從 Wikipedia 抓取 %s 清單...", label)
    # Wikipedia 會封鎖預設 User-Agent，需設定合理的標頭
    headers = {"User-Agent": "QuantAnalystAgent/1.0 (financial screening tool)"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    df = tables[0]
    tickers = sorted(df["Symbol"].tolist())
    # 正規化：BRK.B -> BRK-B（yfinance 格式）
    tickers = [t.replace(".", "-") for t in tickers]

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(tickers, f, indent=2)
    logger.info("已快取 %d 支股票至 %s", len(tickers), cache_path)

    return tickers


def get_sp500_tickers(use_cache: bool = True) -> list[str]:
    """取得 S&P 500 大型股成分股代碼。"""
    return _fetch_wikipedia_tickers(
        _WIKIPEDIA_SP500_URL, _SP500_CACHE, "S&P 500", use_cache
    )


def get_sp400_tickers(use_cache: bool = True) -> list[str]:
    """取得 S&P MidCap 400 中型股成分股代碼。"""
    return _fetch_wikipedia_tickers(
        _WIKIPEDIA_SP400_URL, _SP400_CACHE, "S&P 400", use_cache
    )


def get_sp600_tickers(use_cache: bool = True) -> list[str]:
    """取得 S&P SmallCap 600 小型股成分股代碼。"""
    return _fetch_wikipedia_tickers(
        _WIKIPEDIA_SP600_URL, _SP600_CACHE, "S&P 600", use_cache
    )


def get_sp1500_tickers(use_cache: bool = True) -> list[str]:
    """
    取得 S&P 1500 成分股代碼（S&P 500 + 400 + 600 聯集，去重複）。

    不另外快取——由三個子清單各自快取後合併。
    """
    all_tickers = (
        get_sp500_tickers(use_cache)
        + get_sp400_tickers(use_cache)
        + get_sp600_tickers(use_cache)
    )
    return sorted(set(all_tickers))


def get_tickers_from_file(filepath: str | Path) -> list[str]:
    """從 JSON 檔案載入股票代碼清單。"""
    with open(filepath) as f:
        tickers = json.load(f)
    if not isinstance(tickers, list):
        raise ValueError(f"預期 JSON 列表，但 {filepath} 格式不符")
    return [str(t).upper().strip() for t in tickers]
