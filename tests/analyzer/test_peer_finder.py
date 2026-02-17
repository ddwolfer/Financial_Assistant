"""
同業比較器測試。

測試排名邏輯、同業篩選、完整流程。
"""

import pytest
from unittest.mock import patch, MagicMock

from scripts.scanner.data_fetcher import TickerMetrics
from scripts.analyzer.peer_finder import (
    find_peers,
    rank_among_peers,
    fetch_peer_metrics,
)


# ============================================================
# 排名邏輯測試
# ============================================================

class TestRankAmongPeers:
    """rank_among_peers 排名測試。"""

    def test_pe_lower_is_better(self):
        """PE 越低排名越前。"""
        target = {"symbol": "TARGET", "pe": 10.0}
        peers = [
            {"symbol": "A", "pe": 15.0},
            {"symbol": "B", "pe": 8.0},
            {"symbol": "C", "pe": 20.0},
        ]
        ranks = rank_among_peers(target, peers)
        # 排序: B(8) < TARGET(10) < A(15) < C(20)
        assert ranks["pe"] == 2

    def test_roe_higher_is_better(self):
        """ROE 越高排名越前。"""
        target = {"symbol": "TARGET", "roe": 0.25}
        peers = [
            {"symbol": "A", "roe": 0.20},
            {"symbol": "B", "roe": 0.30},
            {"symbol": "C", "roe": 0.15},
        ]
        ranks = rank_among_peers(target, peers)
        # 排序: B(0.30) > TARGET(0.25) > A(0.20) > C(0.15)
        assert ranks["roe"] == 2

    def test_best_rank(self):
        """目標股最佳時排名為 1。"""
        target = {"symbol": "TARGET", "pe": 5.0, "roe": 0.40}
        peers = [
            {"symbol": "A", "pe": 15.0, "roe": 0.20},
            {"symbol": "B", "pe": 10.0, "roe": 0.25},
        ]
        ranks = rank_among_peers(target, peers)
        assert ranks["pe"] == 1  # 最低 PE
        assert ranks["roe"] == 1  # 最高 ROE

    def test_worst_rank(self):
        """目標股最差時排名為最後。"""
        target = {"symbol": "TARGET", "pe": 50.0, "roe": 0.05}
        peers = [
            {"symbol": "A", "pe": 15.0, "roe": 0.20},
            {"symbol": "B", "pe": 10.0, "roe": 0.25},
        ]
        ranks = rank_among_peers(target, peers)
        assert ranks["pe"] == 3  # 最高 PE (3 支中最後)
        assert ranks["roe"] == 3  # 最低 ROE

    def test_none_values_skipped(self):
        """None 值應被跳過。"""
        target = {"symbol": "TARGET", "pe": 10.0}
        peers = [
            {"symbol": "A", "pe": None},
            {"symbol": "B", "pe": 15.0},
        ]
        ranks = rank_among_peers(target, peers)
        # 只有 TARGET(10) 和 B(15)
        assert ranks["pe"] == 1

    def test_no_valid_values(self):
        """全部 None 時不應有排名。"""
        target = {"symbol": "TARGET", "pe": None}
        peers = [{"symbol": "A", "pe": None}]
        ranks = rank_among_peers(target, peers)
        assert "pe" not in ranks

    def test_multiple_metrics(self):
        """多指標同時排名。"""
        target = {
            "symbol": "TARGET",
            "pe": 12.0,
            "ev_ebitda": 10.0,
            "roe": 0.22,
            "gross_margin": 0.45,
            "debt_to_equity": 0.5,
        }
        peers = [
            {"symbol": "A", "pe": 15.0, "ev_ebitda": 8.0, "roe": 0.18,
             "gross_margin": 0.50, "debt_to_equity": 0.3},
            {"symbol": "B", "pe": 10.0, "ev_ebitda": 12.0, "roe": 0.25,
             "gross_margin": 0.40, "debt_to_equity": 0.8},
        ]
        ranks = rank_among_peers(target, peers)
        assert "pe" in ranks
        assert "roe" in ranks
        assert "ev_ebitda" in ranks
        assert "gross_margin" in ranks
        assert "debt_to_equity" in ranks


class TestFetchPeerMetrics:
    """fetch_peer_metrics 抓取測試。"""

    @patch("scripts.analyzer.peer_finder.yf.Ticker")
    def test_basic_fetch(self, mock_ticker_cls):
        """基本抓取應回傳正確結構。"""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {
            "shortName": "Peer Corp",
            "trailingPE": 15.0,
            "forwardPE": 13.0,
            "enterpriseToEbitda": 10.0,
            "returnOnEquity": 0.20,
            "grossMargins": 0.45,
            "marketCap": 30e9,
            "debtToEquity": 50.0,  # 百分比
        }

        result = fetch_peer_metrics(["PEER1"])
        assert len(result) == 1
        assert result[0]["symbol"] == "PEER1"
        assert result[0]["pe"] == 15.0
        assert result[0]["roe"] == 0.20
        assert result[0]["debt_to_equity"] == 0.5  # 除以 100

    @patch("scripts.analyzer.peer_finder.yf.Ticker")
    def test_fetch_error_handled(self, mock_ticker_cls):
        """抓取失敗應不 crash，回傳空指標。"""
        mock_ticker_cls.side_effect = Exception("API error")

        result = fetch_peer_metrics(["FAIL"])
        assert len(result) == 1
        assert result[0]["symbol"] == "FAIL"
        assert result[0]["pe"] is None


# ============================================================
# find_peers 同業篩選測試
# ============================================================


def _make_metrics(
    symbol: str,
    sector: str = "Technology",
    industry: str = "Software",
    market_cap: float = 100e9,
    fetch_error: str | None = None,
) -> TickerMetrics:
    """建立測試用 TickerMetrics。"""
    return TickerMetrics(
        symbol=symbol,
        sector=sector,
        industry=industry,
        market_cap=market_cap,
        fetch_error=fetch_error,
    )


class TestFindPeers:
    """find_peers 同業篩選測試。"""

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    @patch("scripts.analyzer.peer_finder.find_peers.__wrapped__", None)
    def _run_find_peers(self, mock_batch, metrics_list, **kwargs):
        """輔助方法：mock universe 和 batch_metrics，呼叫 find_peers。"""
        # mock fetch_batch_metrics 回傳我們準備好的列表
        mock_batch.return_value = metrics_list

        # 同時 mock universe 函數，回傳對應的 symbol 列表
        tickers = [m.symbol for m in metrics_list]
        with patch(
            "scripts.analyzer.peer_finder.get_sp500_tickers",
            return_value=tickers,
        ):
            # 繞過 find_peers 內部的 import
            with patch.dict(
                "scripts.analyzer.peer_finder.find_peers.__globals__",
            ):
                pass

        return find_peers(**kwargs)

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_same_industry_preferred(self, mock_batch):
        """同 industry 數量足夠時，應只選同 industry 的股票。"""
        metrics = [
            _make_metrics("PEER1", industry="Software", market_cap=200e9),
            _make_metrics("PEER2", industry="Software", market_cap=150e9),
            _make_metrics("PEER3", industry="Software", market_cap=100e9),
            _make_metrics("PEER4", industry="Software", market_cap=80e9),
            _make_metrics("PEER5", industry="Software", market_cap=50e9),
            _make_metrics("OTHER1", industry="Hardware", market_cap=500e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=[m.symbol for m in metrics] + ["TARGET"],
        ):
            result = find_peers("TARGET", "Technology", "Software", count=5)

        assert len(result) == 5
        # 應全部是 Software，不含 OTHER1
        assert "OTHER1" not in result
        # 應按市值排序（最大的排前面）
        assert result[0] == "PEER1"
        assert result[1] == "PEER2"

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_fallback_to_sector(self, mock_batch):
        """同 industry 不足時應擴展到同 sector。"""
        metrics = [
            _make_metrics("IND1", industry="Software", market_cap=100e9),
            _make_metrics("IND2", industry="Software", market_cap=80e9),
            _make_metrics("SEC1", industry="Hardware", market_cap=200e9),
            _make_metrics("SEC2", industry="Semiconductors", market_cap=150e9),
            _make_metrics("SEC3", industry="IT Services", market_cap=120e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=[m.symbol for m in metrics] + ["TARGET"],
        ):
            result = find_peers("TARGET", "Technology", "Software", count=5)

        assert len(result) == 5
        # 應包含 2 支同 industry + 3 支同 sector
        assert "IND1" in result
        assert "IND2" in result
        assert "SEC1" in result

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_sector_sorted_by_market_cap_not_alphabetical(self, mock_batch):
        """
        同 sector fallback 應按市值選，不是按字母順序。

        這是修復的核心測試：模擬 AAPL 的情境，
        同 industry 為空，同 sector 有很多股票。
        字母排序靠前但市值小的股票不應被選中。
        """
        # 模擬字母排序的科技股（A 開頭的小公司 vs 大公司）
        metrics = [
            # 字母排序靠前但市值小的股票
            _make_metrics("ACN", industry="IT Consulting", market_cap=50e9),
            _make_metrics("ADBE", industry="Application Software", market_cap=40e9),
            _make_metrics("ADI", industry="Semiconductors", market_cap=30e9),
            _make_metrics("ADP", industry="Payroll", market_cap=25e9),
            _make_metrics("ADSK", industry="Design Software", market_cap=20e9),
            # 字母排序靠後但市值大的股票（應被選中）
            _make_metrics("MSFT", industry="Infrastructure Software", market_cap=3000e9),
            _make_metrics("NVDA", industry="Semiconductors", market_cap=2500e9),
            _make_metrics("AVGO", industry="Semiconductors", market_cap=800e9),
            _make_metrics("ORCL", industry="Enterprise Software", market_cap=400e9),
            _make_metrics("CRM", industry="Cloud Software", market_cap=300e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=[m.symbol for m in metrics] + ["AAPL"],
        ):
            # AAPL 的 industry 是 Consumer Electronics，
            # 上面沒有任何股票是 Consumer Electronics
            result = find_peers(
                "AAPL", "Technology", "Consumer Electronics", count=5,
            )

        assert len(result) == 5
        # 應選市值最大的 5 支，而非字母排序的前 5 支
        assert result[0] == "MSFT"   # 3T
        assert result[1] == "NVDA"   # 2.5T
        assert result[2] == "AVGO"   # 800B
        assert result[3] == "ORCL"   # 400B
        assert result[4] == "CRM"    # 300B
        # 字母排序靠前但市值小的股票不應出現
        assert "ACN" not in result
        assert "ADBE" not in result

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_industry_priority_preserved(self, mock_batch):
        """混合時同 industry 應排在前面，即使市值較小。"""
        metrics = [
            # 同 industry 但市值小
            _make_metrics("IND1", industry="Consumer Electronics", market_cap=10e9),
            _make_metrics("IND2", industry="Consumer Electronics", market_cap=8e9),
            # 同 sector 但不同 industry，市值大
            _make_metrics("SEC1", industry="Software", market_cap=3000e9),
            _make_metrics("SEC2", industry="Semiconductors", market_cap=2000e9),
            _make_metrics("SEC3", industry="IT Services", market_cap=1000e9),
            _make_metrics("SEC4", industry="Cloud", market_cap=500e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=[m.symbol for m in metrics] + ["TARGET"],
        ):
            result = find_peers(
                "TARGET", "Technology", "Consumer Electronics", count=5,
            )

        assert len(result) == 5
        # 同 industry 的應在前面（即使市值小）
        assert result[0] == "IND1"
        assert result[1] == "IND2"
        # 剩下 3 個應是市值最大的同 sector
        assert result[2] == "SEC1"
        assert result[3] == "SEC2"
        assert result[4] == "SEC3"

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_excludes_self(self, mock_batch):
        """應排除目標股自身。"""
        metrics = [
            _make_metrics("TARGET", industry="Software", market_cap=500e9),
            _make_metrics("PEER1", industry="Software", market_cap=200e9),
            _make_metrics("PEER2", industry="Software", market_cap=100e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=["TARGET", "PEER1", "PEER2"],
        ):
            result = find_peers("TARGET", "Technology", "Software", count=5)

        assert "TARGET" not in result
        assert "PEER1" in result
        assert "PEER2" in result

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_excludes_fetch_errors(self, mock_batch):
        """應排除抓取失敗的股票。"""
        metrics = [
            _make_metrics("GOOD1", industry="Software", market_cap=200e9),
            _make_metrics("BAD1", industry="Software", market_cap=300e9,
                          fetch_error="API error"),
            _make_metrics("GOOD2", industry="Software", market_cap=100e9),
        ]
        mock_batch.return_value = metrics

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=[m.symbol for m in metrics] + ["TARGET"],
        ):
            result = find_peers("TARGET", "Technology", "Software", count=5)

        assert "BAD1" not in result
        assert "GOOD1" in result
        assert "GOOD2" in result

    @patch("scripts.analyzer.peer_finder.fetch_batch_metrics")
    def test_empty_universe(self, mock_batch):
        """空清單應回傳空結果。"""
        mock_batch.return_value = []

        with patch(
            "scripts.scanner.universe.get_sp500_tickers",
            return_value=["TARGET"],
        ):
            result = find_peers("TARGET", "Technology", "Software", count=5)

        assert result == []
