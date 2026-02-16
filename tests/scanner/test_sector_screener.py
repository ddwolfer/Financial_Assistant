"""Tests for dual-track sector-relative screening engine."""

import pytest
from scripts.scanner.data_fetcher import TickerMetrics
from scripts.scanner.config import SectorRelativeThresholds
from scripts.scanner.sector_screener import (
    _compute_metric_rank,
    _group_by_sector,
    _apply_safety_filter,
    screen_batch_dual_track,
)


def _make_metrics(
    symbol: str = "TEST",
    trailing_pe: float | None = 10.0,
    peg_ratio: float | None = 0.8,
    roe: float | None = 0.20,
    debt_to_equity: float | None = 0.3,
    trailing_eps: float | None = 5.0,
    book_value: float | None = 30.0,
    current_price: float | None = 100.0,
    sector: str | None = "Technology",
    **kwargs,
) -> TickerMetrics:
    """建立測試用的 TickerMetrics，預設值全部通過安全底線。"""
    return TickerMetrics(
        symbol=symbol,
        trailing_pe=trailing_pe,
        peg_ratio=peg_ratio,
        roe=roe,
        debt_to_equity=debt_to_equity,
        trailing_eps=trailing_eps,
        book_value=book_value,
        current_price=current_price,
        sector=sector,
        **kwargs,
    )


# === 百分位排名單元測試 ===


class TestComputeMetricRank:
    def test_rank_lower_is_better(self):
        """最低值排名 0.0（最佳），最高值排名 1.0（最差）。"""
        values = [5.0, 10.0, 15.0, 20.0]
        assert _compute_metric_rank(5.0, values, lower_is_better=True) == 0.0
        assert _compute_metric_rank(20.0, values, lower_is_better=True) == 1.0
        # 10.0: 只有 5.0 嚴格更低 → rank = 1/3 ≈ 0.333
        assert _compute_metric_rank(10.0, values, lower_is_better=True) == pytest.approx(1 / 3)

    def test_rank_higher_is_better(self):
        """ROE 越高越好：最高值排名 0.0（最佳）。"""
        values = [0.05, 0.10, 0.15, 0.20]
        assert _compute_metric_rank(0.20, values, lower_is_better=False) == 0.0
        assert _compute_metric_rank(0.05, values, lower_is_better=False) == 1.0

    def test_rank_with_ties(self):
        """相同值的股票得到相同排名。"""
        values = [10.0, 10.0, 10.0, 20.0]
        # 10.0: 沒有人嚴格更低 → rank 0.0
        assert _compute_metric_rank(10.0, values, lower_is_better=True) == 0.0
        # 20.0: 3 個嚴格更低 → rank = 3/3 = 1.0
        assert _compute_metric_rank(20.0, values, lower_is_better=True) == 1.0

    def test_rank_single_element(self):
        """只有 1 支股票時排名為 0.0。"""
        assert _compute_metric_rank(10.0, [10.0], lower_is_better=True) == 0.0


# === 產業分組測試 ===


class TestGroupBySector:
    def test_group_by_sector(self):
        """按產業正確分組。"""
        metrics_list = [
            _make_metrics("A", sector="Technology"),
            _make_metrics("B", sector="Technology"),
            _make_metrics("C", sector="Technology"),
            _make_metrics("D", sector="Financials"),
            _make_metrics("E", sector="Financials"),
        ]
        groups = _group_by_sector(metrics_list)
        assert len(groups) == 2
        assert len(groups["Technology"]) == 3
        assert len(groups["Financials"]) == 2

    def test_group_none_sector(self):
        """sector=None 歸入 'Unknown' 群組。"""
        metrics_list = [
            _make_metrics("A", sector=None),
            _make_metrics("B", sector="Technology"),
        ]
        groups = _group_by_sector(metrics_list)
        assert "Unknown" in groups
        assert len(groups["Unknown"]) == 1


# === 安全底線測試 ===


class TestSafetyFilter:
    def test_safety_passes_normal(self):
        """正常範圍內的指標通過安全底線。"""
        m = _make_metrics(trailing_pe=25.0, roe=0.10, debt_to_equity=1.5, peg_ratio=2.0)
        passed, reasons = _apply_safety_filter(m)
        assert passed is True
        assert len(reasons) == 0

    def test_safety_fails_extreme_pe(self):
        """P/E 超過安全上限 → 失敗。"""
        m = _make_metrics(trailing_pe=60.0)
        passed, reasons = _apply_safety_filter(m)
        assert passed is False
        assert any("P/E" in r for r in reasons)

    def test_safety_missing_data_passes(self):
        """缺失資料不導致安全底線失敗（只過濾極端值）。"""
        m = _make_metrics(trailing_pe=None, peg_ratio=None, roe=None, debt_to_equity=None)
        passed, reasons = _apply_safety_filter(m)
        assert passed is True
        assert len(reasons) == 0


# === 雙軌整合測試 ===


class TestDualTrackIntegration:
    def _make_sector_batch(self, count: int, sector: str, pe_start: float) -> list[TickerMetrics]:
        """建立同一產業的一批股票，P/E 從 pe_start 遞增。"""
        return [
            _make_metrics(
                symbol=f"{sector[:3].upper()}{i}",
                trailing_pe=pe_start + i * 2,
                peg_ratio=0.5 + i * 0.1,
                roe=0.30 - i * 0.02,
                debt_to_equity=0.1 + i * 0.05,
                sector=sector,
                current_price=50.0 + i * 5,
            )
            for i in range(count)
        ]

    def test_dual_passes_both_tracks(self):
        """產業前 30% + 安全底線 → 通過。"""
        # 建立 10 支科技股，最低 PE 的那幾支應通過
        batch = self._make_sector_batch(10, "Technology", pe_start=8.0)
        results = screen_batch_dual_track(batch)
        passed = [r for r in results if r.passed]
        # 前 30% = 3 支（index 0, 1, 2 的 PE 最低）
        assert len(passed) >= 1
        # 通過的都應該同時通過兩個 track
        for r in passed:
            assert r.passed_sector_filter is True
            assert r.passed_safety_filter is True
            assert r.screening_mode == "dual_track"

    def test_dual_fails_sector_filter(self):
        """不在產業前 30% → 失敗。"""
        batch = self._make_sector_batch(10, "Technology", pe_start=8.0)
        results = screen_batch_dual_track(batch)
        # 最後幾支（PE 最高）應失敗
        failed = [r for r in results if not r.passed]
        assert len(failed) >= 1

    def test_dual_fails_safety_filter(self):
        """在前 30% 但超過安全底線 → 失敗。"""
        # 建立一批股票，其中 PE 最低的那支 ROE 極低（低於安全底線 5%）
        batch = self._make_sector_batch(10, "Technology", pe_start=8.0)
        # 把 index 0（PE 最低）的 ROE 設成 0.02（低於安全底線 0.05）
        bad = _make_metrics(
            symbol="BAD0",
            trailing_pe=5.0,  # 最低 PE → 百分位應排最好
            peg_ratio=0.3,
            roe=0.02,  # 低於安全底線 0.05
            debt_to_equity=0.1,
            sector="Technology",
            current_price=50.0,
        )
        batch.append(bad)
        results = screen_batch_dual_track(batch)
        bad_result = next(r for r in results if r.symbol == "BAD0")
        assert bad_result.passed is False
        assert bad_result.passed_safety_filter is False

    def test_small_sector_fallback(self):
        """產業 < min_sector_size 時僅用安全底線篩選。"""
        # 建立只有 3 支的小產業
        batch = self._make_sector_batch(3, "RealEstate", pe_start=8.0)
        thresholds = SectorRelativeThresholds(min_sector_size=5)
        results = screen_batch_dual_track(batch, thresholds)
        for r in results:
            assert r.screening_mode == "safety_only"


# === 批次處理測試 ===


class TestBatchDualTrack:
    def _make_diverse_batch(self) -> list[TickerMetrics]:
        """建立包含多產業的測試批次。"""
        tech = [
            _make_metrics(f"TECH{i}", trailing_pe=10 + i * 3, peg_ratio=0.5 + i * 0.15,
                          roe=0.30 - i * 0.02, debt_to_equity=0.1 + i * 0.05,
                          sector="Technology", current_price=100 + i * 10)
            for i in range(10)
        ]
        fin = [
            _make_metrics(f"FIN{i}", trailing_pe=6 + i * 2, peg_ratio=0.4 + i * 0.1,
                          roe=0.25 - i * 0.015, debt_to_equity=0.15 + i * 0.04,
                          sector="Financials", current_price=80 + i * 8)
            for i in range(10)
        ]
        return tech + fin

    def test_batch_sector_distribution(self):
        """兩個產業都應有通過的股票。"""
        batch = self._make_diverse_batch()
        results = screen_batch_dual_track(batch)
        passed = [r for r in results if r.passed]
        passed_sectors = {r.metrics.sector for r in passed}
        assert "Technology" in passed_sectors
        assert "Financials" in passed_sectors

    def test_batch_sorting(self):
        """通過的排前面（MOS 降序），失敗的排後面。"""
        batch = self._make_diverse_batch()
        results = screen_batch_dual_track(batch)
        passed_indices = [i for i, r in enumerate(results) if r.passed]
        failed_indices = [i for i, r in enumerate(results) if not r.passed]
        if passed_indices and failed_indices:
            assert max(passed_indices) < min(failed_indices)

    def test_batch_serialization(self):
        """to_dict() 包含所有新欄位。"""
        batch = self._make_diverse_batch()
        results = screen_batch_dual_track(batch)
        passed = [r for r in results if r.passed]
        assert len(passed) > 0
        d = passed[0].to_dict()
        # 驗證新欄位存在
        assert "screening_mode" in d
        assert "sector_percentiles" in d
        assert "passed_sector_filter" in d
        assert "passed_safety_filter" in d
        # 驗證百分位資訊
        sp = d["sector_percentiles"]
        assert "pe_percentile" in sp
        assert "peg_percentile" in sp
        assert "roe_percentile" in sp
        assert "de_percentile" in sp
        assert "sector" in sp
        assert "sector_count" in sp
