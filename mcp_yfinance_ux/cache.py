"""Simple in-memory cache for market data with market-aware TTL"""

from datetime import datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from mcp_yfinance_ux.logging_config import get_logger
from yfinance_ux.common.dates import (
    get_next_asia_open,
    get_next_europe_open,
    get_next_us_open,
    is_asia_market_open,
    is_europe_market_open,
    is_market_open,
)

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

# Futures symbols (subset of 24-hour markets, need shorter cache)
FUTURES_SYMBOLS = {
    "ES=F", "NQ=F", "YM=F",  # US index futures
    "GC=F", "SI=F", "PL=F", "HG=F", "CL=F", "NG=F",  # Commodity futures
}

# Symbol to region: determines which market session governs cache expiry
SYMBOL_REGION: dict[str, str] = {
    # European indices
    "^STOXX50E": "europe", "^GDAXI": "europe", "^FTSE": "europe", "^FCHI": "europe",
    # Asian indices
    "^N225": "asia", "^HSI": "asia", "000001.SS": "asia",
    "^KS11": "asia", "^NSEI": "asia", "^AXJO": "asia", "^TWII": "asia",
}


def is_24_hour_market(symbol: str) -> bool:
    """Check if symbol trades 24 hours (crypto, futures)"""
    return symbol in TWENTY_FOUR_HOUR_SYMBOLS


def get_cache_expiry(symbol: str) -> datetime:
    """Get cache expiry time for symbol based on market type.

    Uses region-aware session hours so global indices expire when their
    local market reopens, not when the US market reopens.
    """
    now = datetime.now(ZoneInfo("America/New_York"))

    if symbol in FUTURES_SYMBOLS:
        return now + timedelta(seconds=FUTURES_TTL_SECONDS)
    if is_24_hour_market(symbol):
        return now + timedelta(seconds=CRYPTO_TTL_SECONDS)

    # Determine which session governs this symbol
    region = SYMBOL_REGION.get(symbol, "us")

    if region == "europe":
        is_open = is_europe_market_open()
        get_next_open = get_next_europe_open
    elif region == "asia":
        is_open = is_asia_market_open()
        get_next_open = get_next_asia_open
    else:
        is_open = is_market_open()
        get_next_open = get_next_us_open

    if is_open:
        return now + timedelta(seconds=120)
    return get_next_open()


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
        market_type = SYMBOL_REGION.get(symbol, "us")
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
        market_type = SYMBOL_REGION.get(symbol, "us")
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
