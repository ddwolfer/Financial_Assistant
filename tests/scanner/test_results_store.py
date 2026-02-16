"""Tests for results persistence."""

import json
import tempfile
from pathlib import Path

from scripts.scanner.data_fetcher import TickerMetrics
from scripts.scanner.screener import screen_ticker
from scripts.scanner.results_store import save_screening_results, load_latest_results


def test_save_and_load_roundtrip():
    metrics = TickerMetrics(
        symbol="TEST",
        trailing_pe=10.0,
        peg_ratio=0.8,
        roe=0.20,
        debt_to_equity=0.3,
        trailing_eps=5.0,
        book_value=30.0,
        current_price=50.0,
    )
    result = screen_ticker(metrics)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_screening_results([result], output_dir=Path(tmpdir))
        assert path.exists()

        loaded = load_latest_results(data_dir=Path(tmpdir))
        assert loaded is not None
        assert loaded["total_screened"] == 1
        assert loaded["total_passed"] == 1
        assert loaded["results"][0]["symbol"] == "TEST"


def test_load_returns_none_when_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        loaded = load_latest_results(data_dir=Path(tmpdir))
        assert loaded is None
