"""
Layer 3 深度分析 CLI 進入點。

用法:
    # 指定股票分析
    uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT

    # 從 Layer 1 篩選結果自動載入通過的股票
    uv run python -m scripts.analyzer.run_layer3 --from-layer1

    # 強制重新抓取，忽略快取
    uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --force-refresh

    # 指定股票清單範圍（同業比較用）
    uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --universe sp1500
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.analyzer.deep_data_fetcher import (
    fetch_deep_data,
    DeepDataCache,
    DeepAnalysisData,
)
from scripts.analyzer.peer_finder import build_peer_comparison
from scripts.analyzer.report_generator import generate_report
from scripts.scanner.results_store import (
    load_latest_results,
    save_deep_analysis,
)

# 報告輸出目錄
REPORTS_DIR = Path("data/reports")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 全域快取實例
_cache = DeepDataCache()


def _load_layer1_passed_tickers() -> list[str]:
    """
    從最新的 Layer 1 篩選結果中載入通過的股票代碼。

    優先載入雙軌制結果，其次載入絕對門檻結果。
    """
    # 先嘗試雙軌制結果
    data = load_latest_results(tag="layer1_dual")
    if data is None:
        data = load_latest_results(tag="layer1")

    if data is None:
        logger.error("找不到 Layer 1 篩選結果，請先執行 Layer 1 篩選")
        return []

    passed_tickers = []
    for r in data.get("results", []):
        if r.get("passed", False):
            passed_tickers.append(r["symbol"])

    logger.info(
        "從 Layer 1 結果載入 %d 支通過篩選的股票 (共 %d 支)",
        len(passed_tickers), data.get("total_screened", 0),
    )
    return passed_tickers


def _analyze_single(
    symbol: str,
    universe: str = "sp500",
    peer_count: int = 5,
    use_cache: bool = True,
    ai_summary: bool = True,
    include_chart: bool = True,
) -> dict | None:
    """
    對單一股票執行完整深度分析流程。

    流程：抓取深度數據 → 同業比較 → 生成報告 → 持久化。

    Returns:
        generate_report() 的結果字典，或 None（失敗時）
    """
    # 1. 檢查快取
    if use_cache:
        cached = _cache.get(symbol)
        if cached is not None:
            logger.info("[快取命中] %s，直接生成報告", symbol)
            result = generate_report(
                cached,
                ai_summary=ai_summary,
                include_chart=include_chart,
                output_dir=REPORTS_DIR,
            )
            return result

    # 2. 抓取深度數據
    logger.info("[抓取中] %s 深度數據...", symbol)
    deep_data = fetch_deep_data(symbol)

    if not deep_data.company_name:
        logger.warning("[跳過] %s: 無法取得基礎數據", symbol)
        return None

    # 3. 同業比較
    if deep_data.sector and deep_data.industry:
        logger.info("[同業比較] %s: %s > %s", symbol, deep_data.sector, deep_data.industry)
        try:
            import yfinance as yf
            target_info = yf.Ticker(symbol).info or {}
            peer_data = build_peer_comparison(
                symbol=symbol,
                sector=deep_data.sector,
                industry=deep_data.industry,
                target_info=target_info,
                universe=universe,
                peer_count=peer_count,
            )
            deep_data.peer_comparison = peer_data
        except Exception as e:
            logger.warning("[同業比較失敗] %s: %s", symbol, e)
    else:
        logger.warning("[跳過同業比較] %s: 缺少產業資訊", symbol)

    # 4. 快取存入
    if use_cache:
        _cache.put(deep_data)
        _cache.save()

    # 5. 生成報告
    result = generate_report(
        deep_data,
        ai_summary=ai_summary,
        include_chart=include_chart,
        output_dir=REPORTS_DIR,
    )

    # 6. 持久化
    paths = save_deep_analysis(
        symbol=symbol,
        json_data=result["json_data"],
        markdown_report=result["markdown_report"],
    )
    logger.info("[完成] %s → %s", symbol, paths["json_path"].name)

    return result


def _print_summary(results: list[dict]):
    """印出所有分析結果的摘要表格。"""
    if not results:
        print("\n⚠️ 沒有成功完成分析的股票。")
        return

    print("\n" + "=" * 80)
    print("📊 Layer 3 深度分析摘要")
    print("=" * 80)

    header = f"{'代碼':8s} | {'公司名稱':20s} | {'現價':>10s} | {'目標價':>10s} | {'上行空間':>8s} | {'推薦':8s} | {'品質':>5s}"
    print(header)
    print("-" * len(header))

    for r in results:
        s = r["summary"]
        sym = s.get("symbol", "")[:8]
        name = (s.get("company_name", "") or "")[:20]
        price = f"${s['current_price']:.2f}" if s.get("current_price") else "N/A"
        target = f"${s['target_price']:.2f}" if s.get("target_price") else "N/A"
        upside = f"{s['upside_pct']:+.1f}%" if s.get("upside_pct") is not None else "N/A"
        rec = (s.get("recommendation") or "N/A").upper()[:8]
        quality = f"{s.get('data_quality_score', 0) * 100:.0f}%"

        print(f"{sym:8s} | {name:20s} | {price:>10s} | {target:>10s} | {upside:>8s} | {rec:8s} | {quality:>5s}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Layer 3 Deep Analysis — 深度分析與報告生成",
    )
    parser.add_argument(
        "--tickers", nargs="+",
        help="指定要分析的股票代碼（空格分隔）",
    )
    parser.add_argument(
        "--from-layer1", action="store_true", default=False,
        help="自動載入 Layer 1 篩選通過的股票",
    )
    parser.add_argument(
        "--universe",
        choices=["sp500", "sp400", "sp600", "sp1500"],
        default="sp500",
        help="同業比較使用的股票清單（預設: sp500）",
    )
    parser.add_argument(
        "--peer-count", type=int, default=5,
        help="每支股票的同業比較數量（預設: 5）",
    )
    parser.add_argument(
        "--force-refresh", action="store_true", default=False,
        help="強制重新抓取所有資料，忽略快取",
    )
    parser.add_argument(
        "--no-ai-summary", action="store_true", default=False,
        help="停用 AI 白話摘要（T0）",
    )
    parser.add_argument(
        "--no-chart", action="store_true", default=False,
        help="停用價格走勢圖",
    )
    args = parser.parse_args()

    # 取得分析目標
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif args.from_layer1:
        tickers = _load_layer1_passed_tickers()
        if not tickers:
            sys.exit(1)
    else:
        parser.error("請指定 --tickers 或 --from-layer1")
        return

    use_cache = not args.force_refresh
    ai_summary = not args.no_ai_summary
    include_chart = not args.no_chart

    logger.info("=" * 60)
    logger.info("Layer 3 深度分析開始")
    logger.info("分析目標: %d 支股票: %s", len(tickers), tickers)
    logger.info("同業比較範圍: %s, 每支 %d 個同業", args.universe, args.peer_count)
    logger.info("快取: %s", "啟用" if use_cache else "停用 (--force-refresh)")
    logger.info("AI 白話摘要: %s", "啟用" if ai_summary else "停用")
    logger.info("價格走勢圖: %s", "啟用" if include_chart else "停用")
    logger.info("=" * 60)

    # 載入快取
    if use_cache:
        _cache.load()

    # 逐支分析
    results = []
    for i, symbol in enumerate(tickers, 1):
        logger.info("[%d/%d] 開始分析 %s...", i, len(tickers), symbol)
        try:
            result = _analyze_single(
                symbol=symbol,
                universe=args.universe,
                peer_count=args.peer_count,
                use_cache=use_cache,
                ai_summary=ai_summary,
                include_chart=include_chart,
            )
            if result:
                results.append(result)
        except Exception as e:
            logger.error("[失敗] %s: %s", symbol, e)

    # 印出摘要
    _print_summary(results)

    logger.info(
        "分析完成: %d/%d 支成功", len(results), len(tickers),
    )


if __name__ == "__main__":
    main()
