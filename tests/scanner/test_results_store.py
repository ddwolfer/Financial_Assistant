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


# === 雙軌制結果存儲測試 ===


def test_save_dual_track_results():
    """SectorScreeningResult 物件可正確序列化存儲。"""
    from scripts.scanner.sector_screener import (
        SectorScreeningResult,
        SectorPercentiles,
    )

    result = SectorScreeningResult(
        symbol="DUAL",
        passed=True,
        screening_mode="dual_track",
        sector_percentiles=SectorPercentiles(
            pe_percentile=0.1,
            peg_percentile=0.2,
            roe_percentile=0.05,
            de_percentile=0.15,
            sector="Technology",
            sector_count=50,
        ),
        passed_sector_filter=True,
        passed_safety_filter=True,
        graham_number=100.0,
        current_price=80.0,
        margin_of_safety_pct=20.0,
        metrics=TickerMetrics(
            symbol="DUAL",
            trailing_pe=15.0,
            peg_ratio=0.8,
            roe=0.25,
            debt_to_equity=0.3,
            trailing_eps=5.0,
            book_value=30.0,
            current_price=80.0,
            sector="Technology",
            industry="Software",
            company_name="Dual Corp",
        ),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_screening_results([result], tag="layer1_dual", output_dir=Path(tmpdir))
        assert path.exists()

        loaded = load_latest_results(tag="layer1_dual", data_dir=Path(tmpdir))
        assert loaded is not None
        assert loaded["screening_mode"] == "dual_track"
        assert loaded["total_passed"] == 1

        r = loaded["results"][0]
        assert r["screening_mode"] == "dual_track"
        assert r["sector_percentiles"]["sector"] == "Technology"
        assert r["passed_sector_filter"] is True


def test_dual_track_result_has_mode_field():
    """JSON 輸出包含 screening_mode 欄位。"""
    from scripts.scanner.sector_screener import SectorScreeningResult

    result = SectorScreeningResult(
        symbol="MODE",
        passed=False,
        screening_mode="safety_only",
        metrics=TickerMetrics(symbol="MODE", trailing_eps=3.0),
        fail_reasons=["test"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_screening_results([result], tag="layer1_dual", output_dir=Path(tmpdir))
        loaded = load_latest_results(tag="layer1_dual", data_dir=Path(tmpdir))
        assert loaded["screening_mode"] == "dual_track"
