"""
同業比較器測試。

測試排名邏輯、同業篩選、完整流程。
"""

import pytest
from unittest.mock import patch, MagicMock

from scripts.analyzer.peer_finder import (
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
