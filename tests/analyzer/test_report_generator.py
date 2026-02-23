"""
報告生成器測試。

測試數字格式化、各 T1-T6 模板渲染、以及 generate_report 主函數。
"""

import pytest

from scripts.analyzer.deep_data_fetcher import (
    ValuationData,
    FinancialHealthData,
    GrowthMomentumData,
    RiskMetricsData,
    PeerComparisonData,
    DeepAnalysisData,
)
from scripts.analyzer.report_generator import (
    _fmt_number,
    _fmt_pct,
    _fmt_large,
    _fmt_price,
    _fmt_ratio,
    _render_t1_valuation,
    _render_t2_financial_health,
    _render_t3_growth_momentum,
    _render_t4_risk_scenario,
    _render_t5_peer_comparison,
    _render_t6_investment_summary,
    generate_report,
)


# ============================================================
# 測試輔助函數（複用 test_deep_data_fetcher 的模式）
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
        "target_price_mean": 180.0,
        "target_price_median": 175.0,
        "target_price_high": 220.0,
        "target_price_low": 140.0,
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
            {"period": "0q", "avg": 2.5, "low": 2.3, "high": 2.7, "numberOfAnalysts": 20, "growth": 0.10},
        ],
        "revenue_estimates": [
            {"period": "0q", "avg": 25e9, "low": 24e9, "high": 26e9, "numberOfAnalysts": 18, "growth": 0.08},
        ],
        "earnings_surprises": [
            {"date": "2024-10-24", "estimate": 2.3, "actual": 2.5, "surprise_pct": 8.7},
            {"date": "2024-07-25", "estimate": 2.1, "actual": 2.2, "surprise_pct": 4.8},
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
            {"insider": "John CEO", "position": "CEO", "transaction": "Buy", "shares": 10000, "value": 1_500_000},
            {"insider": "Jane CFO", "position": "CFO", "transaction": "Sale", "shares": 5000, "value": 750_000},
        ],
        "top_institutional_holders": [
            {"holder": "Vanguard Group", "pct_held": 0.08, "shares": 50_000_000},
            {"holder": "BlackRock", "pct_held": 0.07, "shares": 45_000_000},
        ],
    }
    defaults.update(overrides)
    return RiskMetricsData(**defaults)


def _make_peers(**overrides) -> PeerComparisonData:
    """建立測試用同業數據。"""
    defaults = {
        "peers": [
            {"symbol": "PEER1", "name": "Peer One Corp", "pe": 18.0, "ev_ebitda": 14.0, "roe": 0.20, "gross_margin": 0.40, "market_cap": 45e9},
            {"symbol": "PEER2", "name": "Peer Two Inc", "pe": 14.0, "ev_ebitda": 10.5, "roe": 0.18, "gross_margin": 0.38, "market_cap": 35e9},
        ],
        "sector": "Technology",
        "industry": "Software - Infrastructure",
        "rank_in_peers": {"pe": 1, "roe": 2, "gross_margin": 1, "ev_ebitda": 2},
    }
    defaults.update(overrides)
    return PeerComparisonData(**defaults)


def _make_deep_analysis(**overrides) -> DeepAnalysisData:
    """建立完整深度分析數據。"""
    defaults = {
        "symbol": "TEST",
        "company_name": "Test Corp",
        "sector": "Technology",
        "industry": "Software - Infrastructure",
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
# 數字格式化測試
# ============================================================

class TestFmtNumber:
    """_fmt_number 數字格式化測試。"""

    def test_none_returns_na(self):
        """None 應回傳 N/A。"""
        assert _fmt_number(None) == "N/A"

    def test_integer_like(self):
        """整數型浮點應正確格式化。"""
        assert _fmt_number(1234.5, 1) == "1,234.5"

    def test_large_number(self):
        """大數字應有千分位。"""
        assert _fmt_number(1_000_000.0, 0) == "1,000,000"

    def test_custom_decimals(self):
        """自訂小數位數。"""
        assert _fmt_number(3.14159, 3) == "3.142"

    def test_negative(self):
        """負數應正確顯示。"""
        assert _fmt_number(-42.5, 1) == "-42.5"

    def test_zero(self):
        """零值應正確顯示。"""
        assert _fmt_number(0.0, 1) == "0.0"


class TestFmtPct:
    """_fmt_pct 百分比格式化測試。"""

    def test_none_returns_na(self):
        """None 應回傳 N/A。"""
        assert _fmt_pct(None) == "N/A"

    def test_normal_ratio(self):
        """0.15 → 15.0%。"""
        assert _fmt_pct(0.15) == "15.0%"

    def test_negative_ratio(self):
        """負值百分比。"""
        assert _fmt_pct(-0.05) == "-5.0%"

    def test_large_ratio(self):
        """大百分比（如 150%）。"""
        assert _fmt_pct(1.5) == "150.0%"

    def test_zero(self):
        """零值百分比。"""
        assert _fmt_pct(0.0) == "0.0%"


class TestFmtLarge:
    """_fmt_large 大數字縮寫測試。"""

    def test_none_returns_na(self):
        """None 應回傳 N/A。"""
        assert _fmt_large(None) == "N/A"

    def test_trillion(self):
        """兆級數字。"""
        assert _fmt_large(1.5e12) == "$1.5T"

    def test_billion(self):
        """十億級數字。"""
        assert _fmt_large(50e9) == "$50.0B"

    def test_million(self):
        """百萬級數字。"""
        assert _fmt_large(7.5e6) == "$7.5M"

    def test_thousand(self):
        """千級數字。"""
        assert _fmt_large(5000.0) == "$5.0K"

    def test_small_number(self):
        """小數字。"""
        assert _fmt_large(500.0) == "$500"

    def test_negative_billion(self):
        """負數十億。"""
        assert _fmt_large(-3e9) == "-$3.0B"

    def test_negative_million(self):
        """負數百萬。"""
        assert _fmt_large(-7.5e6) == "-$7.5M"


class TestFmtPrice:
    """_fmt_price 價格格式化測試。"""

    def test_none_returns_na(self):
        """None 應回傳 N/A。"""
        assert _fmt_price(None) == "N/A"

    def test_normal_price(self):
        """一般價格。"""
        assert _fmt_price(150.25) == "$150.25"

    def test_large_price(self):
        """高價股。"""
        assert _fmt_price(1234.56) == "$1,234.56"


class TestFmtRatio:
    """_fmt_ratio 倍數格式化測試。"""

    def test_none_returns_na(self):
        """None 應回傳 N/A。"""
        assert _fmt_ratio(None) == "N/A"

    def test_normal_ratio(self):
        """一般倍數。"""
        assert _fmt_ratio(12.5) == "12.5x"

    def test_custom_decimals(self):
        """自訂小數位。"""
        assert _fmt_ratio(3.14159, 2) == "3.14x"


# ============================================================
# T1 估值報告模板測試
# ============================================================

class TestRenderT1Valuation:
    """T1 價值估值報告渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T1 標題和股票資訊。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "T1: 價值估值報告" in result
        assert "Test Corp" in result
        assert "TEST" in result

    def test_contains_valuation_multiples(self):
        """報告應包含估值倍數。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "EV/EBITDA" in result
        assert "12.5x" in result
        assert "P/E (Trailing)" in result
        assert "15.0x" in result

    def test_contains_analyst_targets(self):
        """報告應包含分析師目標價。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "分析師目標價共識" in result
        assert "$180.00" in result  # target_price_mean
        assert "$220.00" in result  # target_price_high
        assert "$140.00" in result  # target_price_low

    def test_upside_calculation(self):
        """應計算上行空間百分比。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        # 目標價 180 / 現價 150 - 1 = 20%
        assert "+20.0%" in result

    def test_contains_recommendation_distribution(self):
        """報告應包含分析師推薦分布。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "分析師推薦分布" in result
        assert "強力買入" in result

    def test_contains_fcf_history(self):
        """報告應包含自由現金流歷史。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "自由現金流歷史" in result

    def test_contains_dcf_inputs(self):
        """報告應包含 DCF 輸入參數。"""
        data = _make_deep_analysis()
        result = _render_t1_valuation(data)
        assert "Beta" in result
        assert "Graham Number" in result
        assert "$120.00" in result  # graham_number

    def test_no_targets_when_none(self):
        """目標價為 None 時不應出現目標價段落。"""
        data = _make_deep_analysis(valuation=_make_valuation(target_price_mean=None))
        result = _render_t1_valuation(data)
        assert "分析師目標價共識" not in result


# ============================================================
# T2 財務體質報告模板測試
# ============================================================

class TestRenderT2FinancialHealth:
    """T2 財務體質報告渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T2 標題。"""
        data = _make_deep_analysis()
        result = _render_t2_financial_health(data)
        assert "T2: 財務體質檢查" in result
        assert "Test Corp" in result

    def test_contains_balance_sheet(self):
        """報告應包含資產負債表快照。"""
        data = _make_deep_analysis()
        result = _render_t2_financial_health(data)
        assert "資產負債表快照" in result
        assert "總資產" in result
        assert "$200.0B" in result  # total_assets

    def test_contains_solvency_ratios(self):
        """報告應包含償債能力指標。"""
        data = _make_deep_analysis()
        result = _render_t2_financial_health(data)
        assert "流動比率" in result
        assert "1.5" in result  # current_ratio

    def test_contains_revenue_trend(self):
        """報告應包含損益表趨勢。"""
        data = _make_deep_analysis()
        result = _render_t2_financial_health(data)
        assert "損益表趨勢" in result
        assert "營收" in result
        assert "EBITDA" in result

    def test_contains_cashflow_trend(self):
        """報告應包含現金流量趨勢。"""
        data = _make_deep_analysis()
        result = _render_t2_financial_health(data)
        assert "現金流量趨勢" in result
        assert "營運現金流" in result
        assert "資本支出" in result

    def test_empty_history_no_table(self):
        """空歷史數據時不應出現趨勢表。"""
        data = _make_deep_analysis(
            financial_health=_make_financial_health(
                revenue_history={},
                operating_cashflow_history={},
            )
        )
        result = _render_t2_financial_health(data)
        assert "損益表趨勢" not in result
        assert "現金流量趨勢" not in result


# ============================================================
# T3 成長動能報告模板測試
# ============================================================

class TestRenderT3GrowthMomentum:
    """T3 成長動能報告渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T3 標題。"""
        data = _make_deep_analysis()
        result = _render_t3_growth_momentum(data)
        assert "T3: 成長動能分析" in result

    def test_contains_growth_rates(self):
        """報告應包含成長率指標。"""
        data = _make_deep_analysis()
        result = _render_t3_growth_momentum(data)
        assert "營收成長率" in result
        assert "11.0%" in result  # revenue_growth 0.11

    def test_contains_eps_estimates(self):
        """報告應包含 EPS 預估。"""
        data = _make_deep_analysis()
        result = _render_t3_growth_momentum(data)
        assert "分析師 EPS 預估" in result
        assert "0q" in result  # period

    def test_contains_earnings_surprises(self):
        """報告應包含盈餘驚喜。"""
        data = _make_deep_analysis()
        result = _render_t3_growth_momentum(data)
        assert "歷史盈餘驚喜" in result
        assert "2024-10-24" in result

    def test_no_eps_section_when_empty(self):
        """EPS 預估為空時不應出現該段落。"""
        data = _make_deep_analysis(growth_momentum=_make_growth(eps_estimates=[]))
        result = _render_t3_growth_momentum(data)
        assert "分析師 EPS 預估" not in result

    def test_no_surprise_section_when_empty(self):
        """驚喜記錄為空時不應出現該段落。"""
        data = _make_deep_analysis(growth_momentum=_make_growth(earnings_surprises=[]))
        result = _render_t3_growth_momentum(data)
        assert "歷史盈餘驚喜" not in result


# ============================================================
# T4 風險報告模板測試
# ============================================================

class TestRenderT4RiskScenario:
    """T4 風險與情境報告渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T4 標題。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        assert "T4: 風險與情境分析" in result

    def test_contains_volatility_metrics(self):
        """報告應包含波動性指標。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        assert "Beta" in result
        assert "52 週最高" in result
        assert "$180.00" in result  # 52w high

    def test_contains_price_position(self):
        """報告應包含 52 週價格位置。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        # 150 在 110-180 的位置 = (150-110)/(180-110) ≈ 57%
        assert "57%" in result

    def test_contains_short_metrics(self):
        """報告應包含放空指標。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        assert "放空比率" in result
        assert "Short Ratio" in result

    def test_contains_insider_transactions(self):
        """報告應包含內部交易摘要。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        assert "近 90 天內部交易" in result
        assert "John CEO" in result
        assert "Jane CFO" in result

    def test_insider_buy_sell_counts(self):
        """應正確計算買入/賣出筆數。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        # 1 筆 Buy，1 筆 Sale
        assert "| 買入 | 1 |" in result
        assert "| 賣出 | 1 |" in result

    def test_contains_institutional_holders(self):
        """報告應包含機構持股。"""
        data = _make_deep_analysis()
        result = _render_t4_risk_scenario(data)
        assert "前 5 大機構持股" in result
        assert "Vanguard Group" in result
        assert "BlackRock" in result

    def test_no_insider_section_when_empty(self):
        """無內部交易時不應出現該段落。"""
        data = _make_deep_analysis(risk_metrics=_make_risk(insider_transactions=[]))
        result = _render_t4_risk_scenario(data)
        assert "近 90 天內部交易" not in result

    def test_no_institutional_section_when_empty(self):
        """無機構持股時不應出現該段落。"""
        data = _make_deep_analysis(risk_metrics=_make_risk(top_institutional_holders=[]))
        result = _render_t4_risk_scenario(data)
        assert "前 5 大機構持股" not in result


# ============================================================
# T5 同業比較報告模板測試
# ============================================================

class TestRenderT5PeerComparison:
    """T5 同業競爭力排名報告渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T5 標題。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "T5: 同業競爭力排名" in result

    def test_contains_industry_info(self):
        """報告應包含產業資訊。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "Technology" in result
        assert "Software - Infrastructure" in result

    def test_contains_ranking_summary(self):
        """報告應包含排名摘要。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "排名摘要" in result
        assert "P/E" in result

    def test_trophy_emoji_for_rank_1(self):
        """排名第 1 應有獎盃 emoji。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "🏆" in result

    def test_contains_peer_table(self):
        """報告應包含同業比較表。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "同業比較表" in result
        assert "PEER1" in result
        assert "PEER2" in result

    def test_target_stock_bold(self):
        """目標股應以粗體標示。"""
        data = _make_deep_analysis()
        result = _render_t5_peer_comparison(data)
        assert "**TEST**" in result

    def test_no_peers_shows_warning(self):
        """無同業數據時應顯示警告。"""
        data = _make_deep_analysis(peer_comparison=_make_peers(peers=[]))
        result = _render_t5_peer_comparison(data)
        assert "⚠️" in result
        assert "無同業數據" in result

    def test_no_ranking_when_empty(self):
        """無排名數據時不應出現排名段落。"""
        data = _make_deep_analysis(peer_comparison=_make_peers(rank_in_peers={}))
        result = _render_t5_peer_comparison(data)
        assert "排名摘要" not in result


# ============================================================
# T6 投資決策摘要模板測試
# ============================================================

class TestRenderT6InvestmentSummary:
    """T6 投資決策摘要渲染測試。"""

    def test_contains_header(self):
        """報告應包含 T6 標題。"""
        data = _make_deep_analysis()
        result = _render_t6_investment_summary(data)
        assert "T6: 投資決策摘要" in result

    def test_contains_quick_overview(self):
        """報告應包含快速概覽。"""
        data = _make_deep_analysis()
        result = _render_t6_investment_summary(data)
        assert "快速概覽" in result
        assert "$50.0B" in result  # market_cap
        assert "$150.00" in result  # current_price

    def test_contains_four_dimension_assessment(self):
        """報告應包含四維評估。"""
        data = _make_deep_analysis()
        result = _render_t6_investment_summary(data)
        assert "四維評估" in result
        assert "估值" in result
        assert "財務體質" in result
        assert "成長動能" in result
        assert "風險水平" in result

    def test_valuation_undervalued(self):
        """上行空間 >20% 應判為被低估。"""
        # target_price_mean=200, current_price=150 → 33.3%
        data = _make_deep_analysis(
            valuation=_make_valuation(target_price_mean=200.0),
        )
        result = _render_t6_investment_summary(data)
        assert "🟢" in result
        assert "被低估" in result

    def test_valuation_overvalued(self):
        """大幅下行應判為被高估。"""
        data = _make_deep_analysis(
            current_price=250.0,
            valuation=_make_valuation(target_price_mean=200.0),
        )
        result = _render_t6_investment_summary(data)
        assert "🔴" in result
        assert "被高估" in result

    def test_valuation_fair_slightly_low(self):
        """小幅上行 (0~20%) 應判為合理偏低。"""
        data = _make_deep_analysis(
            current_price=170.0,
            valuation=_make_valuation(target_price_mean=180.0),
        )
        result = _render_t6_investment_summary(data)
        assert "合理偏低" in result

    def test_valuation_fair(self):
        """小幅下行 (0~-10%) 應判為合理估值。"""
        data = _make_deep_analysis(
            current_price=190.0,
            valuation=_make_valuation(target_price_mean=180.0),
        )
        result = _render_t6_investment_summary(data)
        assert "合理估值" in result

    def test_health_strong(self):
        """流動比率 >= 2 應判為財務穩健。"""
        data = _make_deep_analysis(
            financial_health=_make_financial_health(current_ratio=2.5),
        )
        result = _render_t6_investment_summary(data)
        assert "財務穩健" in result

    def test_health_acceptable(self):
        """流動比率 1~2 應判為可接受。"""
        data = _make_deep_analysis(
            financial_health=_make_financial_health(current_ratio=1.5),
        )
        result = _render_t6_investment_summary(data)
        assert "財務可接受" in result

    def test_health_risky(self):
        """流動比率 <1 應判為流動性風險。"""
        data = _make_deep_analysis(
            financial_health=_make_financial_health(current_ratio=0.7),
        )
        result = _render_t6_investment_summary(data)
        assert "流動性風險" in result

    def test_growth_high(self):
        """盈餘成長 >20% 應判為高成長。"""
        data = _make_deep_analysis(
            growth_momentum=_make_growth(earnings_growth=0.35),
        )
        result = _render_t6_investment_summary(data)
        assert "高成長" in result

    def test_growth_stable(self):
        """盈餘成長 0~20% 應判為穩定成長。"""
        data = _make_deep_analysis(
            growth_momentum=_make_growth(earnings_growth=0.10),
        )
        result = _render_t6_investment_summary(data)
        assert "穩定成長" in result

    def test_growth_declining(self):
        """盈餘負成長應判為衰退。"""
        data = _make_deep_analysis(
            growth_momentum=_make_growth(earnings_growth=-0.05),
        )
        result = _render_t6_investment_summary(data)
        assert "盈餘衰退" in result

    def test_risk_low_volatility(self):
        """Beta <0.8 應判為低波動。"""
        data = _make_deep_analysis(
            risk_metrics=_make_risk(beta=0.5),
        )
        result = _render_t6_investment_summary(data)
        assert "低波動" in result

    def test_risk_medium_volatility(self):
        """Beta 0.8~1.2 應判為中等波動。"""
        data = _make_deep_analysis(
            risk_metrics=_make_risk(beta=1.0),
        )
        result = _render_t6_investment_summary(data)
        assert "中等波動" in result

    def test_risk_high_volatility(self):
        """Beta >=1.2 應判為高波動。"""
        data = _make_deep_analysis(
            risk_metrics=_make_risk(beta=1.5),
        )
        result = _render_t6_investment_summary(data)
        assert "高波動" in result

    def test_contains_key_data(self):
        """報告應包含關鍵數據表。"""
        data = _make_deep_analysis()
        result = _render_t6_investment_summary(data)
        assert "關鍵數據" in result
        assert "P/E (Trailing)" in result
        assert "EV/EBITDA" in result
        assert "Graham Number" in result

    def test_none_values_show_na(self):
        """None 值指標應顯示 N/A。"""
        data = _make_deep_analysis(
            current_price=None,
            valuation=_make_valuation(target_price_mean=None),
            financial_health=_make_financial_health(current_ratio=None),
            growth_momentum=_make_growth(earnings_growth=None),
            risk_metrics=_make_risk(beta=None),
        )
        result = _render_t6_investment_summary(data)
        # 四維判斷均應為 N/A
        assert result.count("N/A") >= 4


# ============================================================
# generate_report 主函數測試
# ============================================================

class TestGenerateReport:
    """generate_report 主函數測試。"""

    def test_returns_three_keys(self):
        """回傳應包含 json_data, markdown_report, summary 三個 key。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        assert "json_data" in result
        assert "markdown_report" in result
        assert "summary" in result

    def test_json_data_is_dict(self):
        """json_data 應為字典。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        assert isinstance(result["json_data"], dict)
        assert result["json_data"]["symbol"] == "TEST"

    def test_markdown_report_contains_all_sections(self):
        """Markdown 報告應包含所有 6 個模板的標題。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        md = result["markdown_report"]
        assert "T1: 價值估值報告" in md
        assert "T2: 財務體質檢查" in md
        assert "T3: 成長動能分析" in md
        assert "T4: 風險與情境分析" in md
        assert "T5: 同業競爭力排名" in md
        assert "T6: 投資決策摘要" in md

    def test_markdown_report_header(self):
        """Markdown 報告應有總標題。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        md = result["markdown_report"]
        assert "# 深度分析報告: Test Corp (TEST)" in md

    def test_markdown_report_metadata(self):
        """Markdown 報告應包含元資料（產業、市值、日期）。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        md = result["markdown_report"]
        assert "Technology" in md
        assert "$50.0B" in md
        assert "2026-02-17" in md

    def test_summary_contains_key_fields(self):
        """summary 應包含關鍵決策欄位。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        s = result["summary"]
        assert s["symbol"] == "TEST"
        assert s["company_name"] == "Test Corp"
        assert s["current_price"] == 150.0
        assert s["target_price"] == 180.0
        assert s["recommendation"] == "buy"
        assert s["graham_number"] == 120.0

    def test_summary_upside_calculation(self):
        """summary 的上行空間應正確計算。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        # target 180 / price 150 - 1 = 0.2 → 20%
        assert abs(result["summary"]["upside_pct"] - 20.0) < 0.1

    def test_summary_upside_none_when_no_target(self):
        """無目標價時 upside_pct 應為 None。"""
        data = _make_deep_analysis(
            valuation=_make_valuation(target_price_mean=None)
        )
        result = generate_report(data, ai_summary=False)
        assert result["summary"]["upside_pct"] is None

    def test_summary_upside_none_when_no_price(self):
        """無現價時 upside_pct 應為 None。"""
        data = _make_deep_analysis(current_price=None)
        result = generate_report(data, ai_summary=False)
        assert result["summary"]["upside_pct"] is None

    def test_t6_summary_comes_first(self):
        """T6 投資決策摘要應出現在其他模板之前。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        md = result["markdown_report"]
        t6_pos = md.index("T6: 投資決策摘要")
        t1_pos = md.index("T1: 價值估值報告")
        assert t6_pos < t1_pos

    def test_all_none_data_no_crash(self):
        """全部 None 的數據不應導致崩潰。"""
        data = DeepAnalysisData(
            symbol="EMPTY",
            company_name="Empty Corp",
            sector="Unknown",
            industry="Unknown",
        )
        result = generate_report(data, ai_summary=False)
        assert result["json_data"]["symbol"] == "EMPTY"
        assert isinstance(result["markdown_report"], str)
        assert len(result["markdown_report"]) > 0

    def test_returns_five_keys(self):
        """回傳應包含 5 個 key（含 ai_summary 和 chart_path）。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        assert "json_data" in result
        assert "markdown_report" in result
        assert "summary" in result
        assert "ai_summary" in result
        assert "chart_path" in result

    def test_ai_summary_false_skips_t0(self):
        """ai_summary=False 時報告不應包含 T0。"""
        data = _make_deep_analysis()
        result = generate_report(data, ai_summary=False)
        md = result["markdown_report"]
        assert "T0: 白話分析摘要" not in md
        assert result["ai_summary"] is None

    def test_chart_without_output_dir_returns_none(self):
        """未提供 output_dir 時 chart_path 應為 None。"""
        data = _make_deep_analysis()
        data.price_history = {"dates": ["2026-01-01"], "closes": [100.0]}
        result = generate_report(data, ai_summary=False, include_chart=True)
        assert result["chart_path"] is None

    def test_chart_false_skips_chart(self):
        """include_chart=False 時不應生成圖表。"""
        data = _make_deep_analysis()
        data.price_history = {"dates": ["2026-01-01"], "closes": [100.0]}
        result = generate_report(data, ai_summary=False, include_chart=False)
        assert result["chart_path"] is None
        assert "價格走勢" not in result["markdown_report"]
