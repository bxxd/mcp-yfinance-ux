#!/usr/bin/env python3
"""
MCP Tool Definitions - Single Source of Truth

Tool definitions shared between server.py (stdio) and server_http.py (SSE/HTTP).
Define tools once, import everywhere.
"""

from mcp.types import Tool


def get_mcp_tools() -> list[Tool]:
    """
    Return list of MCP tools.

    Single source of truth for tool definitions.
    Both stdio and HTTP servers import this function.
    """
    return [
        Tool(
            name="markets",
            description="""Market overview: indices, sectors, styles, commodities, rates.

US/Global equities, 11 GICS sectors, style factors, VIX, 10Y. Price, change%, 1M/1Y momentum.
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sector",
            description="""Sector drill-down: ETF performance + top 10 holdings with weights.

sector("technology") → XLK price, 1M/1Y momentum, top holdings
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Sector name (e.g., 'technology', 'financials', "
                            "'healthcare', 'energy', 'consumer discretionary', "
                            "'consumer staples', 'industrials', 'utilities', "
                            "'materials', 'real estate', 'communication')"
                        ),
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="ticker",
            description="""Security analysis: factors, valuation, technicals, insider, analyst.

ticker("TSLA") → beta, idio vol, P/E, momentum, 52wk, options, insider
ticker(["TSLA", "F"]) → side-by-side comparison

Macro: ^TNX, ^VIX, CL=F, GC=F, EURUSD=X for regression.
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": (
                            "Ticker symbol or list of symbols "
                            "(e.g., 'TSLA' or ['TSLA', 'F', 'GM'])"
                        ),
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="ticker_history",
            description="""Price/volume series: one row per bar - close, change%, volume, RVOL.

ticker_history("IPX") -> 3mo daily series + period stats
ticker_history("IPX", "1y") -> 1y, auto-downsampled to weekly bars
ticker_history("IPX", "1y", "1d") -> force daily bars (most recent 80)

Use to date a move or read its volume signature. ticker() is the snapshot; this is the series.
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'IPX', 'AAPL')",
                    },
                    "period": {
                        "type": "string",
                        "description": (
                            "Window: '1mo', '3mo' (default), '6mo', '1y', '2y', '5y'"
                        ),
                        "default": "3mo",
                    },
                    "interval": {
                        "type": "string",
                        "description": (
                            "Bar size: 'auto' (default - daily up to 3mo, weekly to 2y, "
                            "then monthly), or force '1d', '1wk', '1mo'"
                        ),
                        "default": "auto",
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="ticker_options",
            description="""Options chain: positioning, IV, skew, term structure, unusual activity.

ticker_options("AAPL") → P/C ratio, top strikes, IV skew, max pain, unusual vol
ticker_options("AAPL", "2025-01-17") → specific expiration
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., 'PALL', 'AAPL')",
                    },
                    "expiration": {
                        "type": "string",
                        "description": "Expiration date: 'nearest' (default) or 'YYYY-MM-DD'",
                        "default": "nearest",
                    }
                },
                "required": ["symbol"]
            }
        ),
    ]
