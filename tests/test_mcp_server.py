"""Smoke tests for the MCP financial tools server."""

import pytest
from unittest.mock import patch

from scripts.scanner.data_fetcher import fetch_ticker_metrics
from scripts.scanner.config import calculate_graham_number
from scripts.scanner.screener import screen_ticker


def _mock_info(**overrides):
    base = {
        "quoteType": "EQUITY",
        "shortName": "Apple Inc.",
        "trailingPE": 28.0,
        "forwardPE": 25.0,
        "pegRatio": None,
        "returnOnEquity": 0.15,
        "debtToEquity": 80.0,
        "trailingEps": 6.5,
        "bookValue": 4.0,
        "currentPrice": 190.0,
        "earningsGrowth": 0.10,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3_000_000_000_000,
    }
    base.update(overrides)
    return base


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_fetch_missing_data_logic(mock_ticker_cls):
    """The fetch_missing_data logic returns structured data."""
    mock_ticker_cls.return_value.info = _mock_info()

    # Test the underlying logic directly (MCP wraps it)
    metrics = fetch_ticker_metrics("AAPL")

    assert metrics.symbol == "AAPL"
    assert metrics.trailing_pe == 28.0
    assert metrics.debt_to_equity == pytest.approx(0.8)

    graham = None
    if metrics.trailing_eps and metrics.book_value:
        graham = calculate_graham_number(metrics.trailing_eps, metrics.book_value)
    assert graham is not None


@patch("scripts.scanner.data_fetcher.yf.Ticker")
def test_calculate_financial_metrics_logic(mock_ticker_cls):
    """The calculate_financial_metrics logic returns screening results."""
    mock_ticker_cls.return_value.info = _mock_info(
        trailingPE=10.0,
        pegRatio=0.8,
        returnOnEquity=0.25,
        debtToEquity=30.0,
        trailingEps=5.0,
        bookValue=30.0,
        currentPrice=50.0,
        earningsGrowth=0.20,
    )

    metrics = fetch_ticker_metrics("VALUE")
    result = screen_ticker(metrics)

    assert result.passed is True
    assert result.graham_number is not None


def test_mcp_server_has_tools():
    """The MCP server registers the expected tools."""
    from mcp_servers.financial_tools import mcp

    tool_names = [t.name for t in mcp._tool_manager._tools.values()]
    assert "check_data_cache" in tool_names
    assert "fetch_missing_data" in tool_names
    assert "calculate_financial_metrics" in tool_names
