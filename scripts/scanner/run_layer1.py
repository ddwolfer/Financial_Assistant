"""
CLI entry point for Layer 1 quantitative screening.

Usage:
    uv run python -m scripts.scanner.run_layer1
    uv run python -m scripts.scanner.run_layer1 --tickers AAPL MSFT GOOGL
    uv run python -m scripts.scanner.run_layer1 --universe sp500
"""

import argparse
import logging
import sys

from scripts.scanner.config import DEFAULT_THRESHOLDS
from scripts.scanner.data_fetcher import fetch_batch_metrics
from scripts.scanner.screener import screen_batch
from scripts.scanner.results_store import save_screening_results
from scripts.scanner.universe import get_sp500_tickers

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


def main():
    parser = argparse.ArgumentParser(description="Layer 1 Quantitative Screener")
    parser.add_argument(
        "--tickers", nargs="+", help="Specific tickers to screen"
    )
    parser.add_argument(
        "--universe",
        choices=["sp500"],
        default=None,
        help="Predefined universe to screen",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between API calls in seconds (default: 0.1)",
    )
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif args.universe == "sp500":
        tickers = get_sp500_tickers()
    else:
        parser.error("Specify --tickers or --universe")
        return

    logger.info(
        "Screening %d tickers with thresholds: %s", len(tickers), DEFAULT_THRESHOLDS
    )

    logger.info("Phase 1/2: Fetching financial data...")
    metrics_list = fetch_batch_metrics(
        tickers, delay_between=args.delay, progress_callback=_progress
    )

    fetch_errors = sum(1 for m in metrics_list if m.fetch_error)
    logger.info("Fetched %d tickers (%d errors)", len(metrics_list), fetch_errors)

    logger.info("Phase 2/2: Applying quantitative filters...")
    results = screen_batch(metrics_list)

    passed = [r for r in results if r.passed]
    logger.info("Results: %d/%d passed screening", len(passed), len(results))

    filepath = save_screening_results(results)
    logger.info("Results saved to: %s", filepath)

    if passed:
        print("\n=== PASSED SCREENING ===")
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


if __name__ == "__main__":
    main()
