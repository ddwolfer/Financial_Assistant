"""
深度數據抓取器測試。

測試數據結構序列化、yfinance API 整合、數據品質分數計算。
"""

from unittest.mock import patch, MagicMock, PropertyMock
import math

import pandas as pd
import pytest

from scripts.analyzer.deep_data_fetcher import (
    ValuationData,
    FinancialHealthData,
    GrowthMomentumData,
    RiskMetricsData,
    PeerComparisonData,
    DeepAnalysisData,
    calculate_data_quality_score,
    _safe_float,
    _df_row_to_history,
    _df_to_records,
    _compute_margin_history,
    _extract_valuation,
    _extract_financial_health,
    _extract_growth_momentum,
    _extract_risk_metrics,
    fetch_deep_data,
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


# ============================================================
# Task 2+3 測試：輔助函數與數據抓取
# ============================================================

class TestSafeFloat:
    """_safe_float 轉換測試。"""

    def test_normal(self):
        assert _safe_float(3.14) == 3.14

    def test_int(self):
        assert _safe_float(42) == 42.0

    def test_none(self):
        assert _safe_float(None) is None

    def test_nan(self):
        assert _safe_float(float("nan")) is None

    def test_inf(self):
        assert _safe_float(float("inf")) is None

    def test_string(self):
        assert _safe_float("not_a_number") is None

    def test_numeric_string(self):
        assert _safe_float("3.14") == 3.14


class TestDfRowToHistory:
    """_df_row_to_history DataFrame → dict 轉換測試。"""

    def test_basic(self):
        """基本轉換：Timestamp 欄位 → 年份 key。"""
        df = pd.DataFrame(
            {"Total Revenue": [100e9, 90e9, 80e9]},
            index=[
                pd.Timestamp("2024-12-31"),
                pd.Timestamp("2023-12-31"),
                pd.Timestamp("2022-12-31"),
            ],
        ).T
        result = _df_row_to_history(df, "Total Revenue")
        assert result == {"2024": 100e9, "2023": 90e9, "2022": 80e9}

    def test_missing_row(self):
        """不存在的行名應回傳空 dict。"""
        df = pd.DataFrame({"A": [1]}).T
        assert _df_row_to_history(df, "Not Exist") == {}

    def test_empty_df(self):
        """空 DataFrame 應回傳空 dict。"""
        assert _df_row_to_history(pd.DataFrame(), "Any") == {}

    def test_none_df(self):
        """None 應回傳空 dict。"""
        assert _df_row_to_history(None, "Any") == {}

    def test_nan_values_filtered(self):
        """NaN 值應被過濾。"""
        df = pd.DataFrame(
            {"Revenue": [100e9, float("nan")]},
            index=[pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")],
        ).T
        result = _df_row_to_history(df, "Revenue")
        assert result == {"2024": 100e9}


class TestDfToRecords:
    """_df_to_records DataFrame → list[dict] 轉換測試。"""

    def test_basic(self):
        df = pd.DataFrame({
            "avg": [2.5, 2.8],
            "low": [2.3, 2.6],
        }, index=["Q1", "Q2"])
        records = _df_to_records(df)
        assert len(records) == 2
        assert records[0]["avg"] == 2.5
        assert records[0]["period"] == "Q1"

    def test_max_rows(self):
        df = pd.DataFrame({"val": range(20)})
        records = _df_to_records(df, max_rows=5)
        assert len(records) == 5

    def test_empty(self):
        assert _df_to_records(pd.DataFrame()) == []
        assert _df_to_records(None) == []


class TestComputeMarginHistory:
    """_compute_margin_history 比率計算測試。"""

    def test_basic(self):
        numerator = {"2024": 45e9, "2023": 40e9}
        denominator = {"2024": 100e9, "2023": 90e9}
        result = _compute_margin_history(numerator, denominator)
        assert result["2024"] == pytest.approx(0.45, rel=1e-3)

    def test_zero_denominator(self):
        """分母為零應跳過。"""
        result = _compute_margin_history({"2024": 10}, {"2024": 0})
        assert "2024" not in result

    def test_missing_year(self):
        """分子沒有對應年份應跳過。"""
        result = _compute_margin_history({"2024": 10}, {"2024": 100, "2023": 80})
        assert "2024" in result
        assert "2023" not in result


class TestExtractValuation:
    """_extract_valuation 估值提取測試。"""

    def test_full_info(self):
        info = {
            "enterpriseToEbitda": 12.5,
            "enterpriseToRevenue": 3.2,
            "priceToBook": 2.1,
            "priceToSalesTrailing12Months": 1.8,
            "trailingPE": 15.0,
            "forwardPE": 13.0,
            "targetMeanPrice": 150.0,
            "targetMedianPrice": 148.0,
            "targetHighPrice": 180.0,
            "targetLowPrice": 120.0,
            "numberOfAnalystOpinions": 25,
            "recommendationKey": "buy",
            "recommendationMean": 2.1,
            "freeCashflow": 5e9,
            "beta": 1.15,
            "enterpriseValue": 50e9,
            "dividendYield": 0.015,
            "payoutRatio": 0.25,
        }
        cashflow_df = pd.DataFrame(
            {"Free Cash Flow": [5e9, 4.5e9]},
            index=[pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")],
        ).T

        v = _extract_valuation(info, cashflow_df)
        assert v.ev_to_ebitda == 12.5
        assert v.target_price_mean == 150.0
        assert v.analyst_count == 25
        assert v.free_cashflow_history["2024"] == 5e9
        assert v.beta == 1.15

    def test_empty_info(self):
        v = _extract_valuation({}, pd.DataFrame())
        assert v.ev_to_ebitda is None
        assert v.free_cashflow_history == {}


class TestExtractFinancialHealth:
    """_extract_financial_health 財務體質提取測試。"""

    def _make_financials_df(self):
        """建立模擬的損益表 DataFrame。"""
        data = {
            "Total Revenue": [100e9, 90e9],
            "Net Income": [20e9, 18e9],
            "EBITDA": [30e9, 27e9],
            "Gross Profit": [45e9, 40e9],
            "Operating Income": [30e9, 26e9],
        }
        cols = [pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")]
        return pd.DataFrame(data, index=cols).T

    def _make_balance_df(self):
        data = {
            "Total Assets": [200e9, 180e9],
            "Total Liabilities Net Minority Interest": [120e9, 110e9],
            "Stockholders Equity": [80e9, 70e9],
            "Working Capital": [20e9, 15e9],
        }
        cols = [pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")]
        return pd.DataFrame(data, index=cols).T

    def _make_cashflow_df(self):
        data = {
            "Operating Cash Flow": [35e9, 30e9],
            "Capital Expenditure": [-10e9, -9e9],
            "Free Cash Flow": [25e9, 21e9],
        }
        cols = [pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")]
        return pd.DataFrame(data, index=cols).T

    def test_full_extraction(self):
        info = {
            "totalDebt": 50e9,
            "totalCash": 30e9,
            "currentRatio": 1.5,
            "quickRatio": 1.2,
        }
        fh = _extract_financial_health(
            info,
            self._make_financials_df(),
            self._make_balance_df(),
            self._make_cashflow_df(),
        )
        assert fh.revenue_history["2024"] == 100e9
        assert fh.total_assets == 200e9  # 最新一期
        assert fh.total_debt == 50e9
        assert fh.gross_margin_history["2024"] == pytest.approx(0.45, rel=1e-3)
        assert fh.free_cashflow_history["2024"] == 25e9


class TestExtractGrowthMomentum:
    """_extract_growth_momentum 成長動能提取測試。"""

    @patch("scripts.analyzer.deep_data_fetcher.yf.Ticker")
    def test_full_extraction(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker

        # 模擬 earnings_estimate
        mock_ticker.earnings_estimate = pd.DataFrame({
            "avg": [2.5, 2.8],
            "low": [2.3, 2.6],
            "high": [2.7, 3.0],
            "numberOfAnalysts": [20, 18],
            "growth": [0.10, 0.12],
        }, index=["0q", "+1q"])

        # 模擬 revenue_estimate
        mock_ticker.revenue_estimate = pd.DataFrame({
            "avg": [25e9, 27e9],
            "low": [24e9, 26e9],
            "high": [26e9, 28e9],
            "numberOfAnalysts": [18, 16],
            "growth": [0.08, 0.09],
        }, index=["0q", "+1q"])

        # 模擬 earnings_dates
        mock_ticker.earnings_dates = pd.DataFrame({
            "EPS Estimate": [2.3, 2.1],
            "Reported EPS": [2.5, 2.2],
            "Surprise(%)": [8.7, 4.8],
        }, index=[pd.Timestamp("2024-10-24"), pd.Timestamp("2024-07-25")])

        info = {"revenueGrowth": 0.11, "earningsGrowth": 0.15, "earningsQuarterlyGrowth": 0.12}

        gm = _extract_growth_momentum(info, mock_ticker)
        assert len(gm.eps_estimates) == 2
        assert gm.eps_estimates[0]["avg"] == 2.5
        assert len(gm.earnings_surprises) == 2
        assert gm.revenue_growth == 0.11


class TestExtractRiskMetrics:
    """_extract_risk_metrics 風險指標提取測試。"""

    @patch("scripts.analyzer.deep_data_fetcher.yf.Ticker")
    def test_full_extraction(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker

        # 模擬 insider_transactions（近期交易）
        mock_ticker.insider_transactions = pd.DataFrame({
            "Insider": ["CEO", "CFO"],
            "Position": ["CEO", "CFO"],
            "Transaction": ["Buy", "Sell"],
            "Shares": [10000, 5000],
            "Value": [1_500_000, 750_000],
            "Start Date": [pd.Timestamp("2026-02-01"), pd.Timestamp("2026-01-15")],
        })

        # 模擬 institutional_holders
        mock_ticker.institutional_holders = pd.DataFrame({
            "Holder": ["Vanguard", "BlackRock"],
            "pctHeld": [0.08, 0.07],
            "Shares": [50e6, 45e6],
            "Value": [7.5e9, 6.75e9],
        })

        info = {
            "beta": 1.15,
            "shortRatio": 2.5,
            "shortPercentOfFloat": 0.03,
            "fiftyTwoWeekHigh": 180.0,
            "fiftyTwoWeekLow": 110.0,
            "52WeekChange": 0.25,
            "currentPrice": 150.0,
            "heldPercentInsiders": 0.05,
            "heldPercentInstitutions": 0.75,
        }

        rm = _extract_risk_metrics(info, mock_ticker)
        assert rm.beta == 1.15
        assert rm.short_ratio == 2.5
        assert rm.fifty_two_week_high == 180.0
        assert len(rm.insider_transactions) == 2
        assert rm.insider_transactions[0]["insider"] == "CEO"
        assert len(rm.top_institutional_holders) == 2
        assert rm.top_institutional_holders[0]["holder"] == "Vanguard"


class TestFetchDeepData:
    """fetch_deep_data 整合測試。"""

    @patch("scripts.analyzer.deep_data_fetcher.yf.Ticker")
    def test_basic_fetch(self, mock_ticker_cls):
        """基本抓取應正確填充所有欄位。"""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker

        mock_ticker.info = {
            "quoteType": "EQUITY",
            "shortName": "Test Corp",
            "sector": "Technology",
            "industry": "Software",
            "marketCap": 50e9,
            "currentPrice": 150.0,
            "currency": "USD",
            "enterpriseToEbitda": 12.5,
            "priceToBook": 2.1,
            "beta": 1.15,
            "freeCashflow": 5e9,
            "targetMeanPrice": 170.0,
            "numberOfAnalystOpinions": 20,
            "recommendationKey": "buy",
            "totalDebt": 50e9,
            "totalCash": 30e9,
            "currentRatio": 1.5,
            "revenueGrowth": 0.11,
            "earningsGrowth": 0.15,
            "fiftyTwoWeekHigh": 180.0,
            "fiftyTwoWeekLow": 110.0,
            "heldPercentInsiders": 0.05,
            "heldPercentInstitutions": 0.75,
        }

        # 三表
        cols = [pd.Timestamp("2024-12-31"), pd.Timestamp("2023-12-31")]
        mock_ticker.financials = pd.DataFrame({
            "Total Revenue": [100e9, 90e9],
            "Net Income": [20e9, 18e9],
            "EBITDA": [30e9, 27e9],
            "Gross Profit": [45e9, 40e9],
            "Operating Income": [30e9, 26e9],
        }, index=cols).T

        mock_ticker.balance_sheet = pd.DataFrame({
            "Total Assets": [200e9, 180e9],
            "Total Liabilities Net Minority Interest": [120e9, 110e9],
            "Stockholders Equity": [80e9, 70e9],
            "Working Capital": [20e9, 15e9],
        }, index=cols).T

        mock_ticker.cashflow = pd.DataFrame({
            "Operating Cash Flow": [35e9, 30e9],
            "Capital Expenditure": [-10e9, -9e9],
            "Free Cash Flow": [25e9, 21e9],
        }, index=cols).T

        # 分析師
        mock_ticker.recommendations = pd.DataFrame({
            "strongBuy": [8], "buy": [10], "hold": [5],
            "sell": [2], "strongSell": [0],
        })
        mock_ticker.earnings_estimate = pd.DataFrame()
        mock_ticker.revenue_estimate = pd.DataFrame()
        mock_ticker.earnings_dates = pd.DataFrame()
        mock_ticker.insider_transactions = pd.DataFrame()
        mock_ticker.institutional_holders = pd.DataFrame()

        result = fetch_deep_data("TEST")

        assert result.symbol == "TEST"
        assert result.company_name == "Test Corp"
        assert result.sector == "Technology"
        assert result.valuation.ev_to_ebitda == 12.5
        assert result.valuation.target_price_mean == 170.0
        assert result.financial_health.revenue_history["2024"] == 100e9
        assert result.financial_health.total_assets == 200e9
        assert result.risk_metrics.beta == 1.15
        assert result.data_quality_score > 0.5

    @patch("scripts.analyzer.deep_data_fetcher.yf.Ticker")
    def test_no_data_returns_empty(self, mock_ticker_cls):
        """無數據應回傳空的 DeepAnalysisData。"""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {}

        result = fetch_deep_data("NODATA")
        assert result.symbol == "NODATA"
        assert result.company_name == ""
        assert result.data_quality_score == 0.0

    @patch("scripts.analyzer.deep_data_fetcher.yf.Ticker")
    def test_json_serializable(self, mock_ticker_cls):
        """fetch_deep_data 結果應可 JSON 序列化。"""
        import json
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {
            "quoteType": "EQUITY",
            "shortName": "Ser Test",
            "sector": "Tech",
            "industry": "SW",
            "marketCap": 1e9,
            "currentPrice": 50.0,
        }
        mock_ticker.financials = pd.DataFrame()
        mock_ticker.balance_sheet = pd.DataFrame()
        mock_ticker.cashflow = pd.DataFrame()
        mock_ticker.recommendations = pd.DataFrame()
        mock_ticker.earnings_estimate = pd.DataFrame()
        mock_ticker.revenue_estimate = pd.DataFrame()
        mock_ticker.earnings_dates = pd.DataFrame()
        mock_ticker.insider_transactions = pd.DataFrame()
        mock_ticker.institutional_holders = pd.DataFrame()

        result = fetch_deep_data("SER")
        # 不應丟出例外
        json_str = json.dumps(result.to_dict())
        restored = DeepAnalysisData.from_dict(json.loads(json_str))
        assert restored.symbol == "SER"


# ============================================================
# Task 5 測試：DeepDataCache 快取
# ============================================================

from scripts.analyzer.deep_data_fetcher import DeepDataCache, DEEP_CACHE_CONFIG


class TestDeepDataCache:
    """DeepDataCache 快取測試。"""

    def test_put_and_get(self, tmp_path):
        """put → get 應回傳相同數據。"""
        cache = DeepDataCache(cache_dir=tmp_path)
        data = _make_deep_analysis(symbol="AAPL")
        cache.put(data)
        cached = cache.get("AAPL")
        assert cached is not None
        assert cached.symbol == "AAPL"
        assert cached.valuation.ev_to_ebitda == 12.5

    def test_miss_returns_none(self, tmp_path):
        """未快取的 symbol 應回傳 None。"""
        cache = DeepDataCache(cache_dir=tmp_path)
        assert cache.get("NOEXIST") is None

    def test_case_insensitive(self, tmp_path):
        """symbol 查詢應不分大小寫。"""
        cache = DeepDataCache(cache_dir=tmp_path)
        data = _make_deep_analysis(symbol="aapl")
        cache.put(data)
        assert cache.get("AAPL") is not None

    def test_save_and_load(self, tmp_path):
        """save → 新建 cache → load 應能復原。"""
        cache1 = DeepDataCache(cache_dir=tmp_path)
        cache1.put(_make_deep_analysis(symbol="MSFT"))
        cache1.save()

        cache2 = DeepDataCache(cache_dir=tmp_path)
        cache2.load()
        cached = cache2.get("MSFT")
        assert cached is not None
        assert cached.symbol == "MSFT"

    def test_ttl_expiry(self, tmp_path):
        """過期的數據應回傳 None。"""
        from scripts.scanner.config import CacheConfig
        config = CacheConfig(ttl_seconds=1, error_ttl_seconds=1,
                             cache_filename="deep_analysis_cache.json")
        cache = DeepDataCache(config=config, cache_dir=tmp_path)
        cache.put(_make_deep_analysis(symbol="OLD"))

        import time
        time.sleep(1.1)
        assert cache.get("OLD") is None

    def test_empty_data_uses_error_ttl(self, tmp_path):
        """空數據（quality=0）使用較短 TTL。"""
        empty = DeepAnalysisData(
            symbol="EMPTY", company_name="", sector="", industry="",
            data_quality_score=0.0,
        )
        cache = DeepDataCache(cache_dir=tmp_path)
        cache.put(empty)
        # 應正常回傳（還沒過期）
        cached = cache.get("EMPTY")
        assert cached is not None
        assert cached.data_quality_score == 0.0

    def test_dirty_flag(self, tmp_path):
        """沒有變更時 save 不應寫入磁碟。"""
        cache = DeepDataCache(cache_dir=tmp_path)
        cache.save()  # 沒有 dirty，不應建立檔案
        cache_file = tmp_path / "deep_analysis_cache.json"
        assert not cache_file.exists()

    def test_clear(self, tmp_path):
        """clear 後 get 應回傳 None。"""
        cache = DeepDataCache(cache_dir=tmp_path)
        cache.put(_make_deep_analysis(symbol="DEL"))
        assert cache.get("DEL") is not None
        cache.clear()
        assert cache.get("DEL") is None
        assert cache.size == 0

    def test_corrupted_json(self, tmp_path):
        """損壞的 JSON 應建立空快取。"""
        cache_file = tmp_path / "deep_analysis_cache.json"
        cache_file.write_text("NOT VALID JSON {{{")
        cache = DeepDataCache(cache_dir=tmp_path)
        cache.load()
        assert cache.size == 0
