"""
Core market data functionality - yfinance business logic
Testable independently of MCP protocol layer
"""


from mcp_yfinance_ux.formatters.markets import (
    format_market_snapshot,
    format_markets,
)
from mcp_yfinance_ux.formatters.options import format_options
from mcp_yfinance_ux.formatters.sectors import format_sector
from mcp_yfinance_ux.formatters.tickers import (
    format_options_summary,
    format_ticker,
    format_ticker_batch,
)
from yfinance_ux.services.markets import (
    get_market_snapshot,
    get_markets_data,
    get_ticker_data,
    get_ticker_full_data,
    get_ticker_history,
)
from yfinance_ux.services.options import get_options_data
from yfinance_ux.services.sectors import get_sector_data
from yfinance_ux.services.tickers import (
    get_ticker_screen_data,
    get_ticker_screen_data_batch,
)

# Re-export all functions for backward compatibility
__all__ = [
    "format_market_snapshot",
    "format_markets",
    "format_options",
    "format_options_summary",
    "format_sector",
    "format_ticker",
    "format_ticker_batch",
    "get_market_snapshot",
    "get_markets_data",
    "get_options_data",
    "get_sector_data",
    "get_ticker_data",
    "get_ticker_full_data",
    "get_ticker_history",
    "get_ticker_screen_data",
    "get_ticker_screen_data_batch",
]
