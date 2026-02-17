"""
Layer 3 CLI 進入點測試。

測試參數解析、Layer 1 結果載入、摘要輸出。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.analyzer.run_layer3 import (
    _load_layer1_passed_tickers,
    _print_summary,
    main,
)


class TestLoadLayer1PassedTickers:
    """Layer 1 結果載入測試。"""

    @patch("scripts.analyzer.run_layer3.load_latest_results")
    def test_loads_dual_track_first(self, mock_load):
        """應優先載入雙軌制結果。"""
        mock_load.side_effect = lambda tag: {
            "layer1_dual": {
                "total_screened": 500,
                "results": [
                    {"symbol": "AAPL", "passed": True},
                    {"symbol": "MSFT", "passed": True},
                    {"symbol": "GOOGL", "passed": False},
                ],
            },
            "layer1": None,
        }.get(tag)

        tickers = _load_layer1_passed_tickers()
        assert tickers == ["AAPL", "MSFT"]

    @patch("scripts.analyzer.run_layer3.load_latest_results")
    def test_falls_back_to_absolute(self, mock_load):
        """雙軌制無結果時應回退到絕對門檻。"""
        mock_load.side_effect = lambda tag: {
            "layer1_dual": None,
            "layer1": {
                "total_screened": 100,
                "results": [
                    {"symbol": "DELL", "passed": True},
                ],
            },
        }.get(tag)

        tickers = _load_layer1_passed_tickers()
        assert tickers == ["DELL"]

    @patch("scripts.analyzer.run_layer3.load_latest_results")
    def test_returns_empty_when_no_results(self, mock_load):
        """無任何結果時應回傳空列表。"""
        mock_load.return_value = None
        tickers = _load_layer1_passed_tickers()
        assert tickers == []

    @patch("scripts.analyzer.run_layer3.load_latest_results")
    def test_all_failed_returns_empty(self, mock_load):
        """所有股票都未通過時應回傳空列表。"""
        mock_load.side_effect = lambda tag: {
            "layer1_dual": {
                "total_screened": 500,
                "results": [
                    {"symbol": "FAIL1", "passed": False},
                    {"symbol": "FAIL2", "passed": False},
                ],
            },
        }.get(tag)

        tickers = _load_layer1_passed_tickers()
        assert tickers == []


class TestPrintSummary:
    """摘要輸出測試。"""

    def test_empty_results(self, capsys):
        """空結果應顯示警告。"""
        _print_summary([])
        captured = capsys.readouterr()
        assert "沒有成功完成分析" in captured.out

    def test_normal_results(self, capsys):
        """正常結果應包含股票代碼和價格。"""
        results = [
            {
                "summary": {
                    "symbol": "AAPL",
                    "company_name": "Apple Inc.",
                    "current_price": 150.0,
                    "target_price": 180.0,
                    "upside_pct": 20.0,
                    "recommendation": "buy",
                    "data_quality_score": 0.85,
                },
            }
        ]
        _print_summary(results)
        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "$150.00" in captured.out
        assert "$180.00" in captured.out
        assert "+20.0%" in captured.out
        assert "BUY" in captured.out

    def test_none_values(self, capsys):
        """None 值應顯示 N/A。"""
        results = [
            {
                "summary": {
                    "symbol": "TEST",
                    "company_name": None,
                    "current_price": None,
                    "target_price": None,
                    "upside_pct": None,
                    "recommendation": None,
                    "data_quality_score": 0,
                },
            }
        ]
        _print_summary(results)
        captured = capsys.readouterr()
        assert "TEST" in captured.out
        assert "N/A" in captured.out


class TestMainArgParsing:
    """main() 參數解析測試。"""

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_tickers_arg(self, mock_cache, mock_analyze):
        """--tickers 應正確傳遞。"""
        mock_analyze.return_value = {
            "summary": {"symbol": "AAPL", "company_name": "Apple", "current_price": 150,
                        "target_price": 180, "upside_pct": 20, "recommendation": "buy",
                        "data_quality_score": 0.85},
            "json_data": {},
            "markdown_report": "",
        }

        with patch("sys.argv", ["run_layer3", "--tickers", "AAPL"]):
            main()

        mock_analyze.assert_called_once()
        call_kwargs = mock_analyze.call_args
        assert call_kwargs[1]["symbol"] == "AAPL" or call_kwargs[0][0] == "AAPL"

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    @patch("scripts.analyzer.run_layer3._load_layer1_passed_tickers")
    def test_from_layer1_arg(self, mock_load, mock_cache, mock_analyze):
        """--from-layer1 應從 Layer 1 結果載入。"""
        mock_load.return_value = ["MSFT", "DELL"]
        mock_analyze.return_value = {
            "summary": {"symbol": "MSFT", "company_name": "Microsoft",
                        "current_price": 300, "target_price": 350, "upside_pct": 16.7,
                        "recommendation": "buy", "data_quality_score": 0.9},
            "json_data": {},
            "markdown_report": "",
        }

        with patch("sys.argv", ["run_layer3", "--from-layer1"]):
            main()

        mock_load.assert_called_once()
        assert mock_analyze.call_count == 2  # MSFT + DELL

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_force_refresh_disables_cache(self, mock_cache, mock_analyze):
        """--force-refresh 應停用快取。"""
        mock_analyze.return_value = None

        with patch("sys.argv", ["run_layer3", "--tickers", "AAPL", "--force-refresh"]):
            main()

        # use_cache=False 應傳入
        call_kwargs = mock_analyze.call_args[1]
        assert call_kwargs["use_cache"] is False

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_universe_arg(self, mock_cache, mock_analyze):
        """--universe 應正確傳遞。"""
        mock_analyze.return_value = None

        with patch("sys.argv", ["run_layer3", "--tickers", "AAPL", "--universe", "sp1500"]):
            main()

        call_kwargs = mock_analyze.call_args[1]
        assert call_kwargs["universe"] == "sp1500"

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_peer_count_arg(self, mock_cache, mock_analyze):
        """--peer-count 應正確傳遞。"""
        mock_analyze.return_value = None

        with patch("sys.argv", ["run_layer3", "--tickers", "AAPL", "--peer-count", "10"]):
            main()

        call_kwargs = mock_analyze.call_args[1]
        assert call_kwargs["peer_count"] == 10

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_tickers_uppercased(self, mock_cache, mock_analyze):
        """股票代碼應統一轉大寫。"""
        mock_analyze.return_value = None

        with patch("sys.argv", ["run_layer3", "--tickers", "aapl", "msft"]):
            main()

        calls = mock_analyze.call_args_list
        symbols = [c[1]["symbol"] for c in calls]
        assert symbols == ["AAPL", "MSFT"]

    @patch("scripts.analyzer.run_layer3._analyze_single")
    @patch("scripts.analyzer.run_layer3._cache")
    def test_exception_handling(self, mock_cache, mock_analyze):
        """分析中的例外不應導致整體崩潰。"""
        mock_analyze.side_effect = Exception("API Error")

        with patch("sys.argv", ["run_layer3", "--tickers", "FAIL"]):
            main()  # 不應拋出例外
