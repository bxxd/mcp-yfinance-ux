"""
Historical data fetching - optimized date range queries
Separate from market_data.py business logic
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd  # type: ignore[import-untyped]
import yfinance as yf  # type: ignore[import-untyped]


def normalize_symbol(symbol: str) -> str | None:
    """
    Normalize ticker symbol to Yahoo Finance format.

    Handles:
    - Exchange suffixes: NEO.TO, 0700.HK (keep dots)
    - Share classes: BRK.B → BRK-B, BRK/B → BRK-B (replace with hyphens)
    - Preferred stock: BAC.PL → BAC-PL

    Args:
        symbol: Raw ticker symbol

    Returns:
        Normalized symbol, or None if invalid
    """
    if not symbol or not symbol.strip():
        return None

    symbol = symbol.strip().upper()

    # Replace slashes with hyphens first
    symbol = symbol.replace("/", "-")

    # Check if this is an exchange suffix
    # Common exchange suffixes: .TO, .HK, .L, .AX, .PA, .DE, .SW, .F, etc.
    if "." in symbol:
        parts = symbol.split(".")
        if len(parts) == 2:  # noqa: PLR2004
            suffix = parts[1].upper()
            # Known single-letter exchange suffixes
            single_letter_exchanges = {"L", "F", "P"}  # London, Frankfurt, Paris
            # Exchange suffix if:
            # - Single uppercase letter in known set, OR
            # - 2+ uppercase characters
            if (
                (len(suffix) == 1 and suffix in single_letter_exchanges)
                or (len(suffix) >= 2 and suffix.isupper())  # noqa: PLR2004
            ):
                # Exchange suffix - keep the dot
                return symbol
        # Share class - replace dot with dash
        return symbol.replace(".", "-")

    return symbol


def calculate_date_range(months: int) -> tuple[str, str]:
    """
    Calculate start/end dates for historical data fetch

    Args:
        months: Number of months of history (minimal buffer for weekends/holidays)

    Returns:
        Tuple of (start_date, end_date) as ISO strings
    """
    end_date = datetime.now(ZoneInfo("America/New_York"))
    # Minimal buffer: ~5 trading days per month are weekends/holidays
    # For 12 months: ~252 trading days = ~365 calendar days
    calendar_days = int(months * 30.5)  # Avg days per month
    start_date = end_date - timedelta(days=calendar_days)

    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def fetch_price_history(
    symbol: str,
    months: int = 12,
    interval: str = "1d"
) -> Any:  # Returns pd.DataFrame  # noqa: ANN401
    """
    Fetch minimal historical price data for a symbol

    Args:
        symbol: Ticker symbol
        months: Number of months of history (default 12)
        interval: Data interval (default "1d")

    Returns:
        DataFrame with OHLCV data, empty DataFrame on error
    """
    try:
        ticker = yf.Ticker(symbol)
        start_date, end_date = calculate_date_range(months)

        hist = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval
        )

        return hist if not hist.empty else pd.DataFrame()

    except Exception:
        return pd.DataFrame()


def fetch_multiple_histories(
    symbols: list[str],
    months: int = 12,
    interval: str = "1d",
    max_workers: int = 10
) -> dict[str, Any]:  # Returns dict[str, pd.DataFrame]
    """
    Fetch historical data for multiple symbols in parallel

    Args:
        symbols: List of ticker symbols
        months: Number of months of history
        interval: Data interval
        max_workers: Max concurrent API calls

    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    results: dict[str, Any] = {}  # Dict[str, pd.DataFrame]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all fetch jobs
        future_to_symbol = {
            executor.submit(fetch_price_history, symbol, months, interval): symbol
            for symbol in symbols
        }

        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                results[symbol] = future.result()
            except Exception:
                results[symbol] = pd.DataFrame()

    return results


def fetch_ticker_and_market(
    symbol: str,
    months: int = 12,
    market_symbol: str = "^GSPC"
) -> tuple[Any, Any]:  # Returns tuple[pd.DataFrame, pd.DataFrame]
    """
    Fetch ticker and market data in parallel (for factor analysis)

    Args:
        symbol: Ticker symbol
        months: Number of months of history
        market_symbol: Market index symbol (default S&P 500)

    Returns:
        Tuple of (ticker_hist, market_hist) DataFrames
    """
    histories = fetch_multiple_histories([symbol, market_symbol], months=months)

    return (
        histories.get(symbol, pd.DataFrame()),
        histories.get(market_symbol, pd.DataFrame())
    )


def fetch_price_at_date(
    symbol: str,
    target_date: datetime,
    window_days: int = 5
) -> Any:  # Returns float | None  # noqa: ANN401
    """
    Fetch price at a specific date using minimal window

    Args:
        symbol: Ticker symbol
        target_date: Target date for price lookup
        window_days: Days to fetch before/after target (default 5)

    Returns:
        Price (float) or None if not available
    """
    try:
        ticker = yf.Ticker(symbol)

        # Fetch narrow window around target date
        start = (target_date - timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = (target_date + timedelta(days=window_days)).strftime("%Y-%m-%d")

        hist = ticker.history(start=start, end=end)

        if hist.empty:
            return None

        closes = hist["Close"].dropna()
        if len(closes) == 0:
            return None

        # Find closest date to target (not just first in window)
        target_ts = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        time_diffs = [(abs((idx - target_ts).total_seconds()), price)
                     for idx, price in closes.items()]
        _, closest_price = min(time_diffs, key=lambda x: x[0])

        return float(closest_price)

    except Exception:
        return None
