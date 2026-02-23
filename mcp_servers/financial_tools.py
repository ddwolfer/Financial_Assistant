"""
MCP Server: Financial Analysis Tools.

提供 Claude 透過 MCP 協議操作篩選管線、數據快取和深度分析的工具。

Run with: uv run python mcp_servers/financial_tools.py
"""

from pathlib import Path

from fastmcp import FastMCP

from scripts.scanner.data_fetcher import fetch_ticker_metrics
from scripts.scanner.config import calculate_graham_number
from scripts.scanner.results_store import (
    load_latest_results,
    save_deep_analysis,
    load_latest_deep_analysis,
    load_latest_deep_analysis_report,
    list_deep_analysis_symbols,
)

mcp = FastMCP("QuantAnalyst Financial Tools")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@mcp.tool
def check_data_cache(ticker: str) -> dict:
    """
    Check if fresh screening data exists for a ticker.

    Returns cache status and last screening timestamp if available.
    """
    latest = load_latest_results()
    if latest is None:
        return {"cached": False, "message": "No screening data found."}

    for result in latest.get("results", []):
        if result["symbol"].upper() == ticker.upper():
            return {
                "cached": True,
                "timestamp": latest["timestamp"],
                "data": result,
            }

    return {
        "cached": False,
        "message": f"Ticker {ticker} not found in latest screening.",
        "screening_timestamp": latest.get("timestamp"),
    }


@mcp.tool
def fetch_missing_data(ticker: str) -> dict:
    """
    Fetch financial metrics for a ticker from yfinance.

    Returns raw financial data including P/E, PEG, ROE, D/E,
    EPS, book value, and calculated Graham Number.
    """
    metrics = fetch_ticker_metrics(ticker)

    if metrics.fetch_error:
        return {"success": False, "error": metrics.fetch_error}

    graham = None
    if metrics.trailing_eps and metrics.book_value:
        graham = calculate_graham_number(metrics.trailing_eps, metrics.book_value)

    return {
        "success": True,
        "symbol": metrics.symbol,
        "company_name": metrics.company_name,
        "trailing_pe": metrics.trailing_pe,
        "forward_pe": metrics.forward_pe,
        "peg_ratio": metrics.peg_ratio,
        "roe": metrics.roe,
        "debt_to_equity": metrics.debt_to_equity,
        "trailing_eps": metrics.trailing_eps,
        "book_value": metrics.book_value,
        "current_price": metrics.current_price,
        "graham_number": graham,
        "sector": metrics.sector,
        "industry": metrics.industry,
        "market_cap": metrics.market_cap,
    }


@mcp.tool
def calculate_financial_metrics(ticker: str) -> dict:
    """
    Calculate derived financial metrics for a ticker.

    Computes Graham Number, margin of safety, and screening verdict.
    """
    from scripts.scanner.screener import screen_ticker

    metrics = fetch_ticker_metrics(ticker)
    if metrics.fetch_error:
        return {"success": False, "error": metrics.fetch_error}

    result = screen_ticker(metrics)
    return {
        "success": True,
        "symbol": result.symbol,
        "screening_passed": result.passed,
        "graham_number": result.graham_number,
        "current_price": result.current_price,
        "margin_of_safety_pct": result.margin_of_safety_pct,
        "fail_reasons": result.fail_reasons,
    }


@mcp.tool
def run_sector_screening(
    universe: str = "sp500",
    percentile_threshold: float = 0.30,
) -> dict:
    """
    Run dual-track sector-relative screening on a stock universe.

    Screens stocks using sector-relative percentile ranking (Track 1)
    combined with safety thresholds (Track 2). Returns stocks that
    pass both filters, with sector distribution info.

    Args:
        universe: Stock universe to screen (sp500, sp400, sp600, sp1500)
        percentile_threshold: Top X% within sector (default 0.30 = top 30%)
    """
    from scripts.scanner.data_fetcher import fetch_batch_metrics
    from scripts.scanner.config import SectorRelativeThresholds
    from scripts.scanner.sector_screener import screen_batch_dual_track
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

    if universe not in universe_map:
        return {
            "success": False,
            "error": f"Unknown universe: {universe}. Choose from: {list(universe_map.keys())}",
        }

    tickers = universe_map[universe]()
    metrics_list = fetch_batch_metrics(tickers)

    thresholds = SectorRelativeThresholds(
        sector_percentile_threshold=percentile_threshold,
    )
    results = screen_batch_dual_track(metrics_list, thresholds)

    passed = [r for r in results if r.passed]

    # 產業分布
    sector_dist: dict[str, dict] = {}
    for r in results:
        if r.metrics and r.metrics.sector:
            sector = r.metrics.sector
            if sector not in sector_dist:
                sector_dist[sector] = {"screened": 0, "passed": 0}
            sector_dist[sector]["screened"] += 1
            if r.passed:
                sector_dist[sector]["passed"] += 1

    return {
        "success": True,
        "universe": universe,
        "total_screened": len(results),
        "total_passed": len(passed),
        "sector_distribution": sector_dist,
        "passed_stocks": [r.to_dict() for r in passed],
    }


@mcp.tool
def fetch_deep_analysis(ticker: str, force_refresh: bool = False) -> dict:
    """
    Execute deep analysis for a single ticker.

    Fetches comprehensive financial data from yfinance (12 API endpoints),
    performs peer comparison, and returns structured JSON data.
    Results are cached for 24 hours unless force_refresh=True.

    Returns the full DeepAnalysisData as a JSON dict, including:
    - Valuation multiples (EV/EBITDA, P/E, P/B, analyst targets)
    - Financial health (3-5 year history, balance sheet, cash flow)
    - Growth momentum (EPS/revenue estimates, earnings surprises)
    - Risk metrics (beta, short ratio, insider transactions)
    - Peer comparison (5 industry peers ranked by key metrics)

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        force_refresh: If True, ignore cache and re-fetch all data
    """
    from scripts.analyzer.deep_data_fetcher import (
        fetch_deep_data,
        DeepDataCache,
    )
    from scripts.analyzer.peer_finder import build_peer_comparison

    cache = DeepDataCache()
    use_cache = not force_refresh

    # 檢查快取
    if use_cache:
        cache.load()
        cached = cache.get(ticker)
        if cached is not None:
            return {
                "success": True,
                "source": "cache",
                "data": cached.to_dict(),
            }

    # 抓取深度數據
    try:
        deep_data = fetch_deep_data(ticker)
    except Exception as e:
        return {"success": False, "error": f"抓取失敗: {e}"}

    if not deep_data.company_name:
        return {"success": False, "error": f"無法取得 {ticker} 的基礎數據"}

    # 同業比較
    if deep_data.sector and deep_data.industry:
        try:
            import yfinance as yf
            target_info = yf.Ticker(ticker).info or {}
            peer_data = build_peer_comparison(
                symbol=ticker,
                sector=deep_data.sector,
                industry=deep_data.industry,
                target_info=target_info,
            )
            deep_data.peer_comparison = peer_data
        except Exception:
            pass  # 同業比較失敗不影響主要分析

    # 存入快取
    if use_cache:
        cache.put(deep_data)
        cache.save()

    return {
        "success": True,
        "source": "fresh",
        "data": deep_data.to_dict(),
    }


@mcp.tool
def generate_analysis_report(
    ticker: str,
    force_refresh: bool = False,
    ai_summary: bool = True,
    include_chart: bool = True,
) -> dict:
    """
    Generate a complete analysis report for a ticker.

    Runs deep analysis and produces both structured JSON and a
    human-readable Markdown report. The report includes 6 sections:

    T0: AI Plain-Language Summary (optional, requires ANTHROPIC_API_KEY)
    T1: Valuation Report (DCF inputs, multiples, analyst targets, price chart)
    T2: Financial Health Check (balance sheet, P&L trends, cash flow)
    T3: Growth Momentum (growth rates, EPS estimates, earnings surprises)
    T4: Risk & Scenario Analysis (volatility, short interest, insider trading)
    T5: Peer Comparison (industry peers ranked by key metrics)
    T6: Investment Decision Summary (4-dimensional assessment)

    The Markdown report and JSON data are also saved to disk.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        force_refresh: If True, ignore cache and re-fetch all data
        ai_summary: If True (default), generate AI plain-language summary (T0)
        include_chart: If True (default), generate 6-month price chart in T1
    """
    from scripts.analyzer.deep_data_fetcher import (
        fetch_deep_data,
        DeepDataCache,
        DeepAnalysisData,
    )
    from scripts.analyzer.peer_finder import build_peer_comparison
    from scripts.analyzer.report_generator import generate_report

    cache = DeepDataCache()
    use_cache = not force_refresh
    deep_data = None

    # 檢查快取
    if use_cache:
        cache.load()
        deep_data = cache.get(ticker)

    # 若無快取，重新抓取
    if deep_data is None:
        try:
            deep_data = fetch_deep_data(ticker)
        except Exception as e:
            return {"success": False, "error": f"抓取失敗: {e}"}

        if not deep_data.company_name:
            return {"success": False, "error": f"無法取得 {ticker} 的基礎數據"}

        # 同業比較
        if deep_data.sector and deep_data.industry:
            try:
                import yfinance as yf
                target_info = yf.Ticker(ticker).info or {}
                peer_data = build_peer_comparison(
                    symbol=ticker,
                    sector=deep_data.sector,
                    industry=deep_data.industry,
                    target_info=target_info,
                )
                deep_data.peer_comparison = peer_data
            except Exception:
                pass

        # 存入快取
        if use_cache:
            cache.put(deep_data)
            cache.save()

    # 生成報告
    from pathlib import Path
    reports_dir = Path("data/reports")
    result = generate_report(
        deep_data,
        ai_summary=ai_summary,
        include_chart=include_chart,
        output_dir=reports_dir,
    )

    # 持久化
    try:
        paths = save_deep_analysis(
            symbol=ticker,
            json_data=result["json_data"],
            markdown_report=result["markdown_report"],
        )
        saved_files = {
            "json_file": str(paths["json_path"]),
            "markdown_file": str(paths["markdown_path"]),
        }
    except Exception:
        saved_files = {}

    return {
        "success": True,
        "summary": result["summary"],
        "markdown_report": result["markdown_report"],
        "ai_summary": result.get("ai_summary"),
        "chart_path": result.get("chart_path"),
        "saved_files": saved_files,
    }


if __name__ == "__main__":
    mcp.run()
