"""
股票清單載入器。

提供篩選用的股票代碼清單。支援從 Wikipedia 抓取 S&P 500 成分股，
以及從本地 JSON 檔案載入自訂清單。
"""

from io import StringIO
from pathlib import Path
import json
import logging
import ssl

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SP500_CACHE = _CACHE_DIR / "sp500_tickers.json"
_WIKIPEDIA_SP500_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
)


def get_sp500_tickers(use_cache: bool = True) -> list[str]:
    """
    取得 S&P 500 成分股代碼。

    透過 requests 從 Wikipedia 抓取（避免 macOS SSL 憑證問題），
    結果快取至 data/sp500_tickers.json。
    """
    if use_cache and _SP500_CACHE.exists():
        logger.info("從快取載入 S&P 500 清單: %s", _SP500_CACHE)
        with open(_SP500_CACHE) as f:
            return json.load(f)

    logger.info("從 Wikipedia 抓取 S&P 500 清單...")
    # 使用 requests（內建 certifi）避免系統 SSL 憑證問題
    # Wikipedia 會封鎖預設 User-Agent，需設定合理的標頭
    headers = {"User-Agent": "QuantAnalystAgent/1.0 (financial screening tool)"}
    response = requests.get(_WIKIPEDIA_SP500_URL, headers=headers, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    df = tables[0]
    tickers = sorted(df["Symbol"].tolist())
    # 正規化：BRK.B -> BRK-B（yfinance 格式）
    tickers = [t.replace(".", "-") for t in tickers]

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_SP500_CACHE, "w") as f:
        json.dump(tickers, f, indent=2)
    logger.info("已快取 %d 支股票至 %s", len(tickers), _SP500_CACHE)

    return tickers


def get_tickers_from_file(filepath: str | Path) -> list[str]:
    """從 JSON 檔案載入股票代碼清單。"""
    with open(filepath) as f:
        tickers = json.load(f)
    if not isinstance(tickers, list):
        raise ValueError(f"預期 JSON 列表，但 {filepath} 格式不符")
    return [str(t).upper().strip() for t in tickers]
