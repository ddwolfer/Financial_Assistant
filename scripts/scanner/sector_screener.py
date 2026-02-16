"""
雙軌制產業相對篩選引擎。

Track 1（主要）：產業內百分位排名篩選——每個指標在同 GICS 產業中
排名前 X%（預設 30%）的股票才通過，確保各產業都有機會被選出。

Track 2（安全底線）：寬鬆的絕對門檻，排除明顯不健康的極端值公司。

兩個 track 同時通過才算最終通過。
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from scripts.scanner.config import (
    SectorRelativeThresholds,
    DEFAULT_SECTOR_THRESHOLDS,
    calculate_graham_number,
)
from scripts.scanner.data_fetcher import TickerMetrics

logger = logging.getLogger(__name__)


# ── 資料結構 ──────────────────────────────────────────


@dataclass
class SectorPercentiles:
    """個股在產業內的百分位排名（0.0=最佳, 1.0=最差）。"""

    pe_percentile: Optional[float] = None
    peg_percentile: Optional[float] = None
    roe_percentile: Optional[float] = None
    de_percentile: Optional[float] = None
    sector: str = ""
    sector_count: int = 0


@dataclass
class SectorScreeningResult:
    """雙軌制篩選結果。"""

    symbol: str
    passed: bool
    screening_mode: str  # "dual_track" | "safety_only"

    # Track 1 結果
    sector_percentiles: Optional[SectorPercentiles] = None
    passed_sector_filter: bool = False

    # Track 2 結果
    passed_safety_filter: bool = False
    safety_fail_reasons: list[str] = field(default_factory=list)

    # 葛拉漢數
    graham_number: Optional[float] = None
    current_price: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None

    # 原始指標
    metrics: Optional[TickerMetrics] = None
    fail_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """序列化為 JSON 格式。"""
        return {
            "symbol": self.symbol,
            "passed": self.passed,
            "screening_mode": self.screening_mode,
            "graham_number": self.graham_number,
            "current_price": self.current_price,
            "margin_of_safety_pct": self.margin_of_safety_pct,
            "fail_reasons": self.fail_reasons,
            "sector_percentiles": {
                "pe_percentile": self.sector_percentiles.pe_percentile,
                "peg_percentile": self.sector_percentiles.peg_percentile,
                "roe_percentile": self.sector_percentiles.roe_percentile,
                "de_percentile": self.sector_percentiles.de_percentile,
                "sector": self.sector_percentiles.sector,
                "sector_count": self.sector_percentiles.sector_count,
            }
            if self.sector_percentiles
            else None,
            "passed_sector_filter": self.passed_sector_filter,
            "passed_safety_filter": self.passed_safety_filter,
            "safety_fail_reasons": self.safety_fail_reasons,
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


# ── 內部工具函數 ──────────────────────────────────────


def _compute_metric_rank(
    value: float,
    all_values: list[float],
    lower_is_better: bool,
) -> float:
    """
    計算正規化排名：0.0（最佳）到 1.0（最差）。

    公式：better_count / (N - 1)
    - lower_is_better=True：比目標值嚴格更低的數量
    - lower_is_better=False：比目標值嚴格更高的數量
    - Ties 得到相同排名
    - 單一元素回傳 0.0
    """
    n = len(all_values)
    if n <= 1:
        return 0.0
    if lower_is_better:
        better_count = sum(1 for v in all_values if v < value)
    else:
        better_count = sum(1 for v in all_values if v > value)
    return better_count / (n - 1)


def _group_by_sector(
    metrics_list: list[TickerMetrics],
) -> dict[str, list[TickerMetrics]]:
    """按 GICS 產業分組，sector=None 歸入 'Unknown'。"""
    groups: dict[str, list[TickerMetrics]] = {}
    for m in metrics_list:
        sector = m.sector or "Unknown"
        groups.setdefault(sector, []).append(m)
    return groups


def _calculate_sector_percentiles(
    metrics: TickerMetrics,
    sector_group: list[TickerMetrics],
) -> SectorPercentiles:
    """計算個股在產業內各指標的百分位排名。"""
    sector = metrics.sector or "Unknown"
    sector_count = len(sector_group)

    # 收集每個指標的有效值（排除 None）
    pe_values = [m.trailing_pe for m in sector_group if m.trailing_pe is not None]
    peg_values = [m.peg_ratio for m in sector_group if m.peg_ratio is not None]
    roe_values = [m.roe for m in sector_group if m.roe is not None]
    de_values = [m.debt_to_equity for m in sector_group if m.debt_to_equity is not None]

    # 計算百分位（若目標值為 None 則該百分位也是 None）
    pe_pct = None
    if metrics.trailing_pe is not None and len(pe_values) > 1:
        pe_pct = _compute_metric_rank(metrics.trailing_pe, pe_values, lower_is_better=True)

    peg_pct = None
    if metrics.peg_ratio is not None and len(peg_values) > 1:
        peg_pct = _compute_metric_rank(metrics.peg_ratio, peg_values, lower_is_better=True)

    roe_pct = None
    if metrics.roe is not None and len(roe_values) > 1:
        roe_pct = _compute_metric_rank(metrics.roe, roe_values, lower_is_better=False)

    de_pct = None
    if metrics.debt_to_equity is not None and len(de_values) > 1:
        de_pct = _compute_metric_rank(metrics.debt_to_equity, de_values, lower_is_better=True)

    return SectorPercentiles(
        pe_percentile=pe_pct,
        peg_percentile=peg_pct,
        roe_percentile=roe_pct,
        de_percentile=de_pct,
        sector=sector,
        sector_count=sector_count,
    )


def _apply_safety_filter(
    metrics: TickerMetrics,
    thresholds: SectorRelativeThresholds = DEFAULT_SECTOR_THRESHOLDS,
) -> tuple[bool, list[str]]:
    """
    寬鬆安全底線篩選（Track 2）。

    只過濾明顯極端的數值，缺失資料不導致失敗。
    """
    fail_reasons: list[str] = []

    # P/E 安全上限
    if metrics.trailing_pe is not None:
        if metrics.trailing_pe >= thresholds.safety_pe_max:
            fail_reasons.append(
                f"P/E {metrics.trailing_pe:.1f} >= 安全上限 {thresholds.safety_pe_max}"
            )

    # PEG 安全上限
    if metrics.peg_ratio is not None:
        if metrics.peg_ratio >= thresholds.safety_peg_max:
            fail_reasons.append(
                f"PEG {metrics.peg_ratio:.2f} >= 安全上限 {thresholds.safety_peg_max}"
            )

    # ROE 安全下限
    if metrics.roe is not None:
        if metrics.roe < thresholds.safety_roe_min:
            fail_reasons.append(
                f"ROE {metrics.roe:.2%} < 安全下限 {thresholds.safety_roe_min:.0%}"
            )

    # D/E 安全上限
    if metrics.debt_to_equity is not None:
        if metrics.debt_to_equity > thresholds.safety_de_max:
            fail_reasons.append(
                f"D/E {metrics.debt_to_equity:.2f} > 安全上限 {thresholds.safety_de_max}"
            )

    return len(fail_reasons) == 0, fail_reasons


# ── 主要入口函數 ──────────────────────────────────────


def screen_batch_dual_track(
    metrics_list: list[TickerMetrics],
    thresholds: SectorRelativeThresholds = DEFAULT_SECTOR_THRESHOLDS,
) -> list[SectorScreeningResult]:
    """
    雙軌制批次篩選：產業內百分位排名 + 安全底線。

    流程：
    1. 按產業分組
    2. 對每支股票計算產業內百分位
    3. 同時執行 Track 1（百分位）和 Track 2（安全底線）
    4. 兩者都通過才算最終通過
    5. 產業 < min_sector_size → 僅用安全底線

    排序：通過的按安全邊際降序，失敗的排後面。
    """
    # 過濾掉抓取失敗的股票
    valid_metrics = [m for m in metrics_list if m.is_valid]
    invalid_metrics = [m for m in metrics_list if not m.is_valid]

    # 按產業分組
    sector_groups = _group_by_sector(valid_metrics)
    results: list[SectorScreeningResult] = []

    for sector, group in sector_groups.items():
        use_sector_filter = len(group) >= thresholds.min_sector_size

        for metrics in group:
            # Track 2：安全底線
            safety_passed, safety_reasons = _apply_safety_filter(metrics, thresholds)

            # Track 1：產業百分位
            percentiles = _calculate_sector_percentiles(metrics, group)
            sector_passed = False

            if use_sector_filter:
                screening_mode = "dual_track"
                # 所有非 None 百分位都必須 <= 門檻才算通過
                pct_checks = []
                if percentiles.pe_percentile is not None:
                    pct_checks.append(
                        percentiles.pe_percentile <= thresholds.sector_percentile_threshold
                    )
                if percentiles.peg_percentile is not None:
                    pct_checks.append(
                        percentiles.peg_percentile <= thresholds.sector_percentile_threshold
                    )
                if percentiles.roe_percentile is not None:
                    pct_checks.append(
                        percentiles.roe_percentile <= thresholds.sector_percentile_threshold
                    )
                if percentiles.de_percentile is not None:
                    pct_checks.append(
                        percentiles.de_percentile <= thresholds.sector_percentile_threshold
                    )

                # 至少要有 1 個指標有百分位，且全部通過
                sector_passed = len(pct_checks) > 0 and all(pct_checks)
            else:
                # 產業太小，跳過百分位篩選
                screening_mode = "safety_only"
                sector_passed = True  # 不使用 sector filter，視為通過

            # 最終判定：兩個 track 都通過
            passed = safety_passed and sector_passed

            # 收集失敗原因
            fail_reasons: list[str] = []
            if not sector_passed and use_sector_filter:
                fail_reasons.append("未通過產業內百分位排名篩選")
            if not safety_passed:
                fail_reasons.extend(safety_reasons)

            # 計算葛拉漢數
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

            results.append(
                SectorScreeningResult(
                    symbol=metrics.symbol,
                    passed=passed,
                    screening_mode=screening_mode,
                    sector_percentiles=percentiles,
                    passed_sector_filter=sector_passed,
                    passed_safety_filter=safety_passed,
                    safety_fail_reasons=safety_reasons,
                    graham_number=graham,
                    current_price=metrics.current_price,
                    margin_of_safety_pct=mos_pct,
                    metrics=metrics,
                    fail_reasons=fail_reasons,
                )
            )

    # 處理抓取失敗的股票
    for m in invalid_metrics:
        results.append(
            SectorScreeningResult(
                symbol=m.symbol,
                passed=False,
                screening_mode="error",
                metrics=m,
                fail_reasons=[f"資料抓取失敗: {m.fetch_error}"],
            )
        )

    # 排序：通過的按安全邊際降序排前面，失敗的排後面
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    passed.sort(key=lambda r: r.margin_of_safety_pct or -999, reverse=True)

    return passed + failed
