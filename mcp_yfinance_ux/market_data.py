"""
Core market data functionality - yfinance business logic
Testable independently of MCP protocol layer

Adds caching layer on top of yfinance_ux services for production use.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from mcp_yfinance_ux.cache import get_cached_data, set_cached_data
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
from mcp_yfinance_ux.logging_config import get_logger
from yfinance_ux.services.markets import (
    get_market_snapshot,
    get_ticker_data,
    get_ticker_history,
)
from yfinance_ux.services.markets import (
    get_ticker_full_data as _get_ticker_full_data_uncached,
)
from yfinance_ux.services.options import get_options_data
from yfinance_ux.services.sectors import get_sector_data
from yfinance_ux.services.tickers import (
    get_ticker_screen_data as _get_ticker_screen_data_uncached,
)
from yfinance_ux.services.tickers import (
    get_ticker_screen_data_batch as _get_ticker_screen_data_batch_uncached,
)

logger = get_logger(__name__)


def get_ticker_full_data(symbol: str, _stats: dict[str, int] | None = None) -> dict[str, Any]:
    """Cached wrapper for get_ticker_full_data with market-aware TTL

    Caching strategy:
    - 24-hour markets (crypto, futures): 2 min cache
    - Session markets (equities, ETFs, indices): cache until next market open

    After market close, session-based symbols use cached data (prices won't change).
    24-hour markets always fetch fresh data with short TTL.
    """
    # Check cache first
    cached = get_cached_data(symbol)
    if cached is not None:
        if _stats is not None:
            _stats["hits"] = _stats.get("hits", 0) + 1
        return cached

    # Cache miss - fetch fresh data
    if _stats is not None:
        _stats["misses"] = _stats.get("misses", 0) + 1

    data = _get_ticker_full_data_uncached(symbol)

    # Cache the result (skip if error)
    if "error" not in data:
        set_cached_data(symbol, data)

    return data


def get_markets_data() -> dict[str, dict[str, Any]]:
    """Fetch all market data for markets() screen with caching

    Uses cached version of get_ticker_full_data to avoid unnecessary API calls
    for closed markets while keeping 24-hour markets fresh.
    """
    # Complete symbol list for markets() screen
    symbols_to_fetch = [
        # US Equities (cash indices)
        ("sp500", "^GSPC"),
        ("nasdaq", "^IXIC"),
        ("dow", "^DJI"),
        ("russell2000", "^RUT"),
        # US Futures
        ("es_futures", "ES=F"),
        ("nq_futures", "NQ=F"),
        ("ym_futures", "YM=F"),
        # Global - Asia/Pacific
        ("nikkei", "^N225"),
        ("hangseng", "^HSI"),
        ("shanghai", "000001.SS"),
        ("kospi", "^KS11"),
        ("nifty50", "^NSEI"),
        ("asx200", "^AXJO"),
        ("taiwan", "^TWII"),
        # Global - Europe
        ("stoxx50", "^STOXX50E"),
        # Global - Latin America
        ("bovespa", "^BVSP"),
        # Crypto
        ("btc", "BTC-USD"),
        ("eth", "ETH-USD"),
        ("sol", "SOL-USD"),
        # Sectors (all 11 GICS)
        ("tech", "XLK"),
        ("financials", "XLF"),
        ("healthcare", "XLV"),
        ("energy", "XLE"),
        ("consumer_disc", "XLY"),
        ("consumer_stpl", "XLP"),
        ("industrials", "XLI"),
        ("utilities", "XLU"),
        ("materials", "XLB"),
        ("real_estate", "XLRE"),
        ("communication", "XLC"),
        # Styles
        ("momentum", "MTUM"),
        ("value", "VTV"),
        ("growth", "VUG"),
        ("quality", "QUAL"),
        ("small_cap", "IWM"),
        # Private Credit
        ("private_credit", "BIZD"),
        # Commodities
        ("gold", "GC=F"),
        ("silver", "SI=F"),
        ("platinum", "PL=F"),
        ("copper", "HG=F"),
        ("oil_wti", "CL=F"),
        ("natgas", "NG=F"),
        # Volatility & Rates
        ("vix", "^VIX"),
        ("us10y", "^TNX"),
    ]

    # Track cache performance
    stats: dict[str, int] = {"hits": 0, "misses": 0}

    # Fetch in parallel using cached wrapper
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_key = {
            executor.submit(get_ticker_full_data, symbol, stats): key
            for key, symbol in symbols_to_fetch
        }

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"symbol": key, "error": str(e)}

    # Log cache performance summary
    total = stats["hits"] + stats["misses"]
    hit_rate = (stats["hits"] / total * 100) if total > 0 else 0
    logger.info(
        f"markets() cache stats: {stats['hits']}/{total} hits ({hit_rate:.0f}%), "
        f"{stats['misses']} API calls"
    )

    return results


def get_ticker_screen_data(symbol: str) -> dict[str, Any]:
    """Cached wrapper for get_ticker_screen_data with market-aware TTL

    Caching strategy (same as markets):
    - Futures: 30 sec cache (very active)
    - Crypto: 2 min cache
    - Session markets: cache until next market open

    After market close, session-based symbols use cached data (prices/data won't change).
    """
    # Check cache first
    cached = get_cached_data(symbol)
    if cached is not None:
        logger.debug(f"ticker({symbol}) cache hit")
        return cached

    # Cache miss - fetch fresh data
    logger.debug(f"ticker({symbol}) cache miss - fetching from yfinance")
    data = _get_ticker_screen_data_uncached(symbol)

    # Cache the result (skip if error)
    if "error" not in data:
        set_cached_data(symbol, data)

    return data


def get_ticker_screen_data_batch(symbols: list[str]) -> list[dict[str, Any]]:
    """Cached wrapper for get_ticker_screen_data_batch

    Checks cache for each symbol individually before fetching.
    Only uncached symbols are fetched from yfinance.
    """
    if not symbols:
        return []

    results = []
    uncached_symbols = []

    # Check cache for each symbol
    for symbol in symbols:
        cached = get_cached_data(symbol)
        if cached is not None:
            logger.debug(f"ticker({symbol}) cache hit in batch")
            results.append(cached)
        else:
            logger.debug(f"ticker({symbol}) cache miss in batch")
            uncached_symbols.append(symbol)

    # Fetch uncached symbols
    if uncached_symbols:
        logger.info(f"ticker() batch: {len(uncached_symbols)}/{len(symbols)} cache misses")
        fresh_data = _get_ticker_screen_data_batch_uncached(uncached_symbols)

        # Cache and add to results
        for data in fresh_data:
            if "error" not in data:
                set_cached_data(data["symbol"], data)
            results.append(data)
    else:
        logger.info(f"ticker() batch: {len(symbols)}/{len(symbols)} cache hits (100%)")

    return results


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
