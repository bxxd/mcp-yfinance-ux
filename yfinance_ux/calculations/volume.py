"""Volume analytics calculations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from yfinance_ux.common.dates import is_market_open


def calculate_relative_volume(volume: float | None, avg_volume: float | None) -> float | None:
    """Calculate relative volume with intraday extrapolation.

    During market hours, raw volume is partial (e.g., 2hrs into 6.5hr day).
    Comparing 20M shares at 11am to 80M average is misleading (0.25x).
    Extrapolate to full day: 20M / (2/6.5) = 65M → 0.81x (more accurate).

    Note: Pre-market and after-hours volume is NOT extrapolated (use raw volume).
    is_market_open() returns True only during regular hours (9:30 AM - 4:00 PM ET).

    Args:
        volume: Current volume
        avg_volume: Average volume (3-month baseline)

    Returns:
        Relative volume (extrapolated if intraday), or None if inputs invalid
    """
    if volume is None or avg_volume is None or avg_volume <= 0:
        return None

    # During regular market hours (9:30 AM - 4:00 PM ET): extrapolate partial volume
    if is_market_open():
        now = datetime.now(ZoneInfo("America/New_York"))
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        if now > market_open:
            elapsed = (now - market_open).total_seconds()
            total_seconds = (market_close - market_open).total_seconds()
            fraction = min(elapsed / total_seconds, 1.0)

            # Extrapolate if we're at least 10% into the day (avoids inflated RVOL at 9:31 AM)
            if fraction > 0.1:
                extrapolated_volume = volume / fraction
                return extrapolated_volume / avg_volume
            else:
                # Very early in session: use raw volume
                return volume / avg_volume
        else:
            # Should not reach here (is_market_open() checks now >= market_open)
            return volume / avg_volume
    else:
        # Pre-market or after-hours: use raw volume (no extrapolation)
        return volume / avg_volume
