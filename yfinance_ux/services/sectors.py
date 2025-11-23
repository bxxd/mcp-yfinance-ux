"""
Sector data fetching service.

Fetches sector ETF data and top holdings with performance metrics.
Uses parallel fetching for holdings data.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.momentum import calculate_momentum
from yfinance_ux.common.constants import DISPLAY_NAMES, MARKET_SYMBOLS
from yfinance_ux.services.markets import get_ticker_full_data


def get_sector_data(name: str) -> dict[str, Any]:
    """Fetch sector data for sector() screen"""
    # Normalize sector name: "real estate" -> "real_estate", "technology" -> "tech"
    sector_key = name.lower().replace(" ", "_")

    # Map display names to keys
    name_to_key = {
        "technology": "tech",
        "consumer discretionary": "consumer_disc",
        "consumer staples": "consumer_stpl",
    }

    # Try direct lookup first, then mapping
    if sector_key in name_to_key:
        sector_key = name_to_key[sector_key]

    # Get sector ETF symbol
    sector_symbol = MARKET_SYMBOLS.get(sector_key)
    if not sector_symbol:
        return {"error": f"Unknown sector: {name}"}

    # Get sector ETF data
    sector_data = get_ticker_full_data(sector_symbol)

    # Get top holdings with performance data (using yfinance batch API to avoid hammering server)
    try:
        ticker = yf.Ticker(sector_symbol)
        holdings_df = ticker.funds_data.top_holdings

        # Get list of symbols for parallel fetch
        symbols = list(holdings_df.head(10).index)

        # Fetch all holdings data in parallel using ThreadPoolExecutor
        def fetch_holding_data(symbol: str) -> dict[str, Any]:
            """Fetch price and momentum data for a single holding"""
            try:
                ticker = yf.Ticker(symbol)

                # Use fast_info instead of info (much faster)
                price = ticker.fast_info.get("lastPrice")
                prev_close = ticker.fast_info.get("previousClose")

                # Calculate change percent
                change_pct = None
                if price is not None and prev_close is not None and prev_close != 0:
                    change_pct = ((price - prev_close) / prev_close) * 100

                # Use optimized momentum calculation (narrow windows, not full year)
                momentum = calculate_momentum(symbol)

                return {
                    "change_percent": change_pct,
                    "momentum_1m": momentum.get("momentum_1m"),
                    "momentum_1y": momentum.get("momentum_1y"),
                }
            except Exception:
                return {
                    "change_percent": None,
                    "momentum_1m": None,
                    "momentum_1y": None,
                }

        # Parallel fetch with ThreadPoolExecutor (10 concurrent requests)
        performance_data: dict[str, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {
                executor.submit(fetch_holding_data, symbol): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    performance_data[symbol] = future.result()
                except Exception:
                    performance_data[symbol] = {
                        "change_percent": None,
                        "momentum_1m": None,
                        "momentum_1y": None,
                    }

        # Build holdings list with performance data
        holdings = []
        for symbol_idx, row in holdings_df.head(10).iterrows():
            perf = performance_data.get(symbol_idx, {})
            holdings.append({
                "symbol": symbol_idx,
                "name": row["Name"],
                "weight": row["Holding Percent"],
                "change_percent": perf.get("change_percent"),
                "momentum_1m": perf.get("momentum_1m"),
                "momentum_1y": perf.get("momentum_1y"),
            })
    except Exception:
        holdings = []

    return {
        "sector_key": sector_key,
        "sector_name": DISPLAY_NAMES.get(sector_key, sector_key),
        "sector_symbol": sector_symbol,
        "sector_data": sector_data,
        "holdings": holdings,
    }
