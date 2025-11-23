"""
Historical data fetching - imports from yfinance_ux library

CANONICAL SOURCE: yfinance_ux.fetcher (library package)

This module re-exports from yfinance_ux for backward compatibility.
"""

from yfinance_ux.fetcher import (
    calculate_date_range,
    fetch_multiple_histories,
    fetch_price_at_date,
    fetch_price_history,
    fetch_ticker_and_market,
)

__all__ = [
    "calculate_date_range",
    "fetch_multiple_histories",
    "fetch_price_at_date",
    "fetch_price_history",
    "fetch_ticker_and_market",
]
