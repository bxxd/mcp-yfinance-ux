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
            description="""
Complete market overview - indices, sectors, styles, commodities, rates.

Coverage:
- US equities (S&P 500, Nasdaq, Dow, Russell 2000)
- Global markets (Europe, Asia)
- All 11 GICS sectors with momentum
- Style factors (Momentum, Value, Growth, Quality, Size)
- Commodities (Gold, Oil, Nat Gas), Volatility (VIX), Rates (10Y)

Shows current price, change %, 1M and 1Y momentum for each.

Use this to scan the entire market landscape at a glance.
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sector",
            description="""
Sector drill-down - ETF performance + top 10 holdings.

Shows sector ETF price, momentum (1M/1Y), and largest positions with weights.

Input: Sector name
- 'technology', 'financials', 'healthcare', 'energy'
- 'consumer_disc', 'consumer_stpl', 'industrials'
- 'materials', 'utilities', 'real_estate', 'communication'

Use this to analyze sector composition and performance.
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
            description="""
Security analysis - factor exposures, valuation, technicals, options, insider activity.

SINGLE: ticker('TSLA')
- Factor exposures: Beta SPX, Idio Vol, Total Vol
- Valuation: P/E, Fwd P/E, Div Yield
- Calendar: Earnings, Ex-Div dates
- Momentum: 1W/1M/1Y, 50/200 MA, RSI
- 52-wk range + viz
- Options: P/C ratio, ATM IV summary
- Insider Transactions: Recent 10 trades (date, insider, position, type, shares, value)

BATCH: ticker(['TSLA', 'F', 'GM'])
- Side-by-side table
- Price, Chg%, Beta, Idio Vol
- Mom (1W/1M/1Y), P/E, Div%, RSI

Single = deep dive. Batch = compare.

MACRO FACTORS (for Paleologo regression analysis):
- Treasury Rates: ^TNX (10Y), ^IRX (2Y), ^TYX (30Y), ^FVX (5Y)
- Commodities: CL=F (Oil WTI), NG=F (Nat Gas), GC=F (Gold), SI=F (Silver)
- Volatility: ^VIX
- Currencies: EURUSD=X, JPY=X, CNY=X, GBPUSD=X
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
            description="""
Options chain - positioning, IV, skew, term structure, unusual activity.

Shows:
- Positioning: P/C ratio (OI+vol), ITM/OTM breakdown
- Top strikes by OI: Top 10 calls/puts, side-by-side
- IV structure: ATM calls/puts, spread
- Vol skew: OTM vs ATM (panic detection)
- Term structure: Near/mid/far IV, contango
- Volume analysis: P/C vol ratio, unusual (vol > 2x OI)
- Max pain: Strike w/ most seller pain
- Historical IV: 30d hist vol, 52-wk IV range, percentile
- All expirations: Summary table

Input: symbol, expiration ('nearest' or 'YYYY-MM-DD')

Context delivery. No recommendations.
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
