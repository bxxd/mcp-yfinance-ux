"""
yfinance_ux - Yahoo Finance data utilities

Pure library for fetching and processing market data.
No MCP dependencies.

Modules:
- common: Utilities (symbols, dates, constants)
- calculations: Math (momentum, volatility, technical indicators)
- services: Data fetching (tickers, markets, sectors, options)
- fetcher: Historical data fetching
"""

# Export key functions for convenience
from yfinance_ux.common.symbols import normalize_ticker_symbol
from yfinance_ux.fetcher import (
    calculate_date_range,
    fetch_multiple_histories,
    fetch_price_at_date,
    fetch_price_history,
    fetch_ticker_and_market,
    normalize_symbol,
)

__all__ = [
    # Fetcher functions
    "normalize_symbol",
    "calculate_date_range",
    "fetch_price_history",
    "fetch_multiple_histories",
    "fetch_ticker_and_market",
    "fetch_price_at_date",
    # Symbol utilities
    "normalize_ticker_symbol",
]

__version__ = "0.1.0"
