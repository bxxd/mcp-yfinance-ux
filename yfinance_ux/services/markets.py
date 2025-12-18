"""
Market data fetching services.

Functions for fetching market overview data, ticker snapshots,
and parallel data fetching for multiple symbols.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.momentum import calculate_momentum
from yfinance_ux.common.constants import CATEGORY_MAPPING, MARKET_SYMBOLS
from yfinance_ux.common.dates import is_market_open

logger = logging.getLogger(__name__)


def get_ticker_data(symbol: str, include_momentum: bool = False) -> dict[str, Any]:
    """Fetch current data for a single ticker"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("regularMarketPrice") or info.get("currentPrice")
        change_pct = info.get("regularMarketChangePercent")

        result: dict[str, Any] = {
            "symbol": symbol,
            "price": price,
            "change_percent": change_pct,
        }

        # Add momentum data if requested
        if include_momentum:
            momentum = calculate_momentum(symbol)
            result.update(momentum)

        return result
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def get_ticker_full_data(symbol: str) -> dict[str, Any]:
    """Fetch comprehensive ticker data (price, momentum) for markets() screen using fast_info

    RVOL Time Window: Uses 10-day average (fast_info.tenDayAverageVolume)
    - Rationale: FREE - already fetching fast_info for price data, no extra API call
    - Purpose: Quick market scan to spot recent momentum shifts
    - Trade-off: More sensitive to recent quiet/hot periods vs longer baseline

    Note: ticker() screen uses 3-month average (info.averageVolume) for stable baseline.
    Different time windows serve different purposes - this is intentional, not a bug!
    """
    try:
        logger.debug(f"yfinance API call: yf.Ticker('{symbol}')")
        ticker = yf.Ticker(symbol)

        # Futures require special handling - fast_info.previousClose is wrong reference
        # Futures trade 24/7, so we need ticker.info.regularMarketChangePercent which
        # uses the correct 6pm ET settlement price as baseline
        is_futures = symbol.endswith("=F")

        if is_futures:
            # Use info for futures (slower but accurate)
            logger.debug(f"yfinance API call: {symbol}.info (futures)")
            info = ticker.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            change_pct = info.get("regularMarketChangePercent")
            avg_volume = info.get("averageVolume")
            volume_today = info.get("volume")
        else:
            # Use fast_info for equities/ETFs (faster)
            # tenDayAverageVolume comes FREE with this call - no extra API cost
            logger.debug(f"yfinance API call: {symbol}.fast_info")
            price = ticker.fast_info.get("lastPrice")
            prev_close = ticker.fast_info.get("previousClose")
            avg_volume = ticker.fast_info.get("tenDayAverageVolume")  # 10-day avg (FREE)
            volume_today = ticker.fast_info.get("lastVolume")

            # Calculate change percent from fast_info data
            change_pct = None
            if price is not None and prev_close is not None and prev_close != 0:
                change_pct = ((price - prev_close) / prev_close) * 100

        # Volume analytics - extrapolate today's partial volume during market hours
        rel_volume = None
        if volume_today is not None and avg_volume is not None and avg_volume > 0:
            # During market hours: extrapolate partial volume to full day
            if is_market_open() and not is_futures:
                now = datetime.now(ZoneInfo("America/New_York"))
                market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

                if now > market_open:
                    elapsed = (now - market_open).total_seconds()
                    total_seconds = (market_close - market_open).total_seconds()
                    fraction = min(elapsed / total_seconds, 1.0)

                    # Extrapolate if we're at least 10% into the day
                    if fraction > 0.1:
                        extrapolated_volume = volume_today / fraction
                        rel_volume = extrapolated_volume / avg_volume
            else:
                # After hours or futures: use today's volume as-is
                # (For futures, volume accumulates 24/7, so comparison is rough)
                rel_volume = volume_today / avg_volume

        # Get momentum (already optimized with narrow windows)
        momentum = calculate_momentum(symbol)

        logger.debug(f"yfinance API call SUCCESS: {symbol} (price={price}, change={change_pct:.2f}%)")
        return {
            "symbol": symbol,
            "price": price,
            "change_percent": change_pct,
            "rel_volume": rel_volume,
            "momentum_1m": momentum.get("momentum_1m"),
            "momentum_1y": momentum.get("momentum_1y"),
        }
    except Exception as e:
        logger.error(f"yfinance API call FAILED: {symbol} - {e}")
        return {"symbol": symbol, "error": str(e)}


def get_market_snapshot(
    categories: list[str],
    show_momentum: bool = False
) -> dict[str, dict[str, Any]]:
    """Get snapshot of multiple market categories"""
    # Auto-detect: if no categories specified, show comprehensive global view with factors
    if not categories:
        if is_market_open():
            categories = ["us", "volatility", "commodities", "rates", "sectors", "styles",
                         "crypto", "europe", "asia", "currencies"]
        else:
            categories = ["futures", "volatility", "commodities", "rates", "sectors", "styles",
                         "crypto", "europe", "asia", "currencies"]

    # Build symbol list based on categories
    symbols_to_fetch: list[str] = []
    for cat in categories:
        category = cat.lower()
        # Performance: O(1) dict lookup instead of if/elif chain
        if category in CATEGORY_MAPPING:
            symbols_to_fetch.extend(CATEGORY_MAPPING[category])
        elif category in MARKET_SYMBOLS:
            # Check if it's a specific symbol key
            symbols_to_fetch.append(category)

    # Build list of (key, symbol) pairs to fetch
    fetch_list = [
        (key, symbol)
        for key in symbols_to_fetch
        if (symbol := MARKET_SYMBOLS.get(key)) is not None
    ]

    # Fetch data in parallel using ThreadPoolExecutor
    # Performance: Parallel I/O (network requests) instead of sequential
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all fetch tasks
        future_to_key = {
            executor.submit(get_ticker_data, symbol, show_momentum): key
            for key, symbol in fetch_list
        }

        # Collect results as they complete
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"symbol": key, "error": str(e)}

    return results


def get_ticker_history(symbol: str, period: str = "1mo") -> dict[str, Any]:
    """Get historical price data for a ticker"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return {"error": f"No historical data found for {symbol}"}

        return {
            "symbol": symbol,
            "period": period,
            "data": hist.to_dict("records"),
            "start_date": hist.index[0].isoformat(),
            "end_date": hist.index[-1].isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_markets_data() -> dict[str, dict[str, Any]]:
    """Fetch all market data for markets() screen - complete market overview"""
    # Symbols to fetch - all market factors
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

    # Fetch in parallel
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_key = {
            executor.submit(get_ticker_full_data, symbol): key
            for key, symbol in symbols_to_fetch
        }

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"symbol": key, "error": str(e)}

    return results
