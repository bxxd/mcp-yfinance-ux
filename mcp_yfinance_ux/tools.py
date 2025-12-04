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
