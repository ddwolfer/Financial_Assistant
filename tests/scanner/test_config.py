"""Tests for screening configuration and Graham Number formula."""

import math

import pytest

from scripts.scanner.config import (
    ScreeningThresholds,
    DEFAULT_THRESHOLDS,
    SectorRelativeThresholds,
    DEFAULT_SECTOR_THRESHOLDS,
    CacheConfig,
    DEFAULT_CACHE_CONFIG,
    calculate_graham_number,
)


class TestGrahamNumber:
    def test_basic(self):
        # sqrt(22.5 * 5 * 30) = sqrt(3375) ≈ 58.09
        assert calculate_graham_number(5.0, 30.0) == pytest.approx(
            math.sqrt(22.5 * 5 * 30)
        )

    def test_negative_eps(self):
        assert calculate_graham_number(-2.0, 30.0) is None

    def test_zero_bvps(self):
        assert calculate_graham_number(5.0, 0.0) is None

    def test_custom_multiplier(self):
        assert calculate_graham_number(5.0, 30.0, multiplier=15.0) == pytest.approx(
            math.sqrt(15.0 * 5 * 30)
        )


def test_default_thresholds():
    t = DEFAULT_THRESHOLDS
    assert t.pe_ratio_max == 15.0
    assert t.peg_ratio_max == 1.0
    assert t.roe_min == 0.15
    assert t.debt_to_equity_max == 0.5


# === 雙軌制設定測試 ===


def test_default_sector_thresholds():
    """驗證雙軌制設定的預設值。"""
    t = DEFAULT_SECTOR_THRESHOLDS
    # Track 1：產業百分位
    assert t.sector_percentile_threshold == 0.30
    assert t.min_sector_size == 5
    # Track 2：安全底線
    assert t.safety_pe_max == 50.0
    assert t.safety_peg_max == 3.0
    assert t.safety_roe_min == 0.05
    assert t.safety_de_max == 2.0
    # 共用
    assert t.graham_multiplier == 22.5


def test_sector_thresholds_frozen():
    """驗證 SectorRelativeThresholds 為不可變 dataclass。"""
    t = DEFAULT_SECTOR_THRESHOLDS
    with pytest.raises(AttributeError):
        t.sector_percentile_threshold = 0.50


def test_custom_sector_thresholds():
    """驗證可以建立自訂的雙軌制設定。"""
    t = SectorRelativeThresholds(
        sector_percentile_threshold=0.20,
        min_sector_size=10,
        safety_pe_max=30.0,
    )
    assert t.sector_percentile_threshold == 0.20
    assert t.min_sector_size == 10
    assert t.safety_pe_max == 30.0
    # 未指定的欄位保持預設值
    assert t.safety_roe_min == 0.05


# === 快取設定測試 ===


def test_default_cache_config():
    """驗證快取設定的預設值。"""
    c = DEFAULT_CACHE_CONFIG
    assert c.ttl_seconds == 86400          # 24 小時
    assert c.error_ttl_seconds == 3600     # 1 小時
    assert c.cache_filename == "metrics_cache.json"


def test_cache_config_frozen():
    """驗證 CacheConfig 為不可變 dataclass。"""
    c = DEFAULT_CACHE_CONFIG
    with pytest.raises(AttributeError):
        c.ttl_seconds = 999
