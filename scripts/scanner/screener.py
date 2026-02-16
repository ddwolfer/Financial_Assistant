"""
Layer 1: Quantitative Hard Filter.

Screens stocks against configurable financial thresholds:
- P/E Ratio below maximum
- PEG Ratio below maximum
- ROE above minimum AND Debt/Equity below maximum
- Graham Number for safety margin assessment (informational only)
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from scripts.scanner.config import (
    ScreeningThresholds,
    DEFAULT_THRESHOLDS,
    calculate_graham_number,
)
from scripts.scanner.data_fetcher import TickerMetrics

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    """Result of screening a single ticker."""

    symbol: str
    passed: bool
    graham_number: Optional[float] = None
    current_price: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    metrics: Optional[TickerMetrics] = None
    fail_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        return {
            "symbol": self.symbol,
            "passed": self.passed,
            "graham_number": self.graham_number,
            "current_price": self.current_price,
            "margin_of_safety_pct": self.margin_of_safety_pct,
            "fail_reasons": self.fail_reasons,
            "metrics": {
                "trailing_pe": self.metrics.trailing_pe,
                "peg_ratio": self.metrics.peg_ratio,
                "roe": self.metrics.roe,
                "debt_to_equity": self.metrics.debt_to_equity,
                "trailing_eps": self.metrics.trailing_eps,
                "book_value": self.metrics.book_value,
                "sector": self.metrics.sector,
                "industry": self.metrics.industry,
                "company_name": self.metrics.company_name,
            }
            if self.metrics
            else None,
        }


def screen_ticker(
    metrics: TickerMetrics,
    thresholds: ScreeningThresholds = DEFAULT_THRESHOLDS,
) -> ScreeningResult:
    """
    Apply Layer 1 quantitative filters to a single ticker.

    A ticker passes if ALL filters pass. Missing data causes failure
    (conservative approach).
    """
    if not metrics.is_valid:
        return ScreeningResult(
            symbol=metrics.symbol,
            passed=False,
            fail_reasons=[f"Invalid data: {metrics.fetch_error}"],
            metrics=metrics,
        )

    fail_reasons = []

    # Filter 1: P/E Ratio
    if metrics.trailing_pe is not None:
        if metrics.trailing_pe >= thresholds.pe_ratio_max:
            fail_reasons.append(
                f"P/E {metrics.trailing_pe:.1f} >= {thresholds.pe_ratio_max}"
            )
    else:
        fail_reasons.append("P/E ratio unavailable")

    # Filter 2: PEG Ratio
    if metrics.peg_ratio is not None:
        if metrics.peg_ratio >= thresholds.peg_ratio_max:
            fail_reasons.append(
                f"PEG {metrics.peg_ratio:.2f} >= {thresholds.peg_ratio_max}"
            )
    else:
        fail_reasons.append("PEG ratio unavailable")

    # Filter 3: ROE
    if metrics.roe is not None:
        if metrics.roe < thresholds.roe_min:
            fail_reasons.append(
                f"ROE {metrics.roe:.2%} < {thresholds.roe_min:.0%}"
            )
    else:
        fail_reasons.append("ROE unavailable")

    # Filter 4: Debt/Equity
    if metrics.debt_to_equity is not None:
        if metrics.debt_to_equity > thresholds.debt_to_equity_max:
            fail_reasons.append(
                f"D/E {metrics.debt_to_equity:.2f} > {thresholds.debt_to_equity_max}"
            )
    else:
        fail_reasons.append("Debt/Equity unavailable")

    # Graham Number (informational, not a filter)
    graham = None
    mos_pct = None
    if metrics.trailing_eps and metrics.book_value:
        graham = calculate_graham_number(
            metrics.trailing_eps,
            metrics.book_value,
            thresholds.graham_multiplier,
        )
        if graham and metrics.current_price:
            mos_pct = (graham - metrics.current_price) / graham * 100

    passed = len(fail_reasons) == 0

    return ScreeningResult(
        symbol=metrics.symbol,
        passed=passed,
        graham_number=graham,
        current_price=metrics.current_price,
        margin_of_safety_pct=mos_pct,
        metrics=metrics,
        fail_reasons=fail_reasons,
    )


def screen_batch(
    metrics_list: list[TickerMetrics],
    thresholds: ScreeningThresholds = DEFAULT_THRESHOLDS,
) -> list[ScreeningResult]:
    """
    Screen a batch of tickers. Returns all results sorted:
    passed first (by margin of safety desc), then failed.
    """
    results = [screen_ticker(m, thresholds) for m in metrics_list]

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    passed.sort(
        key=lambda r: r.margin_of_safety_pct or -999,
        reverse=True,
    )

    return passed + failed
