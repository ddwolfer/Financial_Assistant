"""
Screening configuration for Layer 1 quantitative filters.

All thresholds are configurable. Modify DEFAULT_THRESHOLDS to adjust
screening sensitivity, or pass custom thresholds to the screener.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class ScreeningThresholds:
    """Configurable thresholds for Layer 1 quantitative screening."""

    pe_ratio_max: float = 15.0
    peg_ratio_max: float = 1.0
    roe_min: float = 0.15
    debt_to_equity_max: float = 0.5
    graham_multiplier: float = 22.5


DEFAULT_THRESHOLDS = ScreeningThresholds()


def calculate_graham_number(
    eps: float,
    book_value_per_share: float,
    multiplier: float = 22.5,
) -> Optional[float]:
    """
    Calculate the Graham Number for safety margin assessment.

    Formula: sqrt(multiplier * EPS * Book Value per Share)

    Returns None if inputs are negative or zero.
    """
    if eps <= 0 or book_value_per_share <= 0:
        return None
    return math.sqrt(multiplier * eps * book_value_per_share)
