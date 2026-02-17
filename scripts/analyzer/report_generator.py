"""
分析報告生成器。

將 DeepAnalysisData 轉化為結構化 JSON + Markdown 雙軌輸出。
包含 6 組核心分析模板的渲染邏輯。
"""

import logging
from typing import Optional

from scripts.analyzer.deep_data_fetcher import DeepAnalysisData

logger = logging.getLogger(__name__)


# ============================================================
# 數字格式化輔助函數
# ============================================================

def _fmt_number(value: Optional[float], decimals: int = 1) -> str:
    """格式化數字，None 顯示 N/A。"""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def _fmt_pct(value: Optional[float], decimals: int = 1) -> str:
    """格式化百分比（0.15 → 15.0%），None 顯示 N/A。"""
    if value is None:
        return "N/A"
    return f"{value * 100:,.{decimals}f}%"


def _fmt_large(value: Optional[float]) -> str:
    """格式化大數字（十億/百萬縮寫），None 顯示 N/A。"""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}${abs_val / 1e12:,.1f}T"
    elif abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:,.1f}B"
    elif abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:,.1f}M"
    elif abs_val >= 1e3:
        return f"{sign}${abs_val / 1e3:,.1f}K"
    else:
        return f"{sign}${abs_val:,.0f}"


def _fmt_price(value: Optional[float]) -> str:
    """格式化價格，None 顯示 N/A。"""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def _fmt_ratio(value: Optional[float], decimals: int = 1) -> str:
    """格式化倍數（如 P/E），None 顯示 N/A。"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}x"


# ============================================================
# T1: 價值估值報告
# ============================================================

def _render_t1_valuation(data: DeepAnalysisData) -> str:
    """渲染 T1 價值估值報告。"""
    v = data.valuation

    # 分析師目標價段落
    target_section = ""
    if v.target_price_mean is not None:
        upside = ""
        if data.current_price and v.target_price_mean:
            pct = (v.target_price_mean / data.current_price - 1) * 100
            upside = f" ({pct:+.1f}%)"
        target_section = f"""
### 分析師目標價共識
| 指標 | 數值 |
|------|------|
| 平均目標價 | {_fmt_price(v.target_price_mean)}{upside} |
| 中位數目標價 | {_fmt_price(v.target_price_median)} |
| 最高目標價 | {_fmt_price(v.target_price_high)} |
| 最低目標價 | {_fmt_price(v.target_price_low)} |
| 分析師人數 | {v.analyst_count or 'N/A'} |
| 共識推薦 | {(v.recommendation_key or 'N/A').upper()} |
"""

    # 推薦分布
    rec_section = ""
    if v.recommendations_summary:
        rs = v.recommendations_summary
        rec_section = f"""
### 分析師推薦分布
| 強力買入 | 買入 | 持有 | 賣出 | 強力賣出 |
|---------|------|------|------|---------|
| {rs.get('strongBuy', 0)} | {rs.get('buy', 0)} | {rs.get('hold', 0)} | {rs.get('sell', 0)} | {rs.get('strongSell', 0)} |
"""

    # FCF 歷史
    fcf_section = ""
    if v.free_cashflow_history:
        sorted_years = sorted(v.free_cashflow_history.keys())
        fcf_rows = " | ".join(sorted_years)
        fcf_vals = " | ".join(_fmt_large(v.free_cashflow_history[y]) for y in sorted_years)
        fcf_section = f"""
### 自由現金流歷史
| {fcf_rows} |
|{'---|' * len(sorted_years)}
| {fcf_vals} |
"""

    return f"""## T1: 價值估值報告 — {data.company_name} ({data.symbol})

### 基礎估值倍數
| 指標 | 數值 |
|------|------|
| EV/EBITDA | {_fmt_ratio(v.ev_to_ebitda)} |
| EV/Revenue | {_fmt_ratio(v.ev_to_revenue)} |
| P/E (Trailing) | {_fmt_ratio(v.trailing_pe)} |
| P/E (Forward) | {_fmt_ratio(v.forward_pe)} |
| P/B | {_fmt_ratio(v.price_to_book)} |
| P/S | {_fmt_ratio(v.price_to_sales)} |
| 企業價值 | {_fmt_large(v.enterprise_value)} |

### DCF 輸入參數
| 參數 | 數值 |
|------|------|
| 當前自由現金流 | {_fmt_large(v.free_cashflow)} |
| Beta | {_fmt_number(v.beta)} |
| 股利殖利率 | {_fmt_pct(v.dividend_yield)} |
| 配息率 | {_fmt_pct(v.payout_ratio)} |
| Graham Number | {_fmt_price(data.graham_number)} |
| 安全邊際 | {_fmt_pct(data.margin_of_safety_pct / 100 if data.margin_of_safety_pct else None)} |
{target_section}{rec_section}{fcf_section}"""


# ============================================================
# T2: 財務體質檢查
# ============================================================

def _render_t2_financial_health(data: DeepAnalysisData) -> str:
    """渲染 T2 財務體質報告。"""
    fh = data.financial_health

    # 收入趨勢表
    revenue_table = ""
    if fh.revenue_history:
        sorted_years = sorted(fh.revenue_history.keys())
        headers = " | ".join(sorted_years)
        rev_row = " | ".join(_fmt_large(fh.revenue_history.get(y)) for y in sorted_years)
        ni_row = " | ".join(_fmt_large(fh.net_income_history.get(y)) for y in sorted_years)
        ebitda_row = " | ".join(_fmt_large(fh.ebitda_history.get(y)) for y in sorted_years)
        gm_row = " | ".join(_fmt_pct(fh.gross_margin_history.get(y)) for y in sorted_years)
        om_row = " | ".join(_fmt_pct(fh.operating_margin_history.get(y)) for y in sorted_years)

        sep = "---|" * len(sorted_years)
        revenue_table = f"""
### 損益表趨勢
| 指標 | {headers} |
|------|{sep}
| 營收 | {rev_row} |
| 淨利 | {ni_row} |
| EBITDA | {ebitda_row} |
| 毛利率 | {gm_row} |
| 營業利益率 | {om_row} |
"""

    # 現金流趨勢
    cf_table = ""
    if fh.operating_cashflow_history:
        sorted_years = sorted(fh.operating_cashflow_history.keys())
        headers = " | ".join(sorted_years)
        opcf_row = " | ".join(_fmt_large(fh.operating_cashflow_history.get(y)) for y in sorted_years)
        capex_row = " | ".join(_fmt_large(fh.capex_history.get(y)) for y in sorted_years)
        fcf_row = " | ".join(_fmt_large(fh.free_cashflow_history.get(y)) for y in sorted_years)

        sep = "---|" * len(sorted_years)
        cf_table = f"""
### 現金流量趨勢
| 指標 | {headers} |
|------|{sep}
| 營運現金流 | {opcf_row} |
| 資本支出 | {capex_row} |
| 自由現金流 | {fcf_row} |
"""

    return f"""## T2: 財務體質檢查 — {data.company_name} ({data.symbol})

### 資產負債表快照
| 指標 | 數值 |
|------|------|
| 總資產 | {_fmt_large(fh.total_assets)} |
| 總負債 | {_fmt_large(fh.total_liabilities)} |
| 股東權益 | {_fmt_large(fh.total_equity)} |
| 總債務 | {_fmt_large(fh.total_debt)} |
| 現金及等價物 | {_fmt_large(fh.total_cash)} |
| 營運資金 | {_fmt_large(fh.working_capital)} |

### 償債能力指標
| 指標 | 數值 |
|------|------|
| 流動比率 | {_fmt_number(fh.current_ratio)} |
| 速動比率 | {_fmt_number(fh.quick_ratio)} |
{revenue_table}{cf_table}"""


# ============================================================
# T3: 成長動能分析
# ============================================================

def _render_t3_growth_momentum(data: DeepAnalysisData) -> str:
    """渲染 T3 成長動能報告。"""
    gm = data.growth_momentum

    # 成長率
    growth_section = f"""
### 成長率指標
| 指標 | 數值 |
|------|------|
| 營收成長率 (YoY) | {_fmt_pct(gm.revenue_growth)} |
| 盈餘成長率 (YoY) | {_fmt_pct(gm.earnings_growth)} |
| 盈餘季成長率 (QoQ) | {_fmt_pct(gm.earnings_quarterly_growth)} |
"""

    # EPS 預估
    eps_section = ""
    if gm.eps_estimates:
        eps_rows = ""
        for est in gm.eps_estimates:
            period = est.get("period", "")
            eps_rows += f"| {period} | {_fmt_number(est.get('avg'), 2)} | {_fmt_number(est.get('low'), 2)} | {_fmt_number(est.get('high'), 2)} | {est.get('numberOfAnalysts', 'N/A')} | {_fmt_pct(est.get('growth'))} |\n"

        eps_section = f"""
### 分析師 EPS 預估
| 期間 | 平均 | 最低 | 最高 | 分析師數 | 成長率 |
|------|------|------|------|---------|--------|
{eps_rows}"""

    # 盈餘驚喜
    surprise_section = ""
    if gm.earnings_surprises:
        surprise_rows = ""
        for s in gm.earnings_surprises[:6]:
            surprise_rows += f"| {s.get('date', '')[:10]} | {_fmt_number(s.get('estimate'), 2)} | {_fmt_number(s.get('actual'), 2)} | {_fmt_pct(s.get('surprise_pct', 0) / 100 if s.get('surprise_pct') else None)} |\n"

        surprise_section = f"""
### 歷史盈餘驚喜
| 日期 | 預估 EPS | 實際 EPS | 驚喜幅度 |
|------|---------|---------|---------|
{surprise_rows}"""

    return f"""## T3: 成長動能分析 — {data.company_name} ({data.symbol})
{growth_section}{eps_section}{surprise_section}"""


# ============================================================
# T4: 風險與情境分析
# ============================================================

def _render_t4_risk_scenario(data: DeepAnalysisData) -> str:
    """渲染 T4 風險報告。"""
    rm = data.risk_metrics

    # 52 週價格位置
    price_position = ""
    if rm.fifty_two_week_high and rm.fifty_two_week_low and rm.current_price:
        range_val = rm.fifty_two_week_high - rm.fifty_two_week_low
        if range_val > 0:
            pct_from_high = (rm.fifty_two_week_high - rm.current_price) / rm.fifty_two_week_high * 100
            pct_of_range = (rm.current_price - rm.fifty_two_week_low) / range_val * 100
            price_position = f"\n> 📍 現價位於 52 週區間的 {pct_of_range:.0f}% 位置，距離 52 週高點 -{pct_from_high:.1f}%\n"

    # 內部交易摘要
    insider_section = ""
    if rm.insider_transactions:
        buys = sum(1 for t in rm.insider_transactions if "buy" in t.get("transaction", "").lower())
        sells = sum(1 for t in rm.insider_transactions if "sell" in t.get("transaction", "").lower() or "sale" in t.get("transaction", "").lower())
        insider_section = f"""
### 近 90 天內部交易
| 類型 | 筆數 |
|------|------|
| 買入 | {buys} |
| 賣出 | {sells} |
"""
        # 列出前 5 筆
        insider_section += "\n| 內部人 | 職位 | 交易 | 股數 | 金額 |\n|--------|------|------|------|------|\n"
        for t in rm.insider_transactions[:5]:
            insider_section += f"| {t.get('insider', '')} | {t.get('position', '')} | {t.get('transaction', '')} | {_fmt_number(t.get('shares'), 0)} | {_fmt_large(t.get('value'))} |\n"

    # 機構持股
    inst_section = ""
    if rm.top_institutional_holders:
        inst_section = "\n### 前 5 大機構持股\n| 機構 | 持股比例 | 持股數 |\n|------|---------|-------|\n"
        for h in rm.top_institutional_holders[:5]:
            inst_section += f"| {h.get('holder', '')} | {_fmt_pct(h.get('pct_held'))} | {_fmt_number(h.get('shares'), 0)} |\n"

    return f"""## T4: 風險與情境分析 — {data.company_name} ({data.symbol})

### 波動性與市場風險
| 指標 | 數值 |
|------|------|
| Beta | {_fmt_number(rm.beta)} |
| 52 週最高 | {_fmt_price(rm.fifty_two_week_high)} |
| 52 週最低 | {_fmt_price(rm.fifty_two_week_low)} |
| 52 週漲跌幅 | {_fmt_pct(rm.fifty_two_week_change)} |
| 當前股價 | {_fmt_price(rm.current_price)} |
{price_position}
### 放空與持股結構
| 指標 | 數值 |
|------|------|
| 放空比率 (Short Ratio) | {_fmt_number(rm.short_ratio)} |
| 流通股放空比 | {_fmt_pct(rm.short_percent_of_float)} |
| 內部人持股 | {_fmt_pct(rm.held_percent_insiders)} |
| 機構持股 | {_fmt_pct(rm.held_percent_institutions)} |
{insider_section}{inst_section}"""


# ============================================================
# T5: 同業競爭力排名
# ============================================================

def _render_t5_peer_comparison(data: DeepAnalysisData) -> str:
    """渲染 T5 同業比較報告。"""
    pc = data.peer_comparison

    if not pc.peers:
        return f"""## T5: 同業競爭力排名 — {data.company_name} ({data.symbol})

> ⚠️ 無同業數據可供比較。
"""

    # 排名摘要
    rank_section = ""
    if pc.rank_in_peers:
        total = len(pc.peers) + 1  # 含自身
        rank_rows = ""
        metric_names = {
            "pe": "P/E", "forward_pe": "Forward P/E", "ev_ebitda": "EV/EBITDA",
            "roe": "ROE", "gross_margin": "毛利率", "operating_margin": "營業利益率",
            "profit_margin": "淨利率", "revenue_growth": "營收成長",
            "earnings_growth": "盈餘成長", "debt_to_equity": "D/E",
        }
        for metric, rank in sorted(pc.rank_in_peers.items(), key=lambda x: x[1]):
            name = metric_names.get(metric, metric)
            emoji = "🏆" if rank == 1 else ("🥈" if rank == 2 else "")
            rank_rows += f"| {name} | {rank}/{total} {emoji} |\n"

        rank_section = f"""
### 排名摘要（1 = 最佳）
| 指標 | 排名 |
|------|------|
{rank_rows}"""

    # 同業比較表
    peer_table = "### 同業比較表\n| 代碼 | 名稱 | P/E | EV/EBITDA | ROE | 毛利率 | 市值 |\n|------|------|-----|----------|-----|--------|------|\n"
    # 先列出目標股
    peer_table += f"| **{data.symbol}** | **{data.company_name}** | **{_fmt_ratio(data.valuation.trailing_pe)}** | **{_fmt_ratio(data.valuation.ev_to_ebitda)}** | **{_fmt_pct(data.risk_metrics.held_percent_insiders)}** | N/A | **{_fmt_large(data.market_cap)}** |\n"

    for p in pc.peers:
        peer_table += f"| {p.get('symbol', '')} | {p.get('name', '')[:20]} | {_fmt_ratio(p.get('pe'))} | {_fmt_ratio(p.get('ev_ebitda'))} | {_fmt_pct(p.get('roe'))} | {_fmt_pct(p.get('gross_margin'))} | {_fmt_large(p.get('market_cap'))} |\n"

    return f"""## T5: 同業競爭力排名 — {data.company_name} ({data.symbol})

> 產業: {pc.sector} > {pc.industry}
{rank_section}
{peer_table}"""


# ============================================================
# T6: 投資決策摘要
# ============================================================

def _render_t6_investment_summary(data: DeepAnalysisData) -> str:
    """渲染 T6 投資決策摘要（一頁式結論）。"""
    v = data.valuation
    fh = data.financial_health
    gm = data.growth_momentum
    rm = data.risk_metrics

    # 估值判斷
    valuation_verdict = "N/A"
    if v.target_price_mean and data.current_price:
        upside = (v.target_price_mean / data.current_price - 1) * 100
        if upside > 20:
            valuation_verdict = f"🟢 被低估 (上行空間 {upside:+.1f}%)"
        elif upside > 0:
            valuation_verdict = f"🟡 合理偏低 (上行空間 {upside:+.1f}%)"
        elif upside > -10:
            valuation_verdict = f"🟡 合理估值 ({upside:+.1f}%)"
        else:
            valuation_verdict = f"🔴 被高估 ({upside:+.1f}%)"

    # 財務健康
    health_verdict = "N/A"
    if fh.current_ratio is not None:
        if fh.current_ratio >= 2.0:
            health_verdict = "🟢 財務穩健"
        elif fh.current_ratio >= 1.0:
            health_verdict = "🟡 財務可接受"
        else:
            health_verdict = "🔴 流動性風險"

    # 成長判斷
    growth_verdict = "N/A"
    if gm.earnings_growth is not None:
        if gm.earnings_growth > 0.20:
            growth_verdict = f"🟢 高成長 ({_fmt_pct(gm.earnings_growth)})"
        elif gm.earnings_growth > 0:
            growth_verdict = f"🟡 穩定成長 ({_fmt_pct(gm.earnings_growth)})"
        else:
            growth_verdict = f"🔴 盈餘衰退 ({_fmt_pct(gm.earnings_growth)})"

    # 風險判斷
    risk_verdict = "N/A"
    if rm.beta is not None:
        if rm.beta < 0.8:
            risk_verdict = f"🟢 低波動 (Beta {rm.beta:.2f})"
        elif rm.beta < 1.2:
            risk_verdict = f"🟡 中等波動 (Beta {rm.beta:.2f})"
        else:
            risk_verdict = f"🔴 高波動 (Beta {rm.beta:.2f})"

    return f"""## T6: 投資決策摘要 — {data.company_name} ({data.symbol})

### 快速概覽
| 項目 | 數值 |
|------|------|
| 產業 | {data.sector} > {data.industry} |
| 市值 | {_fmt_large(data.market_cap)} |
| 當前股價 | {_fmt_price(data.current_price)} |
| 數據品質 | {data.data_quality_score * 100:.0f}% |

### 四維評估
| 維度 | 判斷 |
|------|------|
| 估值 | {valuation_verdict} |
| 財務體質 | {health_verdict} |
| 成長動能 | {growth_verdict} |
| 風險水平 | {risk_verdict} |

### 關鍵數據
| 指標 | 數值 |
|------|------|
| P/E (Trailing) | {_fmt_ratio(v.trailing_pe)} |
| EV/EBITDA | {_fmt_ratio(v.ev_to_ebitda)} |
| 自由現金流 | {_fmt_large(v.free_cashflow)} |
| 分析師目標價 | {_fmt_price(v.target_price_mean)} |
| 分析師推薦 | {(v.recommendation_key or 'N/A').upper()} |
| Graham Number | {_fmt_price(data.graham_number)} |
"""


# ============================================================
# 主生成函數
# ============================================================

def generate_report(data: DeepAnalysisData) -> dict:
    """
    生成完整的分析報告。

    Args:
        data: DeepAnalysisData 深度分析數據

    Returns:
        {
            "json_data": dict,        # 結構化 JSON（供 Dashboard）
            "markdown_report": str,    # 完整 Markdown 報告
            "summary": dict,           # T6 投資決策摘要的關鍵數據
        }
    """
    # 渲染各模板
    sections = [
        _render_t6_investment_summary(data),  # 摘要放最前面
        _render_t1_valuation(data),
        _render_t2_financial_health(data),
        _render_t3_growth_momentum(data),
        _render_t4_risk_scenario(data),
        _render_t5_peer_comparison(data),
    ]

    # 組裝完整報告
    header = f"""# 深度分析報告: {data.company_name} ({data.symbol})

> 產業: {data.sector} > {data.industry} | 市值: {_fmt_large(data.market_cap)} | 報告日期: {data.fetched_at[:10] if data.fetched_at else 'N/A'}

---
"""

    markdown_report = header + "\n---\n\n".join(sections)

    # 投資摘要數據
    v = data.valuation
    upside_pct = None
    if v.target_price_mean and data.current_price:
        upside_pct = (v.target_price_mean / data.current_price - 1) * 100

    summary = {
        "symbol": data.symbol,
        "company_name": data.company_name,
        "sector": data.sector,
        "current_price": data.current_price,
        "target_price": v.target_price_mean,
        "upside_pct": upside_pct,
        "recommendation": v.recommendation_key,
        "pe_ratio": v.trailing_pe,
        "ev_ebitda": v.ev_to_ebitda,
        "graham_number": data.graham_number,
        "data_quality_score": data.data_quality_score,
    }

    return {
        "json_data": data.to_dict(),
        "markdown_report": markdown_report,
        "summary": summary,
    }
