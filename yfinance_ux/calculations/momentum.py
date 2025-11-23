"""
Momentum calculations for trailing returns.

Optimized narrow window fetching for 1W, 1M, 1Y momentum.
Fetches ~22 days total vs 252 days (91% reduction).
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.fetcher import fetch_price_at_date


def calculate_momentum(symbol: str) -> dict[str, float | None]:
    """
    Calculate trailing returns (1W, 1M, 1Y) for momentum analysis

    Uses fast_info for current price + narrow window fetches for precise lookback dates
    Fetches ~22 days total vs 252 days (91% reduction)
    """
    try:
        ticker = yf.Ticker(symbol)

        # Get current price from fast_info (no fetch!)
        current_price = ticker.fast_info.get("lastPrice")
        if current_price is None:
            return {"momentum_1w": None, "momentum_1m": None, "momentum_1y": None}

        # Calculate target dates for precise lookback
        now = datetime.now(ZoneInfo("America/New_York"))
        date_1y_ago = now - timedelta(days=365)
        date_1m_ago = now - timedelta(days=30)
        date_1w_ago = now - timedelta(days=7)

        # Fetch prices at specific dates (narrow windows, ~7-8 days each)
        price_1y_ago = fetch_price_at_date(symbol, date_1y_ago)
        price_1m_ago = fetch_price_at_date(symbol, date_1m_ago)
        price_1w_ago = fetch_price_at_date(symbol, date_1w_ago)

        # Calculate momentum
        momentum_1y = (
            ((current_price - price_1y_ago) / price_1y_ago * 100)
            if price_1y_ago else None
        )
        momentum_1m = (
            ((current_price - price_1m_ago) / price_1m_ago * 100)
            if price_1m_ago else None
        )
        momentum_1w = (
            ((current_price - price_1w_ago) / price_1w_ago * 100)
            if price_1w_ago else None
        )

        return {
            "momentum_1w": momentum_1w,
            "momentum_1m": momentum_1m,
            "momentum_1y": momentum_1y,
        }
    except Exception:
        return {"momentum_1w": None, "momentum_1m": None, "momentum_1y": None}
