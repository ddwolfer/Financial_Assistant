"""
同業比較器。

從股票清單中找出同產業的公司，批量抓取關鍵指標，
計算目標股在同業中各項指標的排名。
"""

import logging
from typing import Optional

import yfinance as yf

from scripts.scanner.data_fetcher import fetch_batch_metrics, TickerMetrics
from scripts.analyzer.deep_data_fetcher import (
    PeerComparisonData,
    _safe_float,
)

logger = logging.getLogger(__name__)


def find_peers(
    symbol: str,
    sector: str,
    industry: str,
    universe: str = "sp500",
    count: int = 5,
) -> list[str]:
    """
    從指定股票清單中找出同產業的股票作為同業。

    優先找同 industry，不足時擴展到同 sector。
    排除目標股自身。

    Args:
        symbol: 目標股票代碼
        sector: 目標股的產業大類（如 Technology）
        industry: 目標股的細分產業（如 Software）
        universe: 使用的股票清單 (sp500, sp400, sp600, sp1500)
        count: 需要的同業數量

    Returns:
        同業股票代碼列表
    """
    from scripts.scanner.universe import (
        get_sp500_tickers,
        get_sp400_tickers,
        get_sp600_tickers,
        get_sp1500_tickers,
    )

    universe_map = {
        "sp500": get_sp500_tickers,
        "sp400": get_sp400_tickers,
        "sp600": get_sp600_tickers,
        "sp1500": get_sp1500_tickers,
    }

    get_tickers = universe_map.get(universe, get_sp500_tickers)
    all_tickers = get_tickers()

    # 排除目標股
    candidates = [t for t in all_tickers if t.upper() != symbol.upper()]

    # 需要知道每支股票的 sector/industry，使用快取的 Layer 1 數據
    metrics_list = fetch_batch_metrics(candidates)

    # 第一輪：找同 industry
    same_industry = [
        m for m in metrics_list
        if m.industry and m.industry == industry
        and m.symbol.upper() != symbol.upper()
        and not m.fetch_error
    ]

    if len(same_industry) >= count:
        # 按市值排序，取前 count 支
        same_industry.sort(key=lambda m: m.market_cap or 0, reverse=True)
        return [m.symbol for m in same_industry[:count]]

    # 第二輪：擴展到同 sector
    same_sector = [
        m for m in metrics_list
        if m.sector and m.sector == sector
        and m.symbol.upper() != symbol.upper()
        and not m.fetch_error
    ]

    # ★ 先按市值排序，確保合併時優先選市值大的同業
    same_industry.sort(key=lambda m: m.market_cap or 0, reverse=True)
    same_sector.sort(key=lambda m: m.market_cap or 0, reverse=True)

    # 合併：先同 industry（已按市值排序），再補充同 sector（已按市值排序）
    seen = set(m.symbol for m in same_industry)
    combined = list(same_industry)
    for m in same_sector:
        if m.symbol not in seen:
            combined.append(m)
            seen.add(m.symbol)
        if len(combined) >= count:
            break

    return [m.symbol for m in combined[:count]]


def fetch_peer_metrics(
    peer_symbols: list[str],
) -> list[dict]:
    """
    批量抓取同業的關鍵比較指標。

    每支同業抓取 PE, EV/EBITDA, ROE, 毛利率, 市值等。
    使用 Layer 1 快取加速。

    Args:
        peer_symbols: 同業股票代碼列表

    Returns:
        每支同業的指標字典列表
    """
    peers_data = []

    for symbol in peer_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            peers_data.append({
                "symbol": symbol,
                "name": info.get("shortName", ""),
                "pe": _safe_float(info.get("trailingPE")),
                "forward_pe": _safe_float(info.get("forwardPE")),
                "ev_ebitda": _safe_float(info.get("enterpriseToEbitda")),
                "ev_revenue": _safe_float(info.get("enterpriseToRevenue")),
                "price_to_book": _safe_float(info.get("priceToBook")),
                "roe": _safe_float(info.get("returnOnEquity")),
                "gross_margin": _safe_float(info.get("grossMargins")),
                "operating_margin": _safe_float(info.get("operatingMargins")),
                "profit_margin": _safe_float(info.get("profitMargins")),
                "revenue_growth": _safe_float(info.get("revenueGrowth")),
                "earnings_growth": _safe_float(info.get("earningsGrowth")),
                "market_cap": _safe_float(info.get("marketCap")),
                "beta": _safe_float(info.get("beta")),
                "dividend_yield": _safe_float(info.get("dividendYield")),
                "debt_to_equity": _safe_float(
                    info.get("debtToEquity") / 100.0
                    if info.get("debtToEquity") is not None
                    else None
                ),
            })
        except Exception as e:
            logger.warning("無法抓取同業 %s: %s", symbol, e)
            peers_data.append({"symbol": symbol, "name": "", "pe": None})

    return peers_data


def rank_among_peers(
    target_metrics: dict,
    peers: list[dict],
) -> dict[str, int]:
    """
    計算目標股在同業中各指標的排名。

    排名規則：
    - PE, EV/EBITDA, Debt/Equity: 越低越好（排名 1 = 最低）
    - ROE, Margin, Growth: 越高越好（排名 1 = 最高）

    Args:
        target_metrics: 目標股的指標字典（與 peers 格式相同）
        peers: 同業指標列表

    Returns:
        {指標名: 排名} 字典，1 = 最佳
    """
    # 越低越好的指標
    lower_is_better = ["pe", "forward_pe", "ev_ebitda", "debt_to_equity"]
    # 越高越好的指標
    higher_is_better = [
        "roe", "gross_margin", "operating_margin", "profit_margin",
        "revenue_growth", "earnings_growth",
    ]

    all_entries = [target_metrics] + peers
    rankings = {}

    for metric_name in lower_is_better + higher_is_better:
        # 收集有效值
        values = []
        for entry in all_entries:
            val = entry.get(metric_name)
            if val is not None:
                values.append((entry["symbol"], val))

        if not values:
            continue

        # 排序
        reverse = metric_name in higher_is_better
        values.sort(key=lambda x: x[1], reverse=reverse)

        # 找目標股的排名
        for rank, (sym, _) in enumerate(values, 1):
            if sym == target_metrics["symbol"]:
                rankings[metric_name] = rank
                break

    return rankings


def build_peer_comparison(
    symbol: str,
    sector: str,
    industry: str,
    target_info: dict,
    universe: str = "sp500",
    peer_count: int = 5,
) -> PeerComparisonData:
    """
    完整的同業比較流程：找同業 → 抓指標 → 排名。

    這是 peer_finder 模組的主入口函數。

    Args:
        symbol: 目標股票代碼
        sector: 產業大類
        industry: 細分產業
        target_info: 目標股的 yfinance info 字典
        universe: 股票清單
        peer_count: 同業數量

    Returns:
        PeerComparisonData 含同業列表和排名
    """
    # 1. 找同業
    peer_symbols = find_peers(symbol, sector, industry, universe, peer_count)
    logger.info("%s 找到 %d 個同業: %s", symbol, len(peer_symbols), peer_symbols)

    if not peer_symbols:
        return PeerComparisonData(sector=sector, industry=industry)

    # 2. 抓取同業指標
    peers = fetch_peer_metrics(peer_symbols)

    # 3. 建立目標股的指標（與 peers 格式一致）
    raw_de = target_info.get("debtToEquity")
    target_metrics = {
        "symbol": symbol,
        "name": target_info.get("shortName", ""),
        "pe": _safe_float(target_info.get("trailingPE")),
        "forward_pe": _safe_float(target_info.get("forwardPE")),
        "ev_ebitda": _safe_float(target_info.get("enterpriseToEbitda")),
        "ev_revenue": _safe_float(target_info.get("enterpriseToRevenue")),
        "price_to_book": _safe_float(target_info.get("priceToBook")),
        "roe": _safe_float(target_info.get("returnOnEquity")),
        "gross_margin": _safe_float(target_info.get("grossMargins")),
        "operating_margin": _safe_float(target_info.get("operatingMargins")),
        "profit_margin": _safe_float(target_info.get("profitMargins")),
        "revenue_growth": _safe_float(target_info.get("revenueGrowth")),
        "earnings_growth": _safe_float(target_info.get("earningsGrowth")),
        "market_cap": _safe_float(target_info.get("marketCap")),
        "beta": _safe_float(target_info.get("beta")),
        "dividend_yield": _safe_float(target_info.get("dividendYield")),
        "debt_to_equity": _safe_float(raw_de / 100.0 if raw_de is not None else None),
    }

    # 4. 排名
    rankings = rank_among_peers(target_metrics, peers)

    return PeerComparisonData(
        peers=peers,
        sector=sector,
        industry=industry,
        rank_in_peers=rankings,
    )
