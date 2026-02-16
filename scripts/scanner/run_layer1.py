"""
CLI entry point for Layer 1 quantitative screening.

Usage:
    uv run python -m scripts.scanner.run_layer1 --tickers AAPL MSFT GOOGL
    uv run python -m scripts.scanner.run_layer1 --universe sp500
    uv run python -m scripts.scanner.run_layer1 --universe sp1500 --mode dual
"""

import argparse
import logging

from scripts.scanner.config import DEFAULT_THRESHOLDS, DEFAULT_SECTOR_THRESHOLDS
from scripts.scanner.data_fetcher import fetch_batch_metrics
from scripts.scanner.screener import screen_batch
from scripts.scanner.sector_screener import screen_batch_dual_track
from scripts.scanner.results_store import save_screening_results
from scripts.scanner.universe import (
    get_sp500_tickers,
    get_sp400_tickers,
    get_sp600_tickers,
    get_sp1500_tickers,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _progress(current: int, total: int):
    pct = current / total * 100
    print(f"\r  Fetching: {current}/{total} ({pct:.0f}%)", end="", flush=True)
    if current == total:
        print()


def _print_absolute_results(results):
    """印出絕對門檻模式的篩選結果。"""
    passed = [r for r in results if r.passed]

    if passed:
        print("\n=== PASSED SCREENING (Absolute Mode) ===")
        for r in passed:
            mos = (
                f"MOS: {r.margin_of_safety_pct:.1f}%"
                if r.margin_of_safety_pct
                else "MOS: N/A"
            )
            graham = (
                f"Graham: ${r.graham_number:.2f}" if r.graham_number else "Graham: N/A"
            )
            pe = f"{r.metrics.trailing_pe:>6.1f}" if r.metrics.trailing_pe else "  N/A"
            peg = f"{r.metrics.peg_ratio:>5.2f}" if r.metrics.peg_ratio else "  N/A"
            print(
                f"  {r.symbol:8s} | PE={pe} | PEG={peg} | "
                f"ROE={r.metrics.roe:.1%} | D/E={r.metrics.debt_to_equity:.2f} | "
                f"{graham} | {mos}"
            )
    else:
        print("\nNo tickers passed all screening criteria.")


def _print_dual_results(results):
    """印出雙軌制模式的篩選結果，含產業分布和百分位資訊。"""
    passed = [r for r in results if r.passed]

    if passed:
        print("\n=== PASSED SCREENING (Dual-Track Mode) ===")
        for r in passed:
            mos = (
                f"MOS: {r.margin_of_safety_pct:.1f}%"
                if r.margin_of_safety_pct
                else "MOS: N/A"
            )
            graham = (
                f"Graham: ${r.graham_number:.2f}" if r.graham_number else "Graham: N/A"
            )
            # 指標值 + 百分位
            pe_str = "  N/A"
            if r.metrics.trailing_pe is not None:
                pe_pct = ""
                if r.sector_percentiles and r.sector_percentiles.pe_percentile is not None:
                    pe_pct = f" (p{r.sector_percentiles.pe_percentile:.0%})"
                pe_str = f"{r.metrics.trailing_pe:>6.1f}{pe_pct}"

            peg_str = "  N/A"
            if r.metrics.peg_ratio is not None:
                peg_pct = ""
                if r.sector_percentiles and r.sector_percentiles.peg_percentile is not None:
                    peg_pct = f" (p{r.sector_percentiles.peg_percentile:.0%})"
                peg_str = f"{r.metrics.peg_ratio:>5.2f}{peg_pct}"

            sector = r.metrics.sector or "Unknown"
            print(
                f"  {r.symbol:8s} | {sector:25s} | PE={pe_str} | PEG={peg_str} | "
                f"ROE={r.metrics.roe:.1%} | D/E={r.metrics.debt_to_equity:.2f} | "
                f"{graham} | {mos}"
            )

        # 產業分布摘要
        print("\n=== 產業分布 ===")
        # 收集所有有效結果的產業分布
        all_valid = [r for r in results if r.metrics and r.metrics.sector]
        sector_stats: dict[str, dict] = {}
        for r in all_valid:
            sector = r.metrics.sector
            if sector not in sector_stats:
                sector_stats[sector] = {"screened": 0, "passed": 0}
            sector_stats[sector]["screened"] += 1
            if r.passed:
                sector_stats[sector]["passed"] += 1

        for sector in sorted(sector_stats.keys()):
            s = sector_stats[sector]
            print(f"  {sector:30s}: {s['passed']:>3d} 通過 / {s['screened']:>4d} 篩選")
    else:
        print("\nNo tickers passed dual-track screening criteria.")


def main():
    parser = argparse.ArgumentParser(description="Layer 1 Quantitative Screener")
    parser.add_argument(
        "--tickers", nargs="+", help="Specific tickers to screen"
    )
    parser.add_argument(
        "--universe",
        choices=["sp500", "sp400", "sp600", "sp1500"],
        default=None,
        help="Predefined universe to screen (sp1500 = sp500+sp400+sp600)",
    )
    parser.add_argument(
        "--mode",
        choices=["absolute", "dual"],
        default="dual",
        help="Screening mode: absolute (legacy) or dual (sector-relative + safety)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between API calls in seconds (default: 0.1)",
    )
    args = parser.parse_args()

    # 取得股票代碼清單
    _universe_map = {
        "sp500": get_sp500_tickers,
        "sp400": get_sp400_tickers,
        "sp600": get_sp600_tickers,
        "sp1500": get_sp1500_tickers,
    }

    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif args.universe in _universe_map:
        tickers = _universe_map[args.universe]()
    else:
        parser.error("Specify --tickers or --universe")
        return

    if args.mode == "absolute":
        logger.info(
            "Screening %d tickers (absolute mode): %s",
            len(tickers), DEFAULT_THRESHOLDS,
        )
    else:
        logger.info(
            "Screening %d tickers (dual-track mode): %s",
            len(tickers), DEFAULT_SECTOR_THRESHOLDS,
        )

    logger.info("Phase 1/2: Fetching financial data...")
    metrics_list = fetch_batch_metrics(
        tickers, delay_between=args.delay, progress_callback=_progress
    )

    fetch_errors = sum(1 for m in metrics_list if m.fetch_error)
    logger.info("Fetched %d tickers (%d errors)", len(metrics_list), fetch_errors)

    logger.info("Phase 2/2: Applying quantitative filters...")
    if args.mode == "absolute":
        results = screen_batch(metrics_list)
    else:
        results = screen_batch_dual_track(metrics_list)

    passed = [r for r in results if r.passed]
    logger.info("Results: %d/%d passed screening", len(passed), len(results))

    tag = "layer1" if args.mode == "absolute" else "layer1_dual"
    filepath = save_screening_results(results, tag=tag)
    logger.info("Results saved to: %s", filepath)

    if args.mode == "absolute":
        _print_absolute_results(results)
    else:
        _print_dual_results(results)


if __name__ == "__main__":
    main()
