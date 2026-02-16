"""Tests for the data fetcher module."""

from unittest.mock import patch, MagicMock

import pytest

from scripts.scanner.data_fetcher import (
    fetch_ticker_metrics,
    TickerMetrics,
)


def _mock_info(**overrides):
    """Build a mock yfinance info dict with sensible defaults."""
    base = {
        "quoteType": "EQUITY",
        "shortName": "Test Corp",
        "trailingPE": 12.5,
        "forwardPE": 10.0,
        "pegRatio": None,
        "returnOnEquity": 0.25,
        "debtToEquity": 45.0,  # yfinance returns as percentage
        "trailingEps": 5.0,
        "bookValue": 30.0,
        "currentPrice": 100.0,
        "earningsGrowth": 0.20,
        "sector": "Technology",
        "industry": "Software",
        "marketCap": 1_000_000_000,
    }
    base.update(overrides)
    return base


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_basic_fetch(mock_ticker_cls):
    """Fetches and normalizes metrics correctly."""
    mock_ticker_cls.return_value.info = _mock_info()
    result = fetch_ticker_metrics("TEST", use_cache=False)

    assert result.symbol == "TEST"
    assert result.trailing_pe == 12.5
    assert result.roe == 0.25
    # debtToEquity should be normalized from percentage to ratio
    assert result.debt_to_equity == pytest.approx(0.45)
    assert result.is_valid is True


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_peg_fallback_calculation(mock_ticker_cls):
    """When pegRatio is None, calculates from PE and earnings growth."""
    mock_ticker_cls.return_value.info = _mock_info(
        pegRatio=None,
        trailingPE=20.0,
        earningsGrowth=0.25,
    )
    result = fetch_ticker_metrics("TEST", use_cache=False)
    # PEG = 20.0 / (0.25 * 100) = 20 / 25 = 0.8
    assert result.peg_ratio == pytest.approx(0.8)


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_peg_native_value_preferred(mock_ticker_cls):
    """When pegRatio is present, uses native value."""
    mock_ticker_cls.return_value.info = _mock_info(pegRatio=1.5)
    result = fetch_ticker_metrics("TEST", use_cache=False)
    assert result.peg_ratio == 1.5


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_empty_info_returns_error(mock_ticker_cls):
    """Empty info dict produces a fetch error."""
    mock_ticker_cls.return_value.info = {}
    result = fetch_ticker_metrics("FAKE", use_cache=False)
    assert result.fetch_error is not None
    assert result.is_valid is False


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_exception_retries(mock_ticker_cls):
    """Retries on exception, then returns error."""
    mock_ticker_cls.side_effect = [
        Exception("rate limit"),
        Exception("rate limit"),
        Exception("rate limit"),
    ]
    result = fetch_ticker_metrics("FAIL", retry_count=2, retry_delay=0.01, use_cache=False)
    assert result.fetch_error is not None


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_missing_optional_fields(mock_ticker_cls):
    """Missing optional fields default to None, no crash."""
    mock_ticker_cls.return_value.info = _mock_info(
        returnOnEquity=None,
        debtToEquity=None,
        earningsGrowth=None,
    )
    result = fetch_ticker_metrics("PARTIAL", use_cache=False)
    assert result.roe is None
    assert result.debt_to_equity is None
    assert result.peg_ratio is None
    assert result.is_valid is True


# === TickerMetrics 序列化測試 ===


def test_ticker_metrics_to_dict_roundtrip():
    """to_dict() → from_dict() 的往返正確性。"""
    original = TickerMetrics(
        symbol="ROUND",
        trailing_pe=15.0,
        forward_pe=13.0,
        peg_ratio=0.8,
        roe=0.20,
        debt_to_equity=0.45,
        trailing_eps=5.0,
        book_value=30.0,
        current_price=100.0,
        earnings_growth=0.15,
        sector="Technology",
        industry="Software",
        market_cap=1_000_000_000,
        company_name="Roundtrip Corp",
    )
    restored = TickerMetrics.from_dict(original.to_dict())
    assert restored == original


def test_ticker_metrics_from_dict_with_error():
    """from_dict 正確還原含 fetch_error 的物件。"""
    m = TickerMetrics(symbol="ERR", fetch_error="Connection timeout")
    restored = TickerMetrics.from_dict(m.to_dict())
    assert restored.fetch_error == "Connection timeout"
    assert restored.is_valid is False


def test_ticker_metrics_from_dict_missing_fields():
    """from_dict 遇到缺欄位時不 crash，以 None 填充。"""
    # 模擬舊版快取只有 symbol 和 trailing_pe
    minimal = {"symbol": "OLD", "trailing_pe": 12.0}
    restored = TickerMetrics.from_dict(minimal)
    assert restored.symbol == "OLD"
    assert restored.trailing_pe == 12.0
    assert restored.roe is None
    assert restored.fetch_error is None
