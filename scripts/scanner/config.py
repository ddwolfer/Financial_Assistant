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


@dataclass(frozen=True)
class SectorRelativeThresholds:
    """
    雙軌制篩選設定：產業內百分位排名 + 寬鬆安全底線。

    Track 1（主要）：每個指標在同 GICS 產業內的百分位排名，
    排名在前 sector_percentile_threshold（預設前 30%）的股票才通過。

    Track 2（安全底線）：寬鬆的絕對門檻，排除明顯不健康的極端值。
    與 Track 1 同時滿足才算通過。
    """

    # Track 1：產業內百分位門檻（0.30 = 前 30%）
    sector_percentile_threshold: float = 0.30
    # 產業內股票數低於此值則跳過百分位計算，僅用安全底線
    min_sector_size: int = 5

    # Track 2：寬鬆安全底線（排除極端值）
    safety_pe_max: float = 50.0
    safety_peg_max: float = 3.0
    safety_roe_min: float = 0.05      # 5%
    safety_de_max: float = 2.0

    # 共用
    graham_multiplier: float = 22.5


DEFAULT_SECTOR_THRESHOLDS = SectorRelativeThresholds()


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
