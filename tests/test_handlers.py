#!/usr/bin/env python3
"""
Test handlers module - the single source of truth for tool routing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_yfinance_ux.handlers import normalize_symbols, call_tool


def test_normalize_symbols_single():
    """Test single symbol normalization"""
    assert normalize_symbols("tsla") == ["TSLA"]
    assert normalize_symbols("TSLA") == ["TSLA"]
    assert normalize_symbols(" tsla ") == ["TSLA"]
    print("✓ Single symbol normalization works")


def test_normalize_symbols_comma_separated():
    """Test comma-separated string normalization"""
    assert normalize_symbols("TSLA,F,GM") == ["TSLA", "F", "GM"]
    assert normalize_symbols("tsla, f, gm") == ["TSLA", "F", "GM"]
    assert normalize_symbols("TSLA,  F  ,GM") == ["TSLA", "F", "GM"]
    assert normalize_symbols("GRRR,TSLA") == ["GRRR", "TSLA"]
    print("✓ Comma-separated normalization works")


def test_normalize_symbols_list():
    """Test list normalization"""
    assert normalize_symbols(["tsla", "f"]) == ["TSLA", "F"]
    assert normalize_symbols(["TSLA"]) == ["TSLA"]
    assert normalize_symbols([" tsla ", " f "]) == ["TSLA", "F"]
    print("✓ List normalization works")


def test_normalize_symbols_empty():
    """Test edge cases"""
    assert normalize_symbols([]) == []
    assert normalize_symbols(["", " "]) == []
    assert normalize_symbols(",,,") == []
    print("✓ Edge case normalization works")


def test_call_tool_markets():
    """Test markets tool routing"""
    result = call_tool("markets", {})
    assert "MARKETS" in result
    assert len(result) > 100
    print("✓ markets() tool routing works")


def test_call_tool_ticker_single():
    """Test ticker tool with single symbol"""
    result = call_tool("ticker", {"symbol": "TSLA"})
    assert "TSLA" in result
    assert "Tesla" in result
    print("✓ ticker() single mode works")


def test_call_tool_ticker_batch():
    """Test ticker tool with multiple symbols"""
    result = call_tool("ticker", {"symbol": "TSLA,F"})
    assert "TICKERS" in result  # Batch mode header
    assert "TSLA" in result
    assert "F" in result or "Ford" in result
    print("✓ ticker() batch mode works")


def test_call_tool_ticker_list():
    """Test ticker tool with list input"""
    result = call_tool("ticker", {"symbol": ["TSLA", "F"]})
    assert "TICKERS" in result
    print("✓ ticker() list input works")


def test_call_tool_sector():
    """Test sector tool routing"""
    result = call_tool("sector", {"name": "technology"})
    assert "TECHNOLOGY" in result or "XLK" in result
    print("✓ sector() tool routing works")


def test_call_tool_unknown():
    """Test unknown tool error"""
    try:
        call_tool("unknown_tool", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown tool" in str(e)
    print("✓ Unknown tool error works")


def test_call_tool_missing_param():
    """Test missing parameter error"""
    try:
        call_tool("ticker", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "requires" in str(e)
    print("✓ Missing parameter error works")


if __name__ == "__main__":
    print("Testing handlers module...\n")

    # Unit tests (no network)
    print("--- normalize_symbols tests ---")
    test_normalize_symbols_single()
    test_normalize_symbols_comma_separated()
    test_normalize_symbols_list()
    test_normalize_symbols_empty()
    print()

    # Integration tests (require network)
    print("--- call_tool routing tests ---")
    test_call_tool_markets()
    test_call_tool_ticker_single()
    test_call_tool_ticker_batch()
    test_call_tool_ticker_list()
    test_call_tool_sector()
    print()

    # Error handling tests
    print("--- error handling tests ---")
    test_call_tool_unknown()
    test_call_tool_missing_param()
    print()

    print("All handler tests passed! ✓")
