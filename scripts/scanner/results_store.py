"""
篩選與分析結果持久化。

Layer 1 篩選結果存為 `screening_{tag}_{timestamp}.json`。
Layer 3 深度分析結果存為 `deep_analysis_{symbol}_{timestamp}.json`
以及對應的 Markdown 報告 `deep_analysis_{symbol}_{timestamp}.md`。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_REPORTS_DIR = _DATA_DIR / "reports"


def save_screening_results(
    results: list[Any],
    tag: str = "layer1",
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Save screening results to a timestamped JSON file.

    Accepts any result objects with a to_dict() method
    (ScreeningResult or SectorScreeningResult).

    Returns the path to the saved file.
    """
    output_dir = output_dir or _DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"screening_{tag}_{timestamp}.json"
    filepath = output_dir / filename

    # 判斷 screening_mode（若結果有 screening_mode 屬性）
    screening_mode = "absolute"
    if results and hasattr(results[0], "screening_mode"):
        screening_mode = "dual_track"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": tag,
        "screening_mode": screening_mode,
        "total_screened": len(results),
        "total_passed": sum(1 for r in results if r.passed),
        "results": [r.to_dict() for r in results],
    }

    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    return filepath


def load_latest_results(
    tag: str = "layer1",
    data_dir: Optional[Path] = None,
) -> Optional[dict]:
    """Load the most recent screening results for a given tag."""
    data_dir = data_dir or _DATA_DIR
    pattern = f"screening_{tag}_*.json"
    files = sorted(data_dir.glob(pattern), reverse=True)

    if not files:
        return None

    with open(files[0]) as f:
        return json.load(f)


# ============================================================
# Layer 3 深度分析結果持久化
# ============================================================

def save_deep_analysis(
    symbol: str,
    json_data: dict,
    markdown_report: str,
    output_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
) -> dict[str, Path]:
    """
    儲存 Layer 3 深度分析結果（JSON + Markdown）。

    JSON 存至 data/deep_analysis_{symbol}_{timestamp}.json
    Markdown 存至 data/reports/deep_analysis_{symbol}_{timestamp}.md

    Args:
        symbol: 股票代碼
        json_data: DeepAnalysisData.to_dict() 結果
        markdown_report: 完整 Markdown 報告文字
        output_dir: JSON 輸出目錄（預設 data/）
        reports_dir: Markdown 輸出目錄（預設 data/reports/）

    Returns:
        {"json_path": Path, "markdown_path": Path}
    """
    output_dir = output_dir or _DATA_DIR
    reports_dir = reports_dir or _REPORTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sym = symbol.upper()

    # 存 JSON
    json_filename = f"deep_analysis_{sym}_{timestamp}.json"
    json_path = output_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

    # 存 Markdown
    md_filename = f"deep_analysis_{sym}_{timestamp}.md"
    md_path = reports_dir / md_filename
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    logger.info("已儲存 %s 分析結果: %s, %s", sym, json_path, md_path)

    return {"json_path": json_path, "markdown_path": md_path}


def load_latest_deep_analysis(
    symbol: str,
    data_dir: Optional[Path] = None,
) -> Optional[dict]:
    """
    載入指定股票最新的 Layer 3 深度分析 JSON 結果。

    Args:
        symbol: 股票代碼
        data_dir: 數據目錄（預設 data/）

    Returns:
        解析後的 JSON 字典，或 None
    """
    data_dir = data_dir or _DATA_DIR
    sym = symbol.upper()
    pattern = f"deep_analysis_{sym}_*.json"
    files = sorted(data_dir.glob(pattern), reverse=True)

    if not files:
        return None

    with open(files[0], encoding="utf-8") as f:
        return json.load(f)


def load_latest_deep_analysis_report(
    symbol: str,
    reports_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    載入指定股票最新的 Layer 3 Markdown 報告。

    Args:
        symbol: 股票代碼
        reports_dir: 報告目錄（預設 data/reports/）

    Returns:
        Markdown 報告文字，或 None
    """
    reports_dir = reports_dir or _REPORTS_DIR
    sym = symbol.upper()
    pattern = f"deep_analysis_{sym}_*.md"
    files = sorted(reports_dir.glob(pattern), reverse=True)

    if not files:
        return None

    with open(files[0], encoding="utf-8") as f:
        return f.read()


def list_deep_analysis_symbols(
    data_dir: Optional[Path] = None,
) -> list[str]:
    """
    列出所有已有深度分析結果的股票代碼。

    Returns:
        去重且排序的股票代碼列表
    """
    data_dir = data_dir or _DATA_DIR
    pattern = "deep_analysis_*_*.json"
    files = data_dir.glob(pattern)

    symbols = set()
    for f in files:
        # 檔名格式: deep_analysis_AAPL_20260217_100000.json
        parts = f.stem.split("_")
        if len(parts) >= 3:
            # 取 deep_analysis_ 之後、timestamp 之前的部分
            sym = parts[2]
            symbols.add(sym)

    return sorted(symbols)
