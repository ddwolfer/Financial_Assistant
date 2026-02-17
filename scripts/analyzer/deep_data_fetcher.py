"""
Layer 3 深度分析數據抓取器。

針對 Layer 1 通過的股票，從 yfinance 抓取完整的財務報表、
分析師預估、持股結構等深度數據，用於投行等級分析報告。
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 子數據結構
# ============================================================

@dataclass
class ValuationData:
    """T1 估值數據：倍數、分析師目標價、DCF 輸入參數。"""

    # 估值倍數
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None

    # 分析師共識
    target_price_mean: Optional[float] = None
    target_price_median: Optional[float] = None
    target_price_high: Optional[float] = None
    target_price_low: Optional[float] = None
    analyst_count: Optional[int] = None
    recommendation_key: Optional[str] = None  # "buy", "hold", "sell"
    recommendation_mean: Optional[float] = None  # 1=強力買入, 5=強力賣出

    # 分析師推薦分布
    recommendations_summary: Optional[dict] = None  # {strongBuy, buy, hold, sell, strongSell}

    # DCF 輸入
    free_cashflow: Optional[float] = None
    free_cashflow_history: dict[str, float] = field(default_factory=dict)
    beta: Optional[float] = None
    enterprise_value: Optional[float] = None

    # 股利
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None

    def to_dict(self) -> dict:
        """序列化為字典。"""
        return {
            "ev_to_ebitda": self.ev_to_ebitda,
            "ev_to_revenue": self.ev_to_revenue,
            "price_to_book": self.price_to_book,
            "price_to_sales": self.price_to_sales,
            "trailing_pe": self.trailing_pe,
            "forward_pe": self.forward_pe,
            "target_price_mean": self.target_price_mean,
            "target_price_median": self.target_price_median,
            "target_price_high": self.target_price_high,
            "target_price_low": self.target_price_low,
            "analyst_count": self.analyst_count,
            "recommendation_key": self.recommendation_key,
            "recommendation_mean": self.recommendation_mean,
            "recommendations_summary": self.recommendations_summary,
            "free_cashflow": self.free_cashflow,
            "free_cashflow_history": self.free_cashflow_history,
            "beta": self.beta,
            "enterprise_value": self.enterprise_value,
            "dividend_yield": self.dividend_yield,
            "payout_ratio": self.payout_ratio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValuationData":
        """從字典反序列化。"""
        return cls(
            ev_to_ebitda=data.get("ev_to_ebitda"),
            ev_to_revenue=data.get("ev_to_revenue"),
            price_to_book=data.get("price_to_book"),
            price_to_sales=data.get("price_to_sales"),
            trailing_pe=data.get("trailing_pe"),
            forward_pe=data.get("forward_pe"),
            target_price_mean=data.get("target_price_mean"),
            target_price_median=data.get("target_price_median"),
            target_price_high=data.get("target_price_high"),
            target_price_low=data.get("target_price_low"),
            analyst_count=data.get("analyst_count"),
            recommendation_key=data.get("recommendation_key"),
            recommendation_mean=data.get("recommendation_mean"),
            recommendations_summary=data.get("recommendations_summary"),
            free_cashflow=data.get("free_cashflow"),
            free_cashflow_history=data.get("free_cashflow_history", {}),
            beta=data.get("beta"),
            enterprise_value=data.get("enterprise_value"),
            dividend_yield=data.get("dividend_yield"),
            payout_ratio=data.get("payout_ratio"),
        )


@dataclass
class FinancialHealthData:
    """T2 財務體質數據：三表摘要、債務健康度。"""

    # 損益表歷史（年度，key = 年份字串如 "2024"）
    revenue_history: dict[str, float] = field(default_factory=dict)
    net_income_history: dict[str, float] = field(default_factory=dict)
    ebitda_history: dict[str, float] = field(default_factory=dict)
    gross_margin_history: dict[str, float] = field(default_factory=dict)
    operating_margin_history: dict[str, float] = field(default_factory=dict)

    # 資產負債表快照（最新一期）
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    working_capital: Optional[float] = None

    # 現金流歷史
    operating_cashflow_history: dict[str, float] = field(default_factory=dict)
    capex_history: dict[str, float] = field(default_factory=dict)
    free_cashflow_history: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """序列化為字典。"""
        return {
            "revenue_history": self.revenue_history,
            "net_income_history": self.net_income_history,
            "ebitda_history": self.ebitda_history,
            "gross_margin_history": self.gross_margin_history,
            "operating_margin_history": self.operating_margin_history,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "total_debt": self.total_debt,
            "total_cash": self.total_cash,
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "working_capital": self.working_capital,
            "operating_cashflow_history": self.operating_cashflow_history,
            "capex_history": self.capex_history,
            "free_cashflow_history": self.free_cashflow_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FinancialHealthData":
        """從字典反序列化。"""
        return cls(
            revenue_history=data.get("revenue_history", {}),
            net_income_history=data.get("net_income_history", {}),
            ebitda_history=data.get("ebitda_history", {}),
            gross_margin_history=data.get("gross_margin_history", {}),
            operating_margin_history=data.get("operating_margin_history", {}),
            total_assets=data.get("total_assets"),
            total_liabilities=data.get("total_liabilities"),
            total_equity=data.get("total_equity"),
            total_debt=data.get("total_debt"),
            total_cash=data.get("total_cash"),
            current_ratio=data.get("current_ratio"),
            quick_ratio=data.get("quick_ratio"),
            working_capital=data.get("working_capital"),
            operating_cashflow_history=data.get("operating_cashflow_history", {}),
            capex_history=data.get("capex_history", {}),
            free_cashflow_history=data.get("free_cashflow_history", {}),
        )


@dataclass
class GrowthMomentumData:
    """T3 成長動能數據：分析師預估、盈餘驚喜、成長率。"""

    # 分析師預估（每個元素包含 period, avg, low, high, num_analysts, growth）
    eps_estimates: list[dict] = field(default_factory=list)
    revenue_estimates: list[dict] = field(default_factory=list)

    # 歷史盈餘驚喜（每個元素包含 date, estimate, actual, surprise_pct）
    earnings_surprises: list[dict] = field(default_factory=list)

    # 成長率
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None

    def to_dict(self) -> dict:
        """序列化為字典。"""
        return {
            "eps_estimates": self.eps_estimates,
            "revenue_estimates": self.revenue_estimates,
            "earnings_surprises": self.earnings_surprises,
            "revenue_growth": self.revenue_growth,
            "earnings_growth": self.earnings_growth,
            "earnings_quarterly_growth": self.earnings_quarterly_growth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GrowthMomentumData":
        """從字典反序列化。"""
        return cls(
            eps_estimates=data.get("eps_estimates", []),
            revenue_estimates=data.get("revenue_estimates", []),
            earnings_surprises=data.get("earnings_surprises", []),
            revenue_growth=data.get("revenue_growth"),
            earnings_growth=data.get("earnings_growth"),
            earnings_quarterly_growth=data.get("earnings_quarterly_growth"),
        )


@dataclass
class RiskMetricsData:
    """T4 風險指標數據：波動性、放空、持股結構、內部交易。"""

    beta: Optional[float] = None

    # 放空數據
    short_ratio: Optional[float] = None
    short_percent_of_float: Optional[float] = None

    # 價格區間
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    fifty_two_week_change: Optional[float] = None
    current_price: Optional[float] = None

    # 持股結構
    held_percent_insiders: Optional[float] = None
    held_percent_institutions: Optional[float] = None

    # 內部交易（近 90 天，每個包含 insider, position, transaction, shares, value, date）
    insider_transactions: list[dict] = field(default_factory=list)

    # 機構持股 Top 10（每個包含 holder, pct_held, shares, value）
    top_institutional_holders: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """序列化為字典。"""
        return {
            "beta": self.beta,
            "short_ratio": self.short_ratio,
            "short_percent_of_float": self.short_percent_of_float,
            "fifty_two_week_high": self.fifty_two_week_high,
            "fifty_two_week_low": self.fifty_two_week_low,
            "fifty_two_week_change": self.fifty_two_week_change,
            "current_price": self.current_price,
            "held_percent_insiders": self.held_percent_insiders,
            "held_percent_institutions": self.held_percent_institutions,
            "insider_transactions": self.insider_transactions,
            "top_institutional_holders": self.top_institutional_holders,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RiskMetricsData":
        """從字典反序列化。"""
        return cls(
            beta=data.get("beta"),
            short_ratio=data.get("short_ratio"),
            short_percent_of_float=data.get("short_percent_of_float"),
            fifty_two_week_high=data.get("fifty_two_week_high"),
            fifty_two_week_low=data.get("fifty_two_week_low"),
            fifty_two_week_change=data.get("fifty_two_week_change"),
            current_price=data.get("current_price"),
            held_percent_insiders=data.get("held_percent_insiders"),
            held_percent_institutions=data.get("held_percent_institutions"),
            insider_transactions=data.get("insider_transactions", []),
            top_institutional_holders=data.get("top_institutional_holders", []),
        )


@dataclass
class PeerComparisonData:
    """T5 同業比較數據：同業指標清單與排名。"""

    # 同業列表（每個包含 symbol, name, pe, ev_ebitda, roe, margin, market_cap 等）
    peers: list[dict] = field(default_factory=list)
    sector: str = ""
    industry: str = ""

    # 目標股在同業中各指標的排名（1 = 最佳）
    rank_in_peers: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """序列化為字典。"""
        return {
            "peers": self.peers,
            "sector": self.sector,
            "industry": self.industry,
            "rank_in_peers": self.rank_in_peers,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PeerComparisonData":
        """從字典反序列化。"""
        return cls(
            peers=data.get("peers", []),
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            rank_in_peers=data.get("rank_in_peers", {}),
        )


# ============================================================
# 頂層數據容器
# ============================================================

@dataclass
class DeepAnalysisData:
    """Layer 3 深度分析完整數據包，整合 T1-T5 所有數據。"""

    symbol: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    currency: str = "USD"

    # Layer 1 繼承數據
    graham_number: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None

    # 子數據結構
    valuation: ValuationData = field(default_factory=ValuationData)
    financial_health: FinancialHealthData = field(default_factory=FinancialHealthData)
    growth_momentum: GrowthMomentumData = field(default_factory=GrowthMomentumData)
    risk_metrics: RiskMetricsData = field(default_factory=RiskMetricsData)
    peer_comparison: PeerComparisonData = field(default_factory=PeerComparisonData)

    # 元資料
    fetched_at: str = ""
    data_quality_score: float = 0.0  # 0-1，非 None 欄位比例

    def to_dict(self) -> dict:
        """序列化為字典，供 JSON 儲存。"""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "current_price": self.current_price,
            "currency": self.currency,
            "graham_number": self.graham_number,
            "margin_of_safety_pct": self.margin_of_safety_pct,
            "valuation": self.valuation.to_dict(),
            "financial_health": self.financial_health.to_dict(),
            "growth_momentum": self.growth_momentum.to_dict(),
            "risk_metrics": self.risk_metrics.to_dict(),
            "peer_comparison": self.peer_comparison.to_dict(),
            "fetched_at": self.fetched_at,
            "data_quality_score": self.data_quality_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeepAnalysisData":
        """從字典反序列化。"""
        return cls(
            symbol=data["symbol"],
            company_name=data.get("company_name", ""),
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            market_cap=data.get("market_cap"),
            current_price=data.get("current_price"),
            currency=data.get("currency", "USD"),
            graham_number=data.get("graham_number"),
            margin_of_safety_pct=data.get("margin_of_safety_pct"),
            valuation=ValuationData.from_dict(data.get("valuation", {})),
            financial_health=FinancialHealthData.from_dict(
                data.get("financial_health", {})
            ),
            growth_momentum=GrowthMomentumData.from_dict(
                data.get("growth_momentum", {})
            ),
            risk_metrics=RiskMetricsData.from_dict(data.get("risk_metrics", {})),
            peer_comparison=PeerComparisonData.from_dict(
                data.get("peer_comparison", {})
            ),
            fetched_at=data.get("fetched_at", ""),
            data_quality_score=data.get("data_quality_score", 0.0),
        )


def calculate_data_quality_score(data: DeepAnalysisData) -> float:
    """
    計算數據完整度分數（0-1）。

    檢查所有關鍵欄位是否有值，回傳非 None 的比例。
    """
    # 定義關鍵欄位清單
    key_fields = [
        data.market_cap,
        data.current_price,
        data.valuation.ev_to_ebitda,
        data.valuation.price_to_book,
        data.valuation.target_price_mean,
        data.valuation.analyst_count,
        data.valuation.free_cashflow,
        data.valuation.beta,
        data.financial_health.total_assets,
        data.financial_health.total_debt,
        data.financial_health.total_cash,
        data.financial_health.current_ratio,
        data.growth_momentum.revenue_growth,
        data.growth_momentum.earnings_growth,
        data.risk_metrics.beta,
        data.risk_metrics.fifty_two_week_high,
        data.risk_metrics.held_percent_insiders,
        data.risk_metrics.held_percent_institutions,
    ]

    # 歷史數據也算（有資料即得分）
    history_fields = [
        len(data.financial_health.revenue_history) > 0,
        len(data.financial_health.ebitda_history) > 0,
        len(data.financial_health.free_cashflow_history) > 0,
        len(data.growth_momentum.eps_estimates) > 0,
        len(data.growth_momentum.earnings_surprises) > 0,
        len(data.risk_metrics.insider_transactions) > 0,
        len(data.risk_metrics.top_institutional_holders) > 0,
        len(data.peer_comparison.peers) > 0,
    ]

    total = len(key_fields) + len(history_fields)
    filled = sum(1 for v in key_fields if v is not None)
    filled += sum(1 for v in history_fields if v)

    return round(filled / total, 2) if total > 0 else 0.0
