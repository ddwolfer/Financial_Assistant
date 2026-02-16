"""
指標資料快取管理。

以 JSON 檔案儲存 TickerMetrics，支援 TTL 自動過期。
成功抓取的資料快取 24 小時，失敗的快取 1 小時後自動重試。

快取檔案格式：
{
  "AAPL": {
    "fetched_at": "2026-02-17T10:30:00+00:00",
    "metrics": { ... TickerMetrics.to_dict() ... }
  }
}
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from scripts.scanner.config import CacheConfig, DEFAULT_CACHE_CONFIG
from scripts.scanner.data_fetcher import TickerMetrics

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class MetricsCache:
    """
    TTL 快取管理器，用於 TickerMetrics 的本地 JSON 快取。

    使用方法：
        cache = MetricsCache()
        cache.load()              # 從磁碟載入
        cached = cache.get("AAPL")  # 命中時回傳 TickerMetrics，否則 None
        cache.put(metrics)        # 寫入記憶體快取
        cache.save()              # 將變更寫回磁碟
    """

    def __init__(
        self,
        config: CacheConfig = DEFAULT_CACHE_CONFIG,
        cache_dir: Optional[Path] = None,
    ):
        self._config = config
        self._cache_dir = cache_dir or _CACHE_DIR
        self._cache_path = self._cache_dir / config.cache_filename
        self._data: dict[str, dict] = {}
        self._dirty = False

    def load(self) -> None:
        """從磁碟載入快取檔案。損壞時建立空快取。"""
        if not self._cache_path.exists():
            self._data = {}
            return

        try:
            with open(self._cache_path) as f:
                self._data = json.load(f)
            logger.debug("快取已載入: %d 筆資料", len(self._data))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("快取檔案損壞或無法讀取，重建空快取: %s", e)
            self._data = {}

    def save(self) -> None:
        """將記憶體快取寫回磁碟（僅在有變更時寫入，使用 atomic write）。"""
        if not self._dirty:
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Atomic write：先寫暫存檔，再 rename，防止並行寫入損壞
        tmp_path = self._cache_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self._cache_path)

        self._dirty = False
        logger.info("快取已存檔: %d 筆資料 -> %s", len(self._data), self._cache_path)

    def get(self, symbol: str) -> Optional[TickerMetrics]:
        """
        查詢快取。回傳未過期的 TickerMetrics，或 None。

        TTL 規則：
        - 成功抓取：ttl_seconds（預設 24 小時）
        - 抓取失敗：error_ttl_seconds（預設 1 小時）
        """
        key = symbol.upper()
        entry = self._data.get(key)
        if entry is None:
            logger.debug("快取未命中: %s（不存在）", key)
            return None

        fetched_at = datetime.fromisoformat(entry["fetched_at"])
        now = datetime.now(timezone.utc)
        age_seconds = (now - fetched_at).total_seconds()

        metrics = TickerMetrics.from_dict(entry["metrics"])

        # 失敗的快取用較短 TTL
        ttl = (
            self._config.error_ttl_seconds
            if metrics.fetch_error
            else self._config.ttl_seconds
        )

        if age_seconds > ttl:
            logger.debug(
                "快取已過期: %s（%.0f 秒前抓取，TTL=%d）",
                key, age_seconds, ttl,
            )
            return None

        logger.debug("快取命中: %s（%.0f 秒前抓取）", key, age_seconds)
        return metrics

    def put(self, metrics: TickerMetrics) -> None:
        """寫入快取（記憶體），設定 fetched_at 為當前 UTC 時間。"""
        key = metrics.symbol.upper()
        self._data[key] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics.to_dict(),
        }
        self._dirty = True

    def clear(self) -> None:
        """清除所有快取資料。"""
        self._data = {}
        self._dirty = True

    @property
    def size(self) -> int:
        """回傳快取中的項目數量。"""
        return len(self._data)
