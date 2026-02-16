"""MetricsCache 快取管理器測試。"""

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from scripts.scanner.config import CacheConfig
from scripts.scanner.data_fetcher import TickerMetrics
from scripts.scanner.metrics_cache import MetricsCache


def _make_metrics(symbol="TEST", **kwargs):
    """建立測試用的 TickerMetrics。"""
    defaults = {
        "trailing_pe": 12.5,
        "roe": 0.25,
        "debt_to_equity": 0.45,
        "trailing_eps": 5.0,
        "book_value": 30.0,
        "current_price": 100.0,
        "sector": "Technology",
    }
    defaults.update(kwargs)
    return TickerMetrics(symbol=symbol, **defaults)


def test_cache_put_and_get(tmp_path):
    """put 後 get 回傳正確的 TickerMetrics。"""
    cache = MetricsCache(cache_dir=tmp_path)
    cache.load()

    metrics = _make_metrics("AAPL", trailing_pe=28.5)
    cache.put(metrics)

    result = cache.get("AAPL")
    assert result is not None
    assert result.symbol == "AAPL"
    assert result.trailing_pe == 28.5


def test_cache_miss_returns_none(tmp_path):
    """未快取的 symbol 回傳 None。"""
    cache = MetricsCache(cache_dir=tmp_path)
    cache.load()
    assert cache.get("UNKNOWN") is None


def test_cache_ttl_expiry(tmp_path):
    """超過 TTL 後 get 回傳 None。"""
    config = CacheConfig(ttl_seconds=3600)  # 1 小時
    cache = MetricsCache(config=config, cache_dir=tmp_path)
    cache.load()

    metrics = _make_metrics("AAPL")
    cache.put(metrics)

    # 模擬 2 小時前抓取
    key = "AAPL"
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    cache._data[key]["fetched_at"] = old_time.isoformat()

    assert cache.get("AAPL") is None


def test_cache_error_ttl_shorter(tmp_path):
    """抓取失敗的快取使用較短 TTL。"""
    config = CacheConfig(ttl_seconds=86400, error_ttl_seconds=3600)
    cache = MetricsCache(config=config, cache_dir=tmp_path)
    cache.load()

    # 正常資料 2 小時前抓取 → 仍有效（TTL 24h）
    normal = _make_metrics("GOOD")
    cache.put(normal)
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    cache._data["GOOD"]["fetched_at"] = old_time.isoformat()
    assert cache.get("GOOD") is not None

    # 失敗資料 2 小時前抓取 → 已過期（TTL 1h）
    error = TickerMetrics(symbol="BAD", fetch_error="Timeout")
    cache.put(error)
    cache._data["BAD"]["fetched_at"] = old_time.isoformat()
    assert cache.get("BAD") is None


def test_cache_save_and_load(tmp_path):
    """save → 新建 MetricsCache → load → get 成功。"""
    # 寫入
    cache1 = MetricsCache(cache_dir=tmp_path)
    cache1.load()
    cache1.put(_make_metrics("MSFT", trailing_pe=32.0))
    cache1.save()

    # 讀取（全新實例）
    cache2 = MetricsCache(cache_dir=tmp_path)
    cache2.load()
    result = cache2.get("MSFT")
    assert result is not None
    assert result.trailing_pe == 32.0


def test_cache_corruption_handled(tmp_path):
    """損壞的 JSON 不會 crash，建立空快取。"""
    cache_file = tmp_path / "metrics_cache.json"
    cache_file.write_text("{ invalid json !!!}")

    cache = MetricsCache(cache_dir=tmp_path)
    cache.load()  # 不應 raise

    assert cache.size == 0
    assert cache.get("AAPL") is None


def test_cache_clear(tmp_path):
    """clear 後 get 回傳 None。"""
    cache = MetricsCache(cache_dir=tmp_path)
    cache.load()
    cache.put(_make_metrics("AAPL"))
    assert cache.get("AAPL") is not None

    cache.clear()
    assert cache.get("AAPL") is None
    assert cache.size == 0


def test_cache_dirty_flag(tmp_path):
    """put 後 dirty=True，save 後 dirty=False。"""
    cache = MetricsCache(cache_dir=tmp_path)
    cache.load()

    assert cache._dirty is False

    cache.put(_make_metrics("AAPL"))
    assert cache._dirty is True

    cache.save()
    assert cache._dirty is False
