"""
Date and market hours utilities for yfinance MCP server.

Market hours detection for US, European, and Asian markets.
Used for market status display and timing-aware data fetching.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from yfinance_ux.common.constants import FRIDAY, SATURDAY, SUNDAY, WEEKEND_START_DAY


def is_market_open() -> bool:
    """Check if US market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)"""
    now_et = datetime.now(ZoneInfo("America/New_York"))

    # Check if weekend
    if now_et.weekday() >= WEEKEND_START_DAY:
        return False

    # Check if within market hours (9:30 AM - 4:00 PM ET)
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now_et < market_close


def is_us_market_open() -> bool:
    """Check if US market is currently open (9:30 AM - 4:00 PM ET, Mon-Fri)"""
    return is_market_open()


def is_europe_market_open() -> bool:
    """Check if European markets are open (9:00 AM - 5:30 PM CET, Mon-Fri)"""
    now_cet = datetime.now(ZoneInfo("Europe/Paris"))

    # Check if weekend
    if now_cet.weekday() >= WEEKEND_START_DAY:
        return False

    # Check if within market hours (9:00 AM - 5:30 PM CET)
    market_open = now_cet.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_cet.replace(hour=17, minute=30, second=0, microsecond=0)

    return market_open <= now_cet < market_close


def is_asia_market_open() -> bool:
    """Check if Asian markets are open (9:00 AM - 3:00 PM JST for Tokyo, Mon-Fri)"""
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))

    # Check if weekend
    if now_jst.weekday() >= WEEKEND_START_DAY:
        return False

    # Check if within market hours (9:00 AM - 3:00 PM JST)
    market_open = now_jst.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now_jst.replace(hour=15, minute=0, second=0, microsecond=0)

    return market_open <= now_jst < market_close


def is_futures_open() -> bool:
    """Check if CME futures markets are open

    CME futures trade nearly 24/5:
    - Sunday 6:00 PM ET through Friday 5:00 PM ET
    - Daily maintenance: 5:00 PM - 6:00 PM ET
    """
    now_et = datetime.now(ZoneInfo("America/New_York"))

    # Friday after 5:00 PM ET - closed until Sunday 6:00 PM ET
    if now_et.weekday() == FRIDAY:
        close_time = now_et.replace(hour=17, minute=0, second=0, microsecond=0)
        if now_et >= close_time:
            return False

    # Saturday - closed all day
    if now_et.weekday() == SATURDAY:
        return False

    # Sunday before 6:00 PM ET - closed
    if now_et.weekday() == SUNDAY:
        open_time = now_et.replace(hour=18, minute=0, second=0, microsecond=0)
        if now_et < open_time:
            return False

    # Daily maintenance window: 5:00 PM - 6:00 PM ET (not during maintenance)
    maintenance_start = now_et.replace(hour=17, minute=0, second=0, microsecond=0)
    maintenance_end = now_et.replace(hour=18, minute=0, second=0, microsecond=0)
    return not (maintenance_start <= now_et < maintenance_end)


def get_market_status(region: str) -> str:
    """Get market status for a region"""
    status_map = {
        "us": is_us_market_open,
        "europe": is_europe_market_open,
        "asia": is_asia_market_open,
    }

    if region.lower() in status_map:
        is_open = status_map[region.lower()]()
        return "Open" if is_open else "Closed"

    return ""
