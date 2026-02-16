"""Tests for stock universe providers."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.scanner.universe import (
    get_tickers_from_file,
    _fetch_wikipedia_tickers,
    get_sp400_tickers,
    get_sp600_tickers,
    get_sp1500_tickers,
)


def test_load_tickers_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(["AAPL", "msft", "  GOOGL  "], f)
        f.flush()
        result = get_tickers_from_file(f.name)
    assert result == ["AAPL", "MSFT", "GOOGL"]


def test_load_tickers_invalid_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"not": "a list"}, f)
        f.flush()
        with pytest.raises(ValueError):
            get_tickers_from_file(f.name)


# === 以下為新增的 Universe 擴充測試 ===

_MOCK_HTML_TABLE = """
<html><body>
<table class="wikitable">
<tr><th>Symbol</th><th>Security</th></tr>
<tr><td>AAPL</td><td>Apple</td></tr>
<tr><td>MSFT</td><td>Microsoft</td></tr>
<tr><td>BRK.B</td><td>Berkshire Hathaway</td></tr>
</table>
</body></html>
"""


@patch("scripts.scanner.universe.requests.get")
def test_fetch_helper_parses_wikipedia_table(mock_get, tmp_path):
    """_fetch_wikipedia_tickers 正確解析 Wikipedia HTML 表格並正規化代碼。"""
    mock_resp = MagicMock()
    mock_resp.text = _MOCK_HTML_TABLE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    cache_path = tmp_path / "test_cache.json"
    result = _fetch_wikipedia_tickers(
        url="https://example.com",
        cache_path=cache_path,
        label="Test",
        use_cache=False,
    )

    assert "AAPL" in result
    assert "MSFT" in result
    # BRK.B 應正規化為 BRK-B
    assert "BRK-B" in result
    assert "BRK.B" not in result
    # 應已排序
    assert result == sorted(result)
    # 快取檔案應已寫入
    assert cache_path.exists()
    cached = json.loads(cache_path.read_text())
    assert cached == result


@patch("scripts.scanner.universe.requests.get")
def test_sp400_tickers_cached(mock_get, tmp_path):
    """S&P 400 快取存在時直接讀取，不發送網路請求。"""
    cache_path = tmp_path / "sp400_tickers.json"
    tickers = ["MDT", "MCHP", "NDAQ"]
    cache_path.write_text(json.dumps(tickers))

    with patch("scripts.scanner.universe._SP400_CACHE", cache_path):
        result = get_sp400_tickers(use_cache=True)

    assert result == tickers
    mock_get.assert_not_called()


@patch("scripts.scanner.universe.requests.get")
def test_sp600_tickers_cached(mock_get, tmp_path):
    """S&P 600 快取存在時直接讀取，不發送網路請求。"""
    cache_path = tmp_path / "sp600_tickers.json"
    tickers = ["CABO", "CALM", "CARG"]
    cache_path.write_text(json.dumps(tickers))

    with patch("scripts.scanner.universe._SP600_CACHE", cache_path):
        result = get_sp600_tickers(use_cache=True)

    assert result == tickers
    mock_get.assert_not_called()


def test_sp1500_deduplication():
    """sp1500 應去除重複的股票代碼。"""
    with (
        patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=["AAPL", "MSFT", "GOOGL"],
        ),
        patch(
            "scripts.scanner.universe.get_sp400_tickers",
            return_value=["MDT", "MSFT", "NDAQ"],  # MSFT 重複
        ),
        patch(
            "scripts.scanner.universe.get_sp600_tickers",
            return_value=["CABO", "CALM", "NDAQ"],  # NDAQ 重複
        ),
    ):
        result = get_sp1500_tickers()

    # 應去重複後排序
    assert result == sorted(set(["AAPL", "MSFT", "GOOGL", "MDT", "NDAQ", "CABO", "CALM"]))
    # MSFT 和 NDAQ 各只出現一次
    assert result.count("MSFT") == 1
    assert result.count("NDAQ") == 1


def test_sp1500_combines_all_three():
    """sp1500 包含 sp500 + sp400 + sp600 的聯集。"""
    with (
        patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=["A", "B"],
        ),
        patch(
            "scripts.scanner.universe.get_sp400_tickers",
            return_value=["C", "D"],
        ),
        patch(
            "scripts.scanner.universe.get_sp600_tickers",
            return_value=["E", "F"],
        ),
    ):
        result = get_sp1500_tickers()

    assert result == ["A", "B", "C", "D", "E", "F"]
