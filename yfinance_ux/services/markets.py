"""
Market data fetching services.

Functions for fetching market overview data, ticker snapshots,
and parallel data fetching for multiple symbols.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd  # type: ignore[import-untyped]
import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.momentum import calculate_momentum
from yfinance_ux.calculations.volume import (
    calculate_relative_volume,
    calculate_relative_volume_futures,
)
from yfinance_ux.common.constants import (
    CATEGORY_MAPPING,
    HISTORY_INTERVALS,
    HISTORY_PERIODS,
    HISTORY_RVOL_LOOKBACK,
    HISTORY_RVOL_MIN_BARS,
    MARKET_SYMBOLS,
    MAX_HISTORY_ROWS,
    UNUSUAL_VOLUME_THRESHOLD,
)
from yfinance_ux.common.dates import is_market_open
from yfinance_ux.common.symbols import normalize_ticker_symbol

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

        # Volume analytics - extrapolate partial volume
        # Futures: extrapolate over 24h cycle (resets at 6pm settlement)
        # Session markets: extrapolate over 6.5h trading day (9:30am-4pm)
        if is_futures:
            rel_volume = calculate_relative_volume_futures(volume_today, avg_volume)
        else:
            rel_volume = calculate_relative_volume(volume_today, avg_volume)

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


def _is_bar_in_progress(bar_date: date, interval: str) -> bool:
    """True when the newest bar's period has not closed yet.

    A daily bar is in progress only while the session is open; a weekly or monthly
    bar is in progress for as long as it covers today.
    """
    today = datetime.now(ZoneInfo("America/New_York")).date()
    if interval == "1d":
        return bar_date == today and is_market_open()
    if interval == "1wk":
        return bar_date >= today - timedelta(days=today.weekday())
    return (bar_date.year, bar_date.month) == (today.year, today.month)


def get_ticker_history(  # noqa: PLR0911
    symbol: str,
    period: str = "3mo",
    interval: str = "auto",
) -> dict[str, Any]:
    """Fetch the OHLCV series and period stats behind the ticker_history() screen.

    RVOL is measured against the trailing HISTORY_RVOL_LOOKBACK bars, excluding
    the bar itself. That is why the fetch reaches back further than the display
    window: every displayed bar gets a fully seeded baseline instead of a ramp of
    blanks at the top of the screen.

    Args:
        symbol: Ticker symbol
        period: Display window - one of HISTORY_PERIODS
        interval: Bar size - "auto" (period default) or one of HISTORY_INTERVALS

    Returns:
        dict with bars + summary, or {"error": ...} on failure
    """
    symbol = normalize_ticker_symbol(symbol.strip().upper())

    if period not in HISTORY_PERIODS:
        valid = ", ".join(HISTORY_PERIODS)
        return {"symbol": symbol, "error": f"Unknown period '{period}'. Use one of: {valid}"}

    window_days, default_interval = HISTORY_PERIODS[period]
    if interval == "auto":
        interval = default_interval
    if interval not in HISTORY_INTERVALS:
        valid = ", ".join(HISTORY_INTERVALS)
        return {
            "symbol": symbol,
            "error": f"Unknown interval '{interval}'. Use 'auto' or one of: {valid}",
        }

    interval_label, pad_days = HISTORY_INTERVALS[interval]
    today = datetime.now(ZoneInfo("America/New_York")).date()
    window_start = today - timedelta(days=window_days)

    try:
        hist = yf.Ticker(symbol).history(
            start=window_start - timedelta(days=pad_days),
            end=today + timedelta(days=1),
            interval=interval,
        )
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

    if hist.empty:
        return {"symbol": symbol, "error": f"No historical data found for {symbol}"}

    closes = hist["Close"]
    volumes = hist["Volume"]
    change_pct = closes.pct_change() * 100

    # Baseline excludes the bar itself (shift), so RVOL reads "vs what came before"
    baseline = volumes.rolling(
        HISTORY_RVOL_LOOKBACK, min_periods=HISTORY_RVOL_MIN_BARS
    ).mean().shift(1)
    rvol = volumes / baseline.where(baseline > 0)

    window = [ts for ts in hist.index if ts.date() >= window_start]
    if not window:
        last = hist.index[-1].date()
        return {
            "symbol": symbol,
            "error": f"No {symbol} data inside the {period} window (last bar {last})",
        }

    shown = window[-MAX_HISTORY_ROWS:]
    bars = [
        {
            "date": ts.strftime("%Y-%m-%d"),
            "close": float(closes[ts]),
            "change_pct": None if pd.isna(change_pct[ts]) else float(change_pct[ts]),
            "volume": float(volumes[ts]),
            "rvol": None if pd.isna(rvol[ts]) else float(rvol[ts]),
            "partial": False,
        }
        for ts in shown
    ]

    # The newest bar may still be forming - today's session, this week, this month.
    # Its volume is a partial count, so RVOL reads low for reasons that have nothing
    # to do with participation. Flag it, and for an open daily bar reuse the intraday
    # extrapolation ticker() already applies.
    if _is_bar_in_progress(shown[-1].date(), interval):
        bars[-1]["partial"] = True
        if interval == "1d":
            bars[-1]["rvol"] = calculate_relative_volume(
                bars[-1]["volume"],
                None if pd.isna(baseline[shown[-1]]) else float(baseline[shown[-1]]),
            )

    unusual = [b for b in bars if b["rvol"] is not None and b["rvol"] > UNUSUAL_VOLUME_THRESHOLD]
    moves = [b for b in bars if b["change_pct"] is not None]
    high_ts = max(shown, key=lambda ts: hist["High"][ts])
    low_ts = min(shown, key=lambda ts: hist["Low"][ts])
    first_close, last_close = bars[0]["close"], bars[-1]["close"]

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "interval_label": interval_label,
        "bars": bars,
        "bars_available": len(window),
        "start_date": bars[0]["date"],
        "end_date": bars[-1]["date"],
        "summary": {
            "first_close": first_close,
            "last_close": last_close,
            "return_pct": ((last_close - first_close) / first_close * 100) if first_close else None,
            "high": float(hist["High"][high_ts]),
            "high_date": high_ts.strftime("%Y-%m-%d"),
            "low": float(hist["Low"][low_ts]),
            "low_date": low_ts.strftime("%Y-%m-%d"),
            "avg_volume": sum(b["volume"] for b in bars) / len(bars),
            "best": max(moves, key=lambda b: b["change_pct"]) if moves else None,
            "worst": min(moves, key=lambda b: b["change_pct"]) if moves else None,
            "unusual_count": len(unusual),
            "unusual_latest": unusual[-1] if unusual else None,
        },
    }


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
