"""Tests for screening configuration and Graham Number formula."""

import math

import pytest

from scripts.scanner.config import (
    ScreeningThresholds,
    DEFAULT_THRESHOLDS,
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
