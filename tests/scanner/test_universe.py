"""Tests for stock universe providers."""

import json
import tempfile
from pathlib import Path

from scripts.scanner.universe import get_tickers_from_file


def test_load_tickers_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(["AAPL", "msft", "  GOOGL  "], f)
        f.flush()
        result = get_tickers_from_file(f.name)
    assert result == ["AAPL", "MSFT", "GOOGL"]


def test_load_tickers_invalid_format():
    import pytest

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"not": "a list"}, f)
        f.flush()
        with pytest.raises(ValueError):
            get_tickers_from_file(f.name)
