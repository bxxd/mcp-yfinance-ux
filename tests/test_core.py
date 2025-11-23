#!/usr/bin/env python3
"""
Test core market_data module independently (no MCP required)
Demonstrates proper separation of concerns
"""

import sys
from pathlib import Path

# Add project root to path so we can import mcp_yfinance_ux
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yfinance_ux.common.dates import is_market_open
from mcp_yfinance_ux.market_data import (
    get_ticker_data,
    get_market_snapshot,
    format_market_snapshot,
)


def test_market_hours():
    """Test market hours detection"""
    result = is_market_open()
    print(f"Market open: {result}")
    assert isinstance(result, bool)
    print("✓ Market hours detection works")


def test_single_ticker():
    """Test fetching single ticker data"""
    data = get_ticker_data("^GSPC")
    print(f"S&P 500 data: {data}")
    assert "symbol" in data
    assert data["symbol"] == "^GSPC"
    print("✓ Single ticker fetch works")


def test_market_snapshot():
    """Test market snapshot with categories"""
    data = get_market_snapshot(["futures", "factors"])
    print(f"Fetched {len(data)} symbols")
    assert len(data) > 0
    print("✓ Market snapshot works")


def test_formatting():
    """Test formatted output"""
    data = get_market_snapshot(["futures"])
    formatted = format_market_snapshot(data)
    print("\nFormatted output:")
    print(formatted)
    assert "MARKETS" in formatted
    print("✓ Formatting works")


if __name__ == "__main__":
    print("Testing core market_data module (independent of MCP)...\n")

    test_market_hours()
    print()

    test_single_ticker()
    print()

    test_market_snapshot()
    print()

    test_formatting()
    print()

    print("All tests passed! ✓")
