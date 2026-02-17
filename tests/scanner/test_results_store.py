"""Tests for results persistence."""

import json
import tempfile
import time
from pathlib import Path

from scripts.scanner.data_fetcher import TickerMetrics
from scripts.scanner.screener import screen_ticker
from scripts.scanner.results_store import (
    save_screening_results,
    load_latest_results,
    save_deep_analysis,
    load_latest_deep_analysis,
    load_latest_deep_analysis_report,
    list_deep_analysis_symbols,
)


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


# === Layer 3 深度分析結果持久化測試 ===


def _sample_json_data():
    """建立測試用深度分析 JSON 數據。"""
    return {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3e12,
        "valuation": {"ev_to_ebitda": 25.5, "trailing_pe": 30.0},
        "financial_health": {"current_ratio": 1.1},
        "growth_momentum": {"revenue_growth": 0.08},
        "risk_metrics": {"beta": 1.2},
    }


def _sample_markdown():
    """建立測試用 Markdown 報告。"""
    return """# 深度分析報告: Apple Inc. (AAPL)

> 產業: Technology > Consumer Electronics | 市值: $3.0T

## T6: 投資決策摘要
| 項目 | 數值 |
|------|------|
| 產業 | Technology |
| 市值 | $3.0T |
"""


def test_save_deep_analysis_creates_files():
    """save_deep_analysis 應建立 JSON 和 Markdown 檔案。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"

        paths = save_deep_analysis(
            symbol="AAPL",
            json_data=_sample_json_data(),
            markdown_report=_sample_markdown(),
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        assert paths["json_path"].exists()
        assert paths["markdown_path"].exists()
        assert "AAPL" in paths["json_path"].name
        assert "AAPL" in paths["markdown_path"].name
        assert paths["json_path"].suffix == ".json"
        assert paths["markdown_path"].suffix == ".md"


def test_save_deep_analysis_json_content():
    """JSON 檔案內容應與輸入一致。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"
        original = _sample_json_data()

        paths = save_deep_analysis(
            symbol="AAPL",
            json_data=original,
            markdown_report=_sample_markdown(),
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        with open(paths["json_path"], encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["symbol"] == "AAPL"
        assert loaded["company_name"] == "Apple Inc."
        assert loaded["valuation"]["ev_to_ebitda"] == 25.5


def test_save_deep_analysis_markdown_content():
    """Markdown 檔案內容應與輸入一致。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"
        md_text = _sample_markdown()

        paths = save_deep_analysis(
            symbol="AAPL",
            json_data=_sample_json_data(),
            markdown_report=md_text,
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        with open(paths["markdown_path"], encoding="utf-8") as f:
            loaded = f.read()

        assert loaded == md_text


def test_save_deep_analysis_symbol_uppercase():
    """股票代碼應統一轉大寫。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"

        paths = save_deep_analysis(
            symbol="aapl",
            json_data=_sample_json_data(),
            markdown_report=_sample_markdown(),
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        assert "AAPL" in paths["json_path"].name
        assert "AAPL" in paths["markdown_path"].name


def test_load_latest_deep_analysis_roundtrip():
    """save → load 往返應保持數據一致。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"

        save_deep_analysis(
            symbol="MSFT",
            json_data={"symbol": "MSFT", "pe": 30.0},
            markdown_report="# MSFT Report",
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        loaded = load_latest_deep_analysis("MSFT", data_dir=data_dir)
        assert loaded is not None
        assert loaded["symbol"] == "MSFT"
        assert loaded["pe"] == 30.0


def test_load_latest_deep_analysis_returns_none():
    """無對應檔案時應回傳 None。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        loaded = load_latest_deep_analysis("NONEXIST", data_dir=Path(tmpdir))
        assert loaded is None


def test_load_latest_deep_analysis_case_insensitive():
    """載入時股票代碼應不分大小寫。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"

        save_deep_analysis(
            symbol="aapl",
            json_data={"symbol": "AAPL", "value": 42},
            markdown_report="# AAPL",
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        loaded = load_latest_deep_analysis("AAPL", data_dir=data_dir)
        assert loaded is not None
        assert loaded["value"] == 42


def test_load_latest_deep_analysis_gets_newest():
    """多個版本時應載入最新的。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # 建立舊版本
        old_file = data_dir / "deep_analysis_TEST_20260101_000000.json"
        with open(old_file, "w") as f:
            json.dump({"symbol": "TEST", "version": "old"}, f)

        # 建立新版本
        new_file = data_dir / "deep_analysis_TEST_20260217_120000.json"
        with open(new_file, "w") as f:
            json.dump({"symbol": "TEST", "version": "new"}, f)

        loaded = load_latest_deep_analysis("TEST", data_dir=data_dir)
        assert loaded["version"] == "new"


def test_load_latest_deep_analysis_report_roundtrip():
    """save → load_report 往返應保持一致。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        reports_dir = Path(tmpdir) / "reports"
        md_text = "# GOOGL 深度分析\n\n好股票！"

        save_deep_analysis(
            symbol="GOOGL",
            json_data={"symbol": "GOOGL"},
            markdown_report=md_text,
            output_dir=data_dir,
            reports_dir=reports_dir,
        )

        loaded = load_latest_deep_analysis_report("GOOGL", reports_dir=reports_dir)
        assert loaded is not None
        assert loaded == md_text


def test_load_latest_deep_analysis_report_none():
    """無對應報告時應回傳 None。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        loaded = load_latest_deep_analysis_report("NONE", reports_dir=Path(tmpdir))
        assert loaded is None


def test_list_deep_analysis_symbols():
    """應列出所有已分析的股票代碼。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # 建立多個股票的分析檔案
        for sym in ["AAPL", "MSFT", "GOOGL"]:
            filepath = data_dir / f"deep_analysis_{sym}_20260217_100000.json"
            with open(filepath, "w") as f:
                json.dump({"symbol": sym}, f)

        # 建立同一股票的舊版本（不應重複列出）
        old_file = data_dir / "deep_analysis_AAPL_20260101_000000.json"
        with open(old_file, "w") as f:
            json.dump({"symbol": "AAPL"}, f)

        symbols = list_deep_analysis_symbols(data_dir=data_dir)
        assert symbols == ["AAPL", "GOOGL", "MSFT"]


def test_list_deep_analysis_symbols_empty():
    """無分析檔案時應回傳空列表。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        symbols = list_deep_analysis_symbols(data_dir=Path(tmpdir))
        assert symbols == []
