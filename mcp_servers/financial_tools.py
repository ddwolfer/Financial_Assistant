"""
MCP Server: Financial Analysis Tools.

Exposes tools for Claude to interact with the screening pipeline
and data cache via the Model Context Protocol.

Run with: uv run python mcp_servers/financial_tools.py
"""

from pathlib import Path

from fastmcp import FastMCP

from scripts.scanner.data_fetcher import fetch_ticker_metrics
from scripts.scanner.config import calculate_graham_number
from scripts.scanner.results_store import load_latest_results

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


if __name__ == "__main__":
    mcp.run()
