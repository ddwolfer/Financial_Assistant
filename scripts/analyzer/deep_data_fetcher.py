"""
Layer 3 深度分析數據抓取器。

針對 Layer 1 通過的股票，從 yfinance 抓取完整的財務報表、
分析師預估、持股結構等深度數據，用於投行等級分析報告。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
import math
import time

import pandas as pd
import yfinance as yf

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


# ============================================================
# DataFrame → dict 轉換輔助函數
# ============================================================

def _safe_float(value) -> Optional[float]:
    """安全轉換為 float，處理 NaN / None / inf。"""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _df_row_to_history(df: pd.DataFrame, row_name: str) -> dict[str, float]:
    """
    從 DataFrame 中取出指定行，轉為 {年份: 數值} 的字典。

    yfinance 的 financials/balance_sheet/cashflow 的 columns 是 Timestamp，
    index 是項目名稱。
    """
    if df is None or df.empty:
        return {}

    if row_name not in df.index:
        return {}

    row = df.loc[row_name]
    result = {}
    for col in row.index:
        val = _safe_float(row[col])
        if val is not None:
            # 將 Timestamp 轉為年份字串
            if hasattr(col, "year"):
                key = str(col.year)
            else:
                key = str(col)
            result[key] = val

    return result


def _df_to_records(df: pd.DataFrame, max_rows: int = 10) -> list[dict]:
    """
    將 DataFrame 轉為 list[dict]，處理 NaN 和 Timestamp。

    用於 earnings_estimate、revenue_estimate、insider_transactions 等。
    """
    if df is None or df.empty:
        return []

    records = []
    for idx, row in df.head(max_rows).iterrows():
        record = {}
        # 索引也加入
        if hasattr(idx, "isoformat"):
            record["date"] = idx.isoformat()
        elif hasattr(idx, "year"):
            record["period"] = str(idx)
        else:
            record["period"] = str(idx)

        for col in row.index:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            elif hasattr(val, "isoformat"):
                record[col] = val.isoformat()
            elif isinstance(val, (int, float)):
                record[col] = _safe_float(val)
            else:
                record[col] = str(val)
        records.append(record)

    return records


def _compute_margin_history(
    numerator_history: dict[str, float],
    denominator_history: dict[str, float],
) -> dict[str, float]:
    """計算毛利率/營業利益率等比率的歷史。"""
    result = {}
    for year, denom in denominator_history.items():
        num = numerator_history.get(year)
        if num is not None and denom and denom != 0:
            result[year] = round(num / denom, 4)
    return result


# ============================================================
# 深度數據抓取函數
# ============================================================

def _extract_valuation(info: dict, cashflow_df: pd.DataFrame) -> ValuationData:
    """
    從 ticker.info 和 cashflow 提取 T1 估值數據。

    包含估值倍數、分析師目標價、DCF 輸入參數。
    """
    # FCF 歷史
    fcf_history = _df_row_to_history(cashflow_df, "Free Cash Flow")

    return ValuationData(
        ev_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),
        ev_to_revenue=_safe_float(info.get("enterpriseToRevenue")),
        price_to_book=_safe_float(info.get("priceToBook")),
        price_to_sales=_safe_float(info.get("priceToSalesTrailing12Months")),
        trailing_pe=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        target_price_mean=_safe_float(info.get("targetMeanPrice")),
        target_price_median=_safe_float(info.get("targetMedianPrice")),
        target_price_high=_safe_float(info.get("targetHighPrice")),
        target_price_low=_safe_float(info.get("targetLowPrice")),
        analyst_count=info.get("numberOfAnalystOpinions"),
        recommendation_key=info.get("recommendationKey"),
        recommendation_mean=_safe_float(info.get("recommendationMean")),
        free_cashflow=_safe_float(info.get("freeCashflow")),
        free_cashflow_history=fcf_history,
        beta=_safe_float(info.get("beta")),
        enterprise_value=_safe_float(info.get("enterpriseValue")),
        dividend_yield=_safe_float(info.get("dividendYield")),
        payout_ratio=_safe_float(info.get("payoutRatio")),
    )


def _extract_recommendations_summary(ticker: yf.Ticker) -> Optional[dict]:
    """從 ticker.recommendations 提取分析師推薦分布。"""
    try:
        rec = ticker.recommendations
        if rec is None or rec.empty:
            return None
        # 取最新一期
        latest = rec.iloc[-1]
        return {
            "strongBuy": int(latest.get("strongBuy", 0)),
            "buy": int(latest.get("buy", 0)),
            "hold": int(latest.get("hold", 0)),
            "sell": int(latest.get("sell", 0)),
            "strongSell": int(latest.get("strongSell", 0)),
        }
    except Exception as e:
        logger.debug("無法取得 recommendations: %s", e)
        return None


def _extract_financial_health(
    info: dict,
    financials_df: pd.DataFrame,
    balance_sheet_df: pd.DataFrame,
    cashflow_df: pd.DataFrame,
) -> FinancialHealthData:
    """
    從三表提取 T2 財務體質數據。

    處理 yfinance DataFrame 的各種行名差異。
    """
    # 損益表歷史
    revenue_hist = _df_row_to_history(financials_df, "Total Revenue")
    net_income_hist = _df_row_to_history(financials_df, "Net Income")

    # EBITDA：嘗試多個可能的行名
    ebitda_hist = _df_row_to_history(financials_df, "EBITDA")
    if not ebitda_hist:
        ebitda_hist = _df_row_to_history(financials_df, "Normalized EBITDA")

    # 毛利率 = Gross Profit / Total Revenue
    gross_profit_hist = _df_row_to_history(financials_df, "Gross Profit")
    gross_margin_hist = _compute_margin_history(gross_profit_hist, revenue_hist)

    # 營業利益率 = Operating Income / Total Revenue
    operating_income_hist = _df_row_to_history(financials_df, "Operating Income")
    operating_margin_hist = _compute_margin_history(operating_income_hist, revenue_hist)

    # 現金流歷史
    opcf_hist = _df_row_to_history(cashflow_df, "Operating Cash Flow")
    capex_hist = _df_row_to_history(cashflow_df, "Capital Expenditure")
    fcf_hist = _df_row_to_history(cashflow_df, "Free Cash Flow")

    # 資產負債表快照（最新一期）
    def _latest_bs(row_name: str) -> Optional[float]:
        """取資產負債表最新一期的值。"""
        hist = _df_row_to_history(balance_sheet_df, row_name)
        if not hist:
            return None
        # 取最新年份（key 排序最大）
        latest_year = max(hist.keys())
        return hist[latest_year]

    return FinancialHealthData(
        revenue_history=revenue_hist,
        net_income_history=net_income_hist,
        ebitda_history=ebitda_hist,
        gross_margin_history=gross_margin_hist,
        operating_margin_history=operating_margin_hist,
        total_assets=_latest_bs("Total Assets"),
        total_liabilities=_latest_bs("Total Liabilities Net Minority Interest"),
        total_equity=_latest_bs("Stockholders Equity"),
        total_debt=_safe_float(info.get("totalDebt")),
        total_cash=_safe_float(info.get("totalCash")),
        current_ratio=_safe_float(info.get("currentRatio")),
        quick_ratio=_safe_float(info.get("quickRatio")),
        working_capital=_latest_bs("Working Capital"),
        operating_cashflow_history=opcf_hist,
        capex_history=capex_hist,
        free_cashflow_history=fcf_hist,
    )


def _extract_growth_momentum(
    info: dict,
    ticker: yf.Ticker,
) -> GrowthMomentumData:
    """
    從分析師預估和盈餘驚喜提取 T3 成長動能數據。

    呼叫 ticker.earnings_estimate、revenue_estimate、earnings_dates。
    """
    # EPS 預估
    eps_est = []
    try:
        ee = ticker.earnings_estimate
        if ee is not None and not ee.empty:
            eps_est = _df_to_records(ee)
    except Exception as e:
        logger.debug("無法取得 earnings_estimate: %s", e)

    # 營收預估
    rev_est = []
    try:
        re_ = ticker.revenue_estimate
        if re_ is not None and not re_.empty:
            rev_est = _df_to_records(re_)
    except Exception as e:
        logger.debug("無法取得 revenue_estimate: %s", e)

    # 盈餘驚喜
    surprises = []
    try:
        ed = ticker.earnings_dates
        if ed is not None and not ed.empty:
            # 只取有 Reported EPS 的記錄（已發布的）
            reported = ed.dropna(subset=["Reported EPS"]) if "Reported EPS" in ed.columns else ed
            records = _df_to_records(reported, max_rows=8)
            # 重新命名欄位
            for rec in records:
                surprises.append({
                    "date": rec.get("date", ""),
                    "estimate": rec.get("EPS Estimate"),
                    "actual": rec.get("Reported EPS"),
                    "surprise_pct": rec.get("Surprise(%)"),
                })
    except Exception as e:
        logger.debug("無法取得 earnings_dates: %s", e)

    return GrowthMomentumData(
        eps_estimates=eps_est,
        revenue_estimates=rev_est,
        earnings_surprises=surprises,
        revenue_growth=_safe_float(info.get("revenueGrowth")),
        earnings_growth=_safe_float(info.get("earningsGrowth")),
        earnings_quarterly_growth=_safe_float(info.get("earningsQuarterlyGrowth")),
    )


def _extract_risk_metrics(
    info: dict,
    ticker: yf.Ticker,
) -> RiskMetricsData:
    """
    從 info 和持股數據提取 T4 風險指標。

    包含波動性、放空、內部交易、機構持股。
    """
    # 內部交易（過濾近 90 天）
    insider_txns = []
    try:
        it = ticker.insider_transactions
        if it is not None and not it.empty:
            # 過濾近 90 天
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            for _, row in it.iterrows():
                start_date = row.get("Start Date")
                if start_date is not None and hasattr(start_date, "year"):
                    if pd.Timestamp(start_date).tz_localize("UTC") < cutoff:
                        continue
                insider_txns.append({
                    "insider": str(row.get("Insider", "")),
                    "position": str(row.get("Position", "")),
                    "transaction": str(row.get("Transaction", "")),
                    "shares": _safe_float(row.get("Shares")),
                    "value": _safe_float(row.get("Value")),
                    "date": str(row.get("Start Date", "")),
                })
            # 最多保留 20 筆
            insider_txns = insider_txns[:20]
    except Exception as e:
        logger.debug("無法取得 insider_transactions: %s", e)

    # 機構持股 Top 10
    inst_holders = []
    try:
        ih = ticker.institutional_holders
        if ih is not None and not ih.empty:
            for _, row in ih.head(10).iterrows():
                inst_holders.append({
                    "holder": str(row.get("Holder", "")),
                    "pct_held": _safe_float(row.get("pctHeld")),
                    "shares": _safe_float(row.get("Shares")),
                    "value": _safe_float(row.get("Value")),
                })
    except Exception as e:
        logger.debug("無法取得 institutional_holders: %s", e)

    return RiskMetricsData(
        beta=_safe_float(info.get("beta")),
        short_ratio=_safe_float(info.get("shortRatio")),
        short_percent_of_float=_safe_float(info.get("shortPercentOfFloat")),
        fifty_two_week_high=_safe_float(info.get("fiftyTwoWeekHigh")),
        fifty_two_week_low=_safe_float(info.get("fiftyTwoWeekLow")),
        fifty_two_week_change=_safe_float(info.get("52WeekChange")),
        current_price=_safe_float(info.get("currentPrice")),
        held_percent_insiders=_safe_float(info.get("heldPercentInsiders")),
        held_percent_institutions=_safe_float(info.get("heldPercentInstitutions")),
        insider_transactions=insider_txns,
        top_institutional_holders=inst_holders,
    )


# ============================================================
# 主抓取函數
# ============================================================

def fetch_deep_data(
    symbol: str,
    retry_count: int = 2,
    retry_delay: float = 1.0,
) -> DeepAnalysisData:
    """
    從 yfinance 抓取單一股票的完整深度分析數據。

    整合 12 個 yfinance API 呼叫，填充 T1-T4 所有子結構。
    T5（同業比較）由 peer_finder 模組另外處理。

    Args:
        symbol: 股票代碼
        retry_count: 失敗重試次數
        retry_delay: 重試間隔（秒）

    Returns:
        DeepAnalysisData，即使部分 API 失敗也會回傳已取得的資料。
    """
    for attempt in range(retry_count + 1):
        try:
            ticker = yf.Ticker(symbol)

            # 1. 基礎資訊（ticker.info）
            info = ticker.info or {}
            if not info or info.get("quoteType") is None:
                logger.warning("無法取得 %s 的基礎資訊", symbol)
                return DeepAnalysisData(
                    symbol=symbol,
                    company_name="",
                    sector="",
                    industry="",
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )

            # 2. 財務報表（三表）
            financials_df = _safe_get_df(ticker, "financials")
            balance_sheet_df = _safe_get_df(ticker, "balance_sheet")
            cashflow_df = _safe_get_df(ticker, "cashflow")

            # 3. 提取各子結構
            valuation = _extract_valuation(info, cashflow_df)

            # 補充推薦分布
            valuation.recommendations_summary = _extract_recommendations_summary(ticker)

            financial_health = _extract_financial_health(
                info, financials_df, balance_sheet_df, cashflow_df
            )

            growth_momentum = _extract_growth_momentum(info, ticker)

            risk_metrics = _extract_risk_metrics(info, ticker)

            # 4. 組裝最終數據包
            deep_data = DeepAnalysisData(
                symbol=symbol,
                company_name=info.get("shortName", "") or info.get("longName", ""),
                sector=info.get("sector", ""),
                industry=info.get("industry", ""),
                market_cap=_safe_float(info.get("marketCap")),
                current_price=_safe_float(info.get("currentPrice")),
                currency=info.get("currency", "USD"),
                valuation=valuation,
                financial_health=financial_health,
                growth_momentum=growth_momentum,
                risk_metrics=risk_metrics,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

            # 5. 計算數據品質分數
            deep_data.data_quality_score = calculate_data_quality_score(deep_data)

            logger.info(
                "%s 深度數據抓取完成 (品質分數: %.0f%%)",
                symbol, deep_data.data_quality_score * 100,
            )
            return deep_data

        except Exception as e:
            if attempt < retry_count:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    "%s 深度抓取第 %d/%d 次失敗: %s，%.1f 秒後重試",
                    symbol, attempt + 1, retry_count + 1, e, delay,
                )
                time.sleep(delay)
            else:
                logger.error("%s 深度抓取全部失敗: %s", symbol, e)
                return DeepAnalysisData(
                    symbol=symbol,
                    company_name="",
                    sector="",
                    industry="",
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )

    # 不應走到這裡
    return DeepAnalysisData(
        symbol=symbol, company_name="", sector="", industry="",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def fetch_batch_deep_data(
    symbols: list[str],
    delay_between: float = 0.5,
    progress_callback=None,
) -> list[DeepAnalysisData]:
    """
    批次抓取多支股票的深度數據。

    Args:
        symbols: 股票代碼列表
        delay_between: 每支股票間隔（秒），深度抓取建議 0.5s
        progress_callback: 進度回呼函數 callback(current, total)
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        data = fetch_deep_data(symbol)
        results.append(data)

        if progress_callback:
            progress_callback(i + 1, total)

        if i < total - 1:
            time.sleep(delay_between)

    return results


def _safe_get_df(ticker: yf.Ticker, attr_name: str) -> pd.DataFrame:
    """安全取得 ticker 的 DataFrame 屬性，失敗回傳空 DataFrame。"""
    try:
        df = getattr(ticker, attr_name, None)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        logger.debug("無法取得 %s.%s: %s", ticker.ticker, attr_name, e)
    return pd.DataFrame()
