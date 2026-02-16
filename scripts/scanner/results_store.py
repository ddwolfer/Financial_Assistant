"""
Screening results persistence.

Saves and loads screening results as JSON in the data/ directory.
Each screening run is timestamped. Supports both ScreeningResult
and SectorScreeningResult via duck typing (both have to_dict()).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


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
