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


def fetch_ticker_metrics(
    symbol: str,
    retry_count: int = 2,
    retry_delay: float = 1.0,
) -> TickerMetrics:
    """
    Fetch financial metrics for a single ticker from yfinance.

    Handles missing fields, PEG ratio fallback calculation,
    and debtToEquity normalization (percentage -> ratio).
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


def fetch_batch_metrics(
    symbols: list[str],
    delay_between: float = 0.1,
    progress_callback=None,
) -> list[TickerMetrics]:
    """
    Fetch metrics for a batch of tickers with rate limiting.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        metrics = fetch_ticker_metrics(symbol)
        results.append(metrics)

        if progress_callback:
            progress_callback(i + 1, total)

        if i < total - 1:
            time.sleep(delay_between)

    return results
