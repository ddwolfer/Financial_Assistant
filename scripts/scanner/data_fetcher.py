"""
Financial data fetcher using yfinance.

Handles API errors, rate limits, missing data, and the known
pegRatio issue (broken since June 2025).
"""

from dataclasses import dataclass
from typing import Optional
import logging
import time

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class TickerMetrics:
    """Raw financial metrics for a single ticker."""

    symbol: str
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    trailing_eps: Optional[float] = None
    book_value: Optional[float] = None
    current_price: Optional[float] = None
    earnings_growth: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    company_name: Optional[str] = None
    fetch_error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if minimum required metrics were fetched."""
        return self.fetch_error is None and self.trailing_eps is not None

    def to_dict(self) -> dict:
        """序列化為字典，供 JSON 快取儲存。"""
        return {
            "symbol": self.symbol,
            "trailing_pe": self.trailing_pe,
            "forward_pe": self.forward_pe,
            "peg_ratio": self.peg_ratio,
            "roe": self.roe,
            "debt_to_equity": self.debt_to_equity,
            "trailing_eps": self.trailing_eps,
            "book_value": self.book_value,
            "current_price": self.current_price,
            "earnings_growth": self.earnings_growth,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "company_name": self.company_name,
            "fetch_error": self.fetch_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TickerMetrics":
        """從字典反序列化為 TickerMetrics，使用 get() 確保向後相容。"""
        return cls(
            symbol=data["symbol"],
            trailing_pe=data.get("trailing_pe"),
            forward_pe=data.get("forward_pe"),
            peg_ratio=data.get("peg_ratio"),
            roe=data.get("roe"),
            debt_to_equity=data.get("debt_to_equity"),
            trailing_eps=data.get("trailing_eps"),
            book_value=data.get("book_value"),
            current_price=data.get("current_price"),
            earnings_growth=data.get("earnings_growth"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            market_cap=data.get("market_cap"),
            company_name=data.get("company_name"),
            fetch_error=data.get("fetch_error"),
        )


def _fetch_from_yfinance(
    symbol: str,
    retry_count: int = 2,
    retry_delay: float = 1.0,
) -> TickerMetrics:
    """
    從 yfinance API 抓取單一股票的指標（內部函數，不含快取邏輯）。

    處理缺失欄位、PEG Ratio 備用計算，以及 debtToEquity 正規化。
    """
    for attempt in range(retry_count + 1):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("quoteType") is None:
                return TickerMetrics(
                    symbol=symbol,
                    fetch_error=f"No data returned for {symbol}",
                )

            raw_de = info.get("debtToEquity")
            debt_to_equity = raw_de / 100.0 if raw_de is not None else None

            peg = info.get("pegRatio")
            trailing_pe = info.get("trailingPE")
            earnings_growth = info.get("earningsGrowth")

            if peg is None and trailing_pe and earnings_growth:
                growth_pct = earnings_growth * 100
                if growth_pct > 0:
                    peg = trailing_pe / growth_pct

            return TickerMetrics(
                symbol=symbol,
                trailing_pe=trailing_pe,
                forward_pe=info.get("forwardPE"),
                peg_ratio=peg,
                roe=info.get("returnOnEquity"),
                debt_to_equity=debt_to_equity,
                trailing_eps=info.get("trailingEps"),
                book_value=info.get("bookValue"),
                current_price=info.get("currentPrice"),
                earnings_growth=earnings_growth,
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                company_name=info.get("shortName"),
            )

        except Exception as e:
            if attempt < retry_count:
                delay = retry_delay * (2**attempt)
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                    attempt + 1,
                    retry_count + 1,
                    symbol,
                    e,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error("All attempts failed for %s: %s", symbol, e)
                return TickerMetrics(symbol=symbol, fetch_error=str(e))

    return TickerMetrics(symbol=symbol, fetch_error="Unknown error")


def fetch_ticker_metrics(
    symbol: str,
    retry_count: int = 2,
    retry_delay: float = 1.0,
    use_cache: bool = True,
    _cache=None,
) -> TickerMetrics:
    """
    抓取單一股票的指標，支援本地快取。

    Args:
        symbol: 股票代碼
        retry_count: 失敗重試次數
        retry_delay: 重試間隔（秒）
        use_cache: 是否使用本地快取（預設 True）
        _cache: 內部參數，批次操作時傳入共用 MetricsCache 實例
    """
    # 延遲 import 避免循環依賴
    from scripts.scanner.metrics_cache import MetricsCache

    # 快取查詢
    own_cache = False
    if use_cache:
        if _cache is None:
            _cache = MetricsCache()
            _cache.load()
            own_cache = True  # 標記為自行建立的快取實例
        cached = _cache.get(symbol)
        if cached is not None:
            return cached

    # 從 yfinance 抓取
    result = _fetch_from_yfinance(symbol, retry_count, retry_delay)

    # 寫入快取
    if use_cache and _cache is not None:
        _cache.put(result)
        # 單獨呼叫時自行管理存檔；批次模式由外部統一存檔
        if own_cache:
            _cache.save()

    return result


def fetch_batch_metrics(
    symbols: list[str],
    delay_between: float = 0.1,
    progress_callback=None,
    use_cache: bool = True,
) -> list[TickerMetrics]:
    """
    批次抓取指標，自動使用快取。

    快取最佳化：載入一次 → 篩選需抓取的標的 → 抓取 → 合併 → 存檔一次。
    """
    from scripts.scanner.metrics_cache import MetricsCache

    cache = MetricsCache() if use_cache else None
    if cache:
        cache.load()

    total = len(symbols)
    # 第一階段：檢查快取，分組為「命中」和「需抓取」
    cached_results: list[tuple[int, TickerMetrics]] = []
    fetch_needed: list[tuple[int, str]] = []

    for i, symbol in enumerate(symbols):
        if cache:
            cached = cache.get(symbol)
            if cached is not None:
                cached_results.append((i, cached))
                continue
        fetch_needed.append((i, symbol))

    cache_hits = len(cached_results)
    if cache:
        logger.info(
            "快取統計: %d 命中 / %d 需抓取 / %d 總計",
            cache_hits, len(fetch_needed), total,
        )

    # 第二階段：從 API 抓取缺失/過期的資料
    fetched_results: list[tuple[int, TickerMetrics]] = []
    for fetch_idx, (original_idx, symbol) in enumerate(fetch_needed):
        metrics = _fetch_from_yfinance(symbol)
        fetched_results.append((original_idx, metrics))

        if cache:
            cache.put(metrics)

        if progress_callback:
            # 進度 = 快取命中數 + 已抓取數
            progress_callback(cache_hits + fetch_idx + 1, total)

        if fetch_idx < len(fetch_needed) - 1:
            time.sleep(delay_between)

    # 快取命中的部分也要報告進度（一次性跳到命中數）
    if cache and cache_hits > 0 and progress_callback and len(fetch_needed) == 0:
        progress_callback(total, total)

    # 第三階段：存檔並依原始順序排列
    if cache:
        cache.save()

    all_results = cached_results + fetched_results
    all_results.sort(key=lambda pair: pair[0])
    return [metrics for _, metrics in all_results]
