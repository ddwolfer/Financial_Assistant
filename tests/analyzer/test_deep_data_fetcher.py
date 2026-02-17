"""
深度數據抓取器測試。

測試數據結構序列化、yfinance API 整合、數據品質分數計算。
"""

import pytest

from scripts.analyzer.deep_data_fetcher import (
    ValuationData,
    FinancialHealthData,
    GrowthMomentumData,
    RiskMetricsData,
    PeerComparisonData,
    DeepAnalysisData,
    calculate_data_quality_score,
)


# ============================================================
# 測試輔助函數
# ============================================================

def _make_valuation(**overrides) -> ValuationData:
    """建立測試用估值數據。"""
    defaults = {
        "ev_to_ebitda": 12.5,
        "ev_to_revenue": 3.2,
        "price_to_book": 2.1,
        "price_to_sales": 1.8,
        "trailing_pe": 15.0,
        "forward_pe": 13.0,
        "target_price_mean": 150.0,
        "target_price_median": 148.0,
        "target_price_high": 180.0,
        "target_price_low": 120.0,
        "analyst_count": 25,
        "recommendation_key": "buy",
        "recommendation_mean": 2.1,
        "recommendations_summary": {"strongBuy": 8, "buy": 10, "hold": 5, "sell": 2, "strongSell": 0},
        "free_cashflow": 5_000_000_000,
        "free_cashflow_history": {"2024": 5e9, "2023": 4.5e9, "2022": 4e9},
        "beta": 1.15,
        "enterprise_value": 50_000_000_000,
        "dividend_yield": 0.015,
        "payout_ratio": 0.25,
    }
    defaults.update(overrides)
    return ValuationData(**defaults)


def _make_financial_health(**overrides) -> FinancialHealthData:
    """建立測試用財務體質數據。"""
    defaults = {
        "revenue_history": {"2024": 100e9, "2023": 90e9, "2022": 80e9},
        "net_income_history": {"2024": 20e9, "2023": 18e9, "2022": 15e9},
        "ebitda_history": {"2024": 30e9, "2023": 27e9, "2022": 24e9},
        "gross_margin_history": {"2024": 0.45, "2023": 0.44, "2022": 0.43},
        "operating_margin_history": {"2024": 0.30, "2023": 0.29, "2022": 0.28},
        "total_assets": 200e9,
        "total_liabilities": 120e9,
        "total_equity": 80e9,
        "total_debt": 50e9,
        "total_cash": 30e9,
        "current_ratio": 1.5,
        "quick_ratio": 1.2,
        "working_capital": 20e9,
        "operating_cashflow_history": {"2024": 35e9, "2023": 30e9},
        "capex_history": {"2024": -10e9, "2023": -9e9},
        "free_cashflow_history": {"2024": 25e9, "2023": 21e9},
    }
    defaults.update(overrides)
    return FinancialHealthData(**defaults)


def _make_growth(**overrides) -> GrowthMomentumData:
    """建立測試用成長動能數據。"""
    defaults = {
        "eps_estimates": [
            {"period": "0q", "avg": 2.5, "low": 2.3, "high": 2.7, "num_analysts": 20, "growth": 0.10},
        ],
        "revenue_estimates": [
            {"period": "0q", "avg": 25e9, "low": 24e9, "high": 26e9, "num_analysts": 18, "growth": 0.08},
        ],
        "earnings_surprises": [
            {"date": "2024-10-24", "estimate": 2.3, "actual": 2.5, "surprise_pct": 8.7},
        ],
        "revenue_growth": 0.11,
        "earnings_growth": 0.15,
        "earnings_quarterly_growth": 0.12,
    }
    defaults.update(overrides)
    return GrowthMomentumData(**defaults)


def _make_risk(**overrides) -> RiskMetricsData:
    """建立測試用風險指標數據。"""
    defaults = {
        "beta": 1.15,
        "short_ratio": 2.5,
        "short_percent_of_float": 0.03,
        "fifty_two_week_high": 180.0,
        "fifty_two_week_low": 110.0,
        "fifty_two_week_change": 0.25,
        "current_price": 150.0,
        "held_percent_insiders": 0.05,
        "held_percent_institutions": 0.75,
        "insider_transactions": [
            {"insider": "CEO", "transaction": "Buy", "shares": 10000, "value": 1_500_000},
        ],
        "top_institutional_holders": [
            {"holder": "Vanguard", "pct_held": 0.08, "shares": 50_000_000},
        ],
    }
    defaults.update(overrides)
    return RiskMetricsData(**defaults)


def _make_peers(**overrides) -> PeerComparisonData:
    """建立測試用同業數據。"""
    defaults = {
        "peers": [
            {"symbol": "PEER1", "name": "Peer One", "pe": 18.0, "roe": 0.20},
            {"symbol": "PEER2", "name": "Peer Two", "pe": 14.0, "roe": 0.18},
        ],
        "sector": "Technology",
        "industry": "Software",
        "rank_in_peers": {"pe": 2, "roe": 1},
    }
    defaults.update(overrides)
    return PeerComparisonData(**defaults)


def _make_deep_analysis(**overrides) -> DeepAnalysisData:
    """建立測試用完整深度分析數據。"""
    defaults = {
        "symbol": "TEST",
        "company_name": "Test Corp",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 50e9,
        "current_price": 150.0,
        "currency": "USD",
        "graham_number": 120.0,
        "margin_of_safety_pct": -25.0,
        "valuation": _make_valuation(),
        "financial_health": _make_financial_health(),
        "growth_momentum": _make_growth(),
        "risk_metrics": _make_risk(),
        "peer_comparison": _make_peers(),
        "fetched_at": "2026-02-17T10:00:00+00:00",
        "data_quality_score": 0.85,
    }
    defaults.update(overrides)
    return DeepAnalysisData(**defaults)


# ============================================================
# Task 1 測試：序列化 roundtrip
# ============================================================

class TestValuationDataSerialization:
    """ValuationData 序列化測試。"""

    def test_roundtrip(self):
        """to_dict → from_dict 應保持一致。"""
        original = _make_valuation()
        restored = ValuationData.from_dict(original.to_dict())
        assert restored.ev_to_ebitda == original.ev_to_ebitda
        assert restored.target_price_mean == original.target_price_mean
        assert restored.free_cashflow_history == original.free_cashflow_history
        assert restored.recommendation_key == original.recommendation_key

    def test_empty_dict(self):
        """空字典應建立全 None/空值的物件。"""
        v = ValuationData.from_dict({})
        assert v.ev_to_ebitda is None
        assert v.free_cashflow_history == {}


class TestFinancialHealthDataSerialization:
    """FinancialHealthData 序列化測試。"""

    def test_roundtrip(self):
        original = _make_financial_health()
        restored = FinancialHealthData.from_dict(original.to_dict())
        assert restored.revenue_history == original.revenue_history
        assert restored.total_assets == original.total_assets
        assert restored.current_ratio == original.current_ratio

    def test_empty_dict(self):
        fh = FinancialHealthData.from_dict({})
        assert fh.revenue_history == {}
        assert fh.total_assets is None


class TestGrowthMomentumDataSerialization:
    """GrowthMomentumData 序列化測試。"""

    def test_roundtrip(self):
        original = _make_growth()
        restored = GrowthMomentumData.from_dict(original.to_dict())
        assert restored.eps_estimates == original.eps_estimates
        assert restored.revenue_growth == original.revenue_growth

    def test_empty_dict(self):
        g = GrowthMomentumData.from_dict({})
        assert g.eps_estimates == []
        assert g.revenue_growth is None


class TestRiskMetricsDataSerialization:
    """RiskMetricsData 序列化測試。"""

    def test_roundtrip(self):
        original = _make_risk()
        restored = RiskMetricsData.from_dict(original.to_dict())
        assert restored.beta == original.beta
        assert restored.insider_transactions == original.insider_transactions
        assert restored.top_institutional_holders == original.top_institutional_holders

    def test_empty_dict(self):
        r = RiskMetricsData.from_dict({})
        assert r.beta is None
        assert r.insider_transactions == []


class TestPeerComparisonDataSerialization:
    """PeerComparisonData 序列化測試。"""

    def test_roundtrip(self):
        original = _make_peers()
        restored = PeerComparisonData.from_dict(original.to_dict())
        assert restored.peers == original.peers
        assert restored.rank_in_peers == original.rank_in_peers

    def test_empty_dict(self):
        p = PeerComparisonData.from_dict({})
        assert p.peers == []
        assert p.sector == ""


class TestDeepAnalysisDataSerialization:
    """DeepAnalysisData 完整 roundtrip 測試。"""

    def test_full_roundtrip(self):
        """完整數據包序列化後應完全復原。"""
        original = _make_deep_analysis()
        d = original.to_dict()
        restored = DeepAnalysisData.from_dict(d)

        # 頂層
        assert restored.symbol == "TEST"
        assert restored.company_name == "Test Corp"
        assert restored.market_cap == 50e9
        assert restored.graham_number == 120.0

        # 子結構
        assert restored.valuation.ev_to_ebitda == 12.5
        assert restored.financial_health.revenue_history["2024"] == 100e9
        assert restored.growth_momentum.eps_estimates[0]["avg"] == 2.5
        assert restored.risk_metrics.beta == 1.15
        assert restored.peer_comparison.peers[0]["symbol"] == "PEER1"

    def test_minimal_data(self):
        """只有 symbol 的最小數據應可建立。"""
        d = DeepAnalysisData.from_dict({"symbol": "MIN"})
        assert d.symbol == "MIN"
        assert d.valuation.ev_to_ebitda is None
        assert d.financial_health.revenue_history == {}

    def test_json_compatible(self):
        """to_dict() 的結果應可被 json.dumps 處理。"""
        import json
        data = _make_deep_analysis()
        json_str = json.dumps(data.to_dict())
        restored = DeepAnalysisData.from_dict(json.loads(json_str))
        assert restored.symbol == data.symbol


# ============================================================
# 數據品質分數測試
# ============================================================

class TestDataQualityScore:
    """calculate_data_quality_score 測試。"""

    def test_full_data(self):
        """完整數據應有高分。"""
        data = _make_deep_analysis()
        score = calculate_data_quality_score(data)
        assert score > 0.8

    def test_empty_data(self):
        """空數據應為 0。"""
        data = DeepAnalysisData(symbol="EMPTY", company_name="", sector="", industry="")
        score = calculate_data_quality_score(data)
        assert score == 0.0

    def test_partial_data(self):
        """部分數據應在 0-1 之間。"""
        data = DeepAnalysisData(
            symbol="HALF",
            company_name="Half Corp",
            sector="Tech",
            industry="Software",
            market_cap=10e9,
            current_price=50.0,
            valuation=ValuationData(beta=1.0, free_cashflow=1e9),
            risk_metrics=RiskMetricsData(beta=1.0, fifty_two_week_high=60.0),
        )
        score = calculate_data_quality_score(data)
        assert 0.0 < score < 1.0
