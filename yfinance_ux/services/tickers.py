"""
Ticker screen data services.

Comprehensive ticker analysis: price, factors, valuation, technicals, calendar, options.
Supports both single and batch fetching (batch uses yf.Tickers for efficiency).
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.momentum import calculate_momentum
from yfinance_ux.calculations.technical import calculate_rsi
from yfinance_ux.calculations.volatility import calculate_idio_vol
from yfinance_ux.common.constants import RSI_PERIOD
from yfinance_ux.common.dates import is_market_open
from yfinance_ux.common.symbols import normalize_ticker_symbol
from yfinance_ux.services.options import get_options_data


def get_ticker_screen_data(symbol: str) -> dict[str, Any]:
    """Fetch comprehensive ticker data for ticker() screen

    RVOL Time Window: Uses 3-month average (info.averageVolume)
    - Rationale: FREE - already fetching info for P/E, market cap, earnings, etc.
    - Purpose: Detailed analysis with stable baseline to filter noise
    - Trade-off: Less sensitive to recent shifts, but more reliable context

    Note: markets() screen uses 10-day average (fast_info.tenDayAverageVolume) for quick scans.
    Different time windows serve different purposes - this is intentional, not a bug!
    """
    try:
        symbol = normalize_ticker_symbol(symbol)
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Basic price data
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        change = info.get("regularMarketChange")
        change_pct = info.get("regularMarketChangePercent")
        market_cap = info.get("marketCap")
        volume = info.get("volume")
        avg_volume = info.get("averageVolume")  # 3-month avg (FREE with info call)
        name = info.get("longName") or info.get("shortName") or symbol

        # Volume analytics - extrapolate intraday volume
        # During market hours, raw volume is partial (e.g., 2hrs into 6.5hr day).
        # Comparing 20M shares at 11am to 80M average is misleading (0.25x).
        # Extrapolate to full day: 20M / (2/6.5) = 65M → 0.81x (more accurate).
        rel_volume = None
        if volume is not None and avg_volume is not None and avg_volume > 0:
            # During market hours: extrapolate partial volume to full day
            if is_market_open():
                now = datetime.now(ZoneInfo("America/New_York"))
                market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

                if now > market_open:
                    elapsed = (now - market_open).total_seconds()
                    total_seconds = (market_close - market_open).total_seconds()
                    fraction = min(elapsed / total_seconds, 1.0)

                    # Extrapolate if we're at least 10% into the day
                    if fraction > 0.1:
                        extrapolated_volume = volume / fraction
                        rel_volume = extrapolated_volume / avg_volume
                    else:
                        rel_volume = volume / avg_volume
                else:
                    rel_volume = volume / avg_volume
            else:
                # After hours: use today's volume as-is
                rel_volume = volume / avg_volume

        # Factor exposures
        beta_spx = info.get("beta")

        # Valuation
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        dividend_yield = info.get("dividendYield")

        # Short interest (positioning)
        short_pct_float = info.get("shortPercentOfFloat")
        short_ratio = info.get("shortRatio")

        # Technicals
        fifty_day_avg = info.get("fiftyDayAverage")
        two_hundred_day_avg = info.get("twoHundredDayAverage")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        fifty_two_week_low = info.get("fiftyTwoWeekLow")

        # Get momentum
        momentum = calculate_momentum(symbol)

        # Get idio vol
        vol_data = calculate_idio_vol(symbol)

        # Calculate RSI and volume momentum
        rsi = None
        vol_momentum_1w = None
        try:
            hist = ticker.history(period="1mo", interval="1d")
            if not hist.empty and len(hist) >= RSI_PERIOD:
                rsi = calculate_rsi(hist["Close"])

                # Calculate volume momentum (1W = 5 trading days)
                # Shows if volume is trending up/down vs recent activity
                # - Positive: Volume increasing (activity picking up)
                # - Negative: Volume decreasing (cooling off)
                # - Complements rel_volume: rel_volume = long-term context (vs 3mo avg)
                #                           vol_momentum = short-term trend (vs last week)
                # Example: (0.93x 3mo, +33% 1W) = near average overall, but heating up recently
                if "Volume" in hist.columns and len(hist) >= 6:
                    recent_vol = hist["Volume"].iloc[-1]  # Today
                    week_ago_vol = hist["Volume"].iloc[-6]  # 5 trading days ago
                    if week_ago_vol > 0:
                        vol_momentum_1w = ((recent_vol - week_ago_vol) / week_ago_vol) * 100
        except Exception:
            pass

        # Get calendar data (earnings and dividend dates)
        calendar = None
        try:  # noqa: SIM105
            calendar = ticker.calendar
        except Exception:
            pass  # Calendar not available for non-stocks (indices, ETFs, etc.)

        # Get options data
        options_data = get_options_data(symbol, "nearest")

        # Get insider transactions
        insider_transactions = None
        try:
            insider_df = ticker.insider_transactions
            if not insider_df.empty:
                # Get most recent 10 transactions
                insider_transactions = insider_df.head(10).to_dict('records')
        except Exception:
            pass

        # Get analyst data
        analyst_recommendations = None
        analyst_price_targets = None
        try:
            # Recommendations summary (current month)
            recs = ticker.recommendations
            if recs is not None and not recs.empty:
                analyst_recommendations = recs.iloc[0].to_dict()
        except Exception:
            pass

        try:
            # Price targets consensus
            analyst_price_targets = ticker.analyst_price_targets
        except Exception:
            pass

        # Get earnings history
        earnings_history = None
        try:
            earnings_df = ticker.earnings_history
            if not earnings_df.empty:
                # Get last 4 quarters, reset index to include quarter date
                earnings_history = (
                    earnings_df.tail(4).reset_index().to_dict('records')
                )
        except Exception:
            pass

        # Get recent upgrades/downgrades (last 10)
        recent_upgrades = None
        try:
            upgrades_df = ticker.upgrades_downgrades
            if upgrades_df is not None and not upgrades_df.empty:
                recent_upgrades = upgrades_df.head(10).reset_index().to_dict('records')
        except Exception:
            pass

        return {
            "symbol": symbol,
            "name": name,
            "price": price,
            "change": change,
            "change_percent": change_pct,
            "market_cap": market_cap,
            "volume": volume,
            "avg_volume": avg_volume,
            "rel_volume": rel_volume,
            "vol_momentum_1w": vol_momentum_1w,
            "beta_spx": beta_spx,
            "trailing_pe": trailing_pe,
            "forward_pe": forward_pe,
            "dividend_yield": dividend_yield,
            "short_pct_float": short_pct_float,
            "short_ratio": short_ratio,
            "fifty_day_avg": fifty_day_avg,
            "two_hundred_day_avg": two_hundred_day_avg,
            "fifty_two_week_high": fifty_two_week_high,
            "fifty_two_week_low": fifty_two_week_low,
            "momentum_1w": momentum.get("momentum_1w"),
            "momentum_1m": momentum.get("momentum_1m"),
            "momentum_1y": momentum.get("momentum_1y"),
            "idio_vol": vol_data.get("idio_vol"),
            "total_vol": vol_data.get("total_vol"),
            "rsi": rsi,
            "calendar": calendar,
            "options_data": options_data,
            "insider_transactions": insider_transactions,
            "analyst_recommendations": analyst_recommendations,
            "analyst_price_targets": analyst_price_targets,
            "earnings_history": earnings_history,
            "recent_upgrades": recent_upgrades,
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def get_ticker_screen_data_batch(symbols: list[str]) -> list[dict[str, Any]]:
    """Fetch comprehensive ticker data for multiple symbols using batch API"""
    if not symbols:
        return []

    # Normalize all symbols
    symbols = [normalize_ticker_symbol(s) for s in symbols]

    # Batch fetch all tickers at once (single request to Yahoo, not N separate requests)
    tickers_obj = yf.Tickers(" ".join(symbols))

    results = []
    for symbol in symbols:
        try:
            ticker_obj = tickers_obj.tickers[symbol]
            info = ticker_obj.info

            # Basic price data
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            change = info.get("regularMarketChange")
            change_pct = info.get("regularMarketChangePercent")
            market_cap = info.get("marketCap")
            volume = info.get("volume")
            avg_volume = info.get("averageVolume")
            name = info.get("longName") or info.get("shortName") or symbol

            # Volume analytics - extrapolate intraday volume
            # During market hours, raw volume is partial (e.g., 2hrs into 6.5hr day).
            # Comparing 20M shares at 11am to 80M average is misleading (0.25x).
            # Extrapolate to full day: 20M / (2/6.5) = 65M → 0.81x (more accurate).
            rel_volume = None
            if volume is not None and avg_volume is not None and avg_volume > 0:
                # During market hours: extrapolate partial volume to full day
                if is_market_open():
                    now = datetime.now(ZoneInfo("America/New_York"))
                    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

                    if now > market_open:
                        elapsed = (now - market_open).total_seconds()
                        total_seconds = (market_close - market_open).total_seconds()
                        fraction = min(elapsed / total_seconds, 1.0)

                        # Extrapolate if we're at least 10% into the day
                        if fraction > 0.1:
                            extrapolated_volume = volume / fraction
                            rel_volume = extrapolated_volume / avg_volume
                        else:
                            rel_volume = volume / avg_volume
                    else:
                        rel_volume = volume / avg_volume
                else:
                    # After hours: use today's volume as-is
                    rel_volume = volume / avg_volume

            # Factor exposures
            beta_spx = info.get("beta")

            # Valuation
            trailing_pe = info.get("trailingPE")
            forward_pe = info.get("forwardPE")
            dividend_yield = info.get("dividendYield")

            # Short interest (positioning)
            short_pct_float = info.get("shortPercentOfFloat")
            short_ratio = info.get("shortRatio")

            # Technicals
            fifty_day_avg = info.get("fiftyDayAverage")
            two_hundred_day_avg = info.get("twoHundredDayAverage")
            fifty_two_week_high = info.get("fiftyTwoWeekHigh")
            fifty_two_week_low = info.get("fiftyTwoWeekLow")

            # Get momentum
            momentum = calculate_momentum(symbol)

            # Get idio vol
            vol_data = calculate_idio_vol(symbol)

            # Calculate RSI and volume momentum
            rsi = None
            vol_momentum_1w = None
            try:
                hist = ticker_obj.history(period="1mo", interval="1d")
                if not hist.empty and len(hist) >= RSI_PERIOD:
                    rsi = calculate_rsi(hist["Close"])

                    # Calculate volume momentum (1W = 5 trading days)
                    # Shows if volume is trending up/down vs recent activity
                    # - Positive: Volume increasing (activity picking up)
                    # - Negative: Volume decreasing (cooling off)
                    # - Complements rel_volume: rel_volume = long-term context (vs 3mo avg)
                    #                           vol_momentum = short-term trend (vs last week)
                    # Example: (0.93x 3mo, +33% 1W) = near average overall, but heating up recently
                    if "Volume" in hist.columns and len(hist) >= 6:
                        recent_vol = hist["Volume"].iloc[-1]  # Today
                        week_ago_vol = hist["Volume"].iloc[-6]  # 5 trading days ago
                        if week_ago_vol > 0:
                            vol_momentum_1w = ((recent_vol - week_ago_vol) / week_ago_vol) * 100
            except Exception:
                pass

            # Get calendar data (earnings and dividend dates)
            calendar = None
            try:  # noqa: SIM105
                calendar = ticker_obj.calendar
            except Exception:
                pass  # Calendar not available for non-stocks (indices, ETFs, etc.)

            results.append({
                "symbol": symbol,
                "name": name,
                "price": price,
                "change": change,
                "change_percent": change_pct,
                "market_cap": market_cap,
                "volume": volume,
                "avg_volume": avg_volume,
                "rel_volume": rel_volume,
                "vol_momentum_1w": vol_momentum_1w,
                "beta_spx": beta_spx,
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "dividend_yield": dividend_yield,
                "short_pct_float": short_pct_float,
                "short_ratio": short_ratio,
                "fifty_day_avg": fifty_day_avg,
                "two_hundred_day_avg": two_hundred_day_avg,
                "fifty_two_week_high": fifty_two_week_high,
                "fifty_two_week_low": fifty_two_week_low,
                "momentum_1w": momentum.get("momentum_1w"),
                "momentum_1m": momentum.get("momentum_1m"),
                "momentum_1y": momentum.get("momentum_1y"),
                "idio_vol": vol_data.get("idio_vol"),
                "total_vol": vol_data.get("total_vol"),
                "rsi": rsi,
                "calendar": calendar,
            })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return results
