"""Tests for the Layer 1 quantitative screener."""

import pytest

from scripts.scanner.config import ScreeningThresholds
from scripts.scanner.data_fetcher import TickerMetrics
from scripts.scanner.screener import screen_ticker, screen_batch


def _make_metrics(symbol="TEST", **kwargs):
    """Helper: create TickerMetrics with all-passing defaults."""
    defaults = dict(
        symbol=symbol,
        trailing_pe=10.0,
        peg_ratio=0.8,
        roe=0.20,
        debt_to_equity=0.3,
        trailing_eps=5.0,
        book_value=30.0,
        current_price=50.0,
        earnings_growth=0.20,
    )
    defaults.update(kwargs)
    return TickerMetrics(**defaults)


class TestScreenTicker:
    def test_all_passing(self):
        metrics = _make_metrics()
        result = screen_ticker(metrics)
        assert result.passed is True
        assert len(result.fail_reasons) == 0
        assert result.graham_number is not None

    def test_pe_too_high(self):
        metrics = _make_metrics(trailing_pe=20.0)
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("P/E" in r for r in result.fail_reasons)

    def test_peg_too_high(self):
        metrics = _make_metrics(peg_ratio=1.5)
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("PEG" in r for r in result.fail_reasons)

    def test_roe_too_low(self):
        metrics = _make_metrics(roe=0.10)
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("ROE" in r for r in result.fail_reasons)

    def test_debt_equity_too_high(self):
        metrics = _make_metrics(debt_to_equity=0.8)
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("D/E" in r for r in result.fail_reasons)

    def test_missing_pe_fails(self):
        metrics = _make_metrics(trailing_pe=None)
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("P/E" in r and "unavailable" in r for r in result.fail_reasons)

    def test_invalid_data_fails(self):
        metrics = TickerMetrics(
            symbol="BAD",
            fetch_error="No data returned",
        )
        result = screen_ticker(metrics)
        assert result.passed is False
        assert any("Invalid data" in r for r in result.fail_reasons)

    def test_custom_thresholds(self):
        """Relaxed thresholds allow values that default would reject."""
        metrics = _make_metrics(trailing_pe=20.0, debt_to_equity=0.8)
        relaxed = ScreeningThresholds(pe_ratio_max=25.0, debt_to_equity_max=1.0)
        result = screen_ticker(metrics, thresholds=relaxed)
        assert result.passed is True

    def test_margin_of_safety_calculation(self):
        # Graham = sqrt(22.5 * 5 * 30) ≈ 58.09
        # Price = 50.0
        # MOS = (58.09 - 50) / 58.09 * 100 ≈ 13.9%
        metrics = _make_metrics(current_price=50.0)
        result = screen_ticker(metrics)
        assert result.margin_of_safety_pct is not None
        assert result.margin_of_safety_pct > 0

    def test_to_dict_serialization(self):
        metrics = _make_metrics()
        result = screen_ticker(metrics)
        d = result.to_dict()
        assert d["symbol"] == "TEST"
        assert d["passed"] is True
        assert "metrics" in d
        assert d["metrics"]["trailing_pe"] == 10.0


class TestScreenBatch:
    def test_sorting_order(self):
        """Passed tickers first, sorted by margin of safety descending."""
        m1 = _make_metrics("CHEAP", current_price=30.0)
        m2 = _make_metrics("FAIR", current_price=55.0)
        m3 = _make_metrics("FAIL", trailing_pe=99.0)

        results = screen_batch([m3, m1, m2])
        assert results[0].symbol == "CHEAP"
        assert results[1].symbol == "FAIR"
        assert results[2].symbol == "FAIL"
        assert results[2].passed is False
