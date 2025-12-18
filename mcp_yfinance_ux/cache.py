"""Simple in-memory cache for market data with market-aware TTL"""

from datetime import datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from mcp_yfinance_ux.logging_config import get_logger

logger = get_logger(__name__)

# 24-hour markets (always live data with short TTL)
TWENTY_FOUR_HOUR_SYMBOLS = {
    # Crypto
    "BTC-USD", "ETH-USD", "SOL-USD",
    # Commodities futures
    "GC=F", "SI=F", "PL=F", "HG=F", "CL=F", "NG=F",
    # US Futures
    "ES=F", "NQ=F", "YM=F",
}

# Cache storage: {symbol: {"data": {...}, "timestamp": datetime, "expires_at": datetime}}
_cache: dict[str, dict[str, Any]] = {}

# TTL for 24-hour markets (in seconds)
CRYPTO_TTL_SECONDS = 120  # 2 minutes for crypto
FUTURES_TTL_SECONDS = 30  # 30 seconds for futures (more active)

# Weekend detection (weekday() returns 5=Saturday, 6=Sunday)
SATURDAY = 5

# Futures symbols (subset of 24-hour markets, need shorter cache)
FUTURES_SYMBOLS = {
    "ES=F", "NQ=F", "YM=F",  # US index futures
    "GC=F", "SI=F", "PL=F", "HG=F", "CL=F", "NG=F",  # Commodity futures
}


def get_next_market_open() -> datetime:
    """Get the next market open time (9:30am ET)"""
    now = datetime.now(ZoneInfo("America/New_York"))

    # Start with today's 9:30am
    next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)

    # If we're past 9:30am today, move to tomorrow
    if now >= next_open:
        next_open = next_open + timedelta(days=1)

    # Handle weekends - if next_open is Saturday or Sunday, move to Monday
    while next_open.weekday() >= SATURDAY:
        next_open = next_open + timedelta(days=1)

    return next_open


def is_24_hour_market(symbol: str) -> bool:
    """Check if symbol trades 24 hours (crypto, futures)"""
    return symbol in TWENTY_FOUR_HOUR_SYMBOLS


def get_cache_expiry(symbol: str) -> datetime:
    """Get cache expiry time for symbol based on market type"""
    now = datetime.now(ZoneInfo("America/New_York"))

    if symbol in FUTURES_SYMBOLS:
        # Futures: 30 second cache (very active)
        return now + timedelta(seconds=FUTURES_TTL_SECONDS)
    if is_24_hour_market(symbol):
        # Crypto: 2 minute cache
        return now + timedelta(seconds=CRYPTO_TTL_SECONDS)

    # Session markets: SHORT TTL when open, cache until next open when closed
    from yfinance_ux.common.dates import is_market_open
    if is_market_open():
        # Market open: 2 minute cache for live updates during trading hours
        return now + timedelta(seconds=120)
    else:
        # Market closed: cache until next open (prices won't change)
        return get_next_market_open()


def get_cached_data(symbol: str) -> dict[str, Any] | None:
    """Get cached data for symbol if still valid"""
    if symbol not in _cache:
        logger.debug(f"Cache MISS: {symbol} (not in cache)")
        return None

    cached = _cache[symbol]
    now = datetime.now(ZoneInfo("America/New_York"))

    # Check if expired
    if now >= cached["expires_at"]:
        # Expired - remove from cache
        ttl_expired = (now - cached["expires_at"]).total_seconds()
        logger.debug(f"Cache MISS: {symbol} (expired {ttl_expired:.1f}s ago)")
        del _cache[symbol]
        return None

    ttl_remaining = (cached["expires_at"] - now).total_seconds()
    if symbol in FUTURES_SYMBOLS:
        market_type = "futures"
    elif is_24_hour_market(symbol):
        market_type = "crypto"
    else:
        market_type = "session"
    logger.info(f"Cache HIT: {symbol} ({market_type}, TTL={ttl_remaining:.0f}s)")
    return cast("dict[str, Any]", cached["data"])


def set_cached_data(symbol: str, data: dict[str, Any]) -> None:
    """Cache data for symbol with appropriate TTL"""
    now = datetime.now(ZoneInfo("America/New_York"))
    expires_at = get_cache_expiry(symbol)
    ttl_seconds = (expires_at - now).total_seconds()

    _cache[symbol] = {
        "data": data,
        "timestamp": now,
        "expires_at": expires_at,
    }

    if symbol in FUTURES_SYMBOLS:
        market_type = "futures"
    elif is_24_hour_market(symbol):
        market_type = "crypto"
    else:
        market_type = "session"
    logger.info(f"Cache SET: {symbol} ({market_type}, TTL={ttl_seconds:.0f}s)")


def clear_cache() -> None:
    """Clear all cached data"""
    _cache.clear()


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics for debugging"""
    now = datetime.now(ZoneInfo("America/New_York"))

    return {
        "total_entries": len(_cache),
        "entries": [
            {
                "symbol": symbol,
                "cached_at": cached["timestamp"].isoformat(),
                "expires_at": cached["expires_at"].isoformat(),
                "ttl_seconds": (cached["expires_at"] - now).total_seconds(),
            }
            for symbol, cached in _cache.items()
        ]
    }
