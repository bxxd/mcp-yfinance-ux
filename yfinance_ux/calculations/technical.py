"""
Technical indicator calculations.

RSI (Relative Strength Index) and other technical analysis indicators.
"""

from typing import Any

import numpy as np

from yfinance_ux.common.constants import RSI_PERIOD


def calculate_rsi(prices: Any, period: int = RSI_PERIOD) -> float | None:  # noqa: ANN401
    """Calculate RSI (Relative Strength Index) for a price series"""
    try:
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Return most recent RSI value
        return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None
    except Exception:
        return None
