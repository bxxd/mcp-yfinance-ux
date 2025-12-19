"""
Tool handlers - single source of truth for tool execution logic.

This module contains the core business logic routing that both
server.py (stdio) and server_http.py (HTTP/SSE) use.

Architecture:
- Protocol layer (server.py, server_http.py) handles MCP transport
- This module handles argument parsing and routing to market_data
- market_data.py handles actual data fetching and formatting
"""

from typing import Any

from .market_data import (
    format_markets,
    format_options,
    format_sector,
    format_ticker,
    format_ticker_batch,
    get_markets_data,
    get_options_data,
    get_sector_data,
    get_ticker_screen_data,
    get_ticker_screen_data_batch,
)


def normalize_symbols(symbol: str | list[str]) -> list[str]:
    """
    Normalize symbol input to list of uppercase symbols.

    Handles:
    - Single string: "TSLA" -> ["TSLA"]
    - Comma-separated string: "TSLA,F,GM" -> ["TSLA", "F", "GM"]
    - List: ["TSLA", "F"] -> ["TSLA", "F"]
    """
    if isinstance(symbol, list):
        return [s.strip().upper() for s in symbol if s.strip()]

    # str case - check for comma-separated
    if "," in symbol:
        return [s.strip().upper() for s in symbol.split(",") if s.strip()]
    return [symbol.strip().upper()]


def handle_markets() -> str:
    """Handle markets() tool call"""
    data = get_markets_data()
    return format_markets(data)


def handle_sector(arguments: dict[str, Any]) -> str:
    """Handle sector() tool call"""
    sector_name = arguments.get("name")
    if not sector_name:
        msg = "sector() requires 'name' parameter"
        raise ValueError(msg)
    data = get_sector_data(sector_name)
    return format_sector(data)


def handle_ticker(arguments: dict[str, Any]) -> str:
    """Handle ticker() tool call - single or batch mode"""
    symbol = arguments.get("symbol")
    if not symbol:
        msg = "ticker() requires 'symbol' parameter"
        raise ValueError(msg)

    symbols = normalize_symbols(symbol)

    if not symbols:
        msg = "ticker() symbol normalization produced no valid symbols"
        raise ValueError(msg)

    if len(symbols) > 1:
        # Batch comparison mode
        data_list = get_ticker_screen_data_batch(symbols)
        return format_ticker_batch(data_list)

    # Single ticker mode
    data = get_ticker_screen_data(symbols[0])
    return format_ticker(data)


def handle_ticker_options(arguments: dict[str, Any]) -> str:
    """Handle ticker_options() tool call"""
    symbol = arguments.get("symbol")
    if not symbol:
        msg = "ticker_options() requires 'symbol' parameter"
        raise ValueError(msg)
    expiration = arguments.get("expiration", "nearest")
    data = get_options_data(symbol, expiration)
    return format_options(data)


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    """
    Route tool call to appropriate handler.

    Returns formatted string output.
    Raises ValueError for unknown tools or missing parameters.
    """
    if name == "markets":
        return handle_markets()

    if name == "sector":
        return handle_sector(arguments)

    if name == "ticker":
        return handle_ticker(arguments)

    if name == "ticker_options":
        return handle_ticker_options(arguments)

    msg = f"Unknown tool: {name}"
    raise ValueError(msg)
