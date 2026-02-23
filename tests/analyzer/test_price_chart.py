"""
價格走勢圖生成器測試。

測試 fetch_price_history 和 generate_price_chart。
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.analyzer.price_chart import (
    fetch_price_history,
    generate_price_chart,
)


# ============================================================
# fetch_price_history 測試
# ============================================================

class TestFetchPriceHistory:
    """fetch_price_history 函數測試。"""

    @patch("scripts.analyzer.price_chart.yf")
    def test_successful_fetch(self, mock_yf):
        """成功抓取應回傳日期和收盤價。"""
        import pandas as pd

        mock_ticker = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker

        # 模擬 DataFrame
        dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
        mock_df = pd.DataFrame(
            {"Close": [100.0, 102.5, 101.0]},
            index=dates,
        )
        mock_ticker.history.return_value = mock_df

        result = fetch_price_history("AAPL")
        assert "dates" in result
        assert "closes" in result
        assert len(result["dates"]) == 3
        assert result["closes"] == [100.0, 102.5, 101.0]

    @patch("scripts.analyzer.price_chart.yf")
    def test_empty_history_returns_empty_dict(self, mock_yf):
        """空歷史數據應回傳空 dict。"""
        import pandas as pd

        mock_ticker = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame()

        result = fetch_price_history("INVALID")
        assert result == {}

    @patch("scripts.analyzer.price_chart.yf")
    def test_exception_returns_empty_dict(self, mock_yf):
        """例外發生時應回傳空 dict。"""
        mock_yf.Ticker.side_effect = Exception("網路錯誤")
        result = fetch_price_history("FAIL")
        assert result == {}


# ============================================================
# generate_price_chart 測試
# ============================================================

class TestGeneratePriceChart:
    """generate_price_chart 函數測試。"""

    def test_empty_price_history_returns_none(self):
        """空價格數據應回傳 None。"""
        result = generate_price_chart(
            symbol="TEST",
            company_name="Test Corp",
            price_history={},
            output_dir=Path("/tmp"),
        )
        assert result is None

    def test_none_price_history_returns_none(self):
        """None 價格數據應回傳 None。"""
        result = generate_price_chart(
            symbol="TEST",
            company_name="Test Corp",
            price_history=None,
            output_dir=Path("/tmp"),
        )
        assert result is None

    def test_successful_chart_generation(self):
        """成功生成圖表應回傳相對路徑。"""
        price_history = {
            "dates": [
                "2026-01-01", "2026-01-02", "2026-01-03",
                "2026-01-06", "2026-01-07",
            ],
            "closes": [100.0, 102.5, 101.0, 103.0, 104.5],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_price_chart(
                symbol="TEST",
                company_name="Test Corp",
                price_history=price_history,
                output_dir=Path(tmpdir),
            )

            assert result is not None
            assert result.startswith("charts/")
            assert "TEST" in result
            assert result.endswith(".png")

            # 驗證檔案存在
            full_path = Path(tmpdir) / result
            assert full_path.exists()
            assert full_path.stat().st_size > 0

    def test_charts_directory_created(self):
        """應自動建立 charts 子目錄。"""
        price_history = {
            "dates": ["2026-01-01", "2026-01-02"],
            "closes": [100.0, 105.0],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            charts_dir = Path(tmpdir) / "charts"
            assert not charts_dir.exists()

            generate_price_chart(
                symbol="TEST",
                company_name="Test Corp",
                price_history=price_history,
                output_dir=Path(tmpdir),
            )

            assert charts_dir.exists()
            assert charts_dir.is_dir()

    def test_empty_dates_returns_none(self):
        """空日期列表應回傳 None。"""
        result = generate_price_chart(
            symbol="TEST",
            company_name="Test Corp",
            price_history={"dates": [], "closes": []},
            output_dir=Path("/tmp"),
        )
        assert result is None
