"""
Ticker screen data services.

Comprehensive ticker analysis: price, factors, valuation, technicals, calendar, options.
Supports both single and batch fetching (batch uses yf.Tickers for efficiency).
"""

from typing import Any

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.momentum import calculate_momentum
from yfinance_ux.calculations.technical import calculate_rsi
from yfinance_ux.calculations.volatility import calculate_idio_vol
from yfinance_ux.common.constants import RSI_PERIOD
from yfinance_ux.common.symbols import normalize_ticker_symbol
from yfinance_ux.services.options import get_options_data


def get_ticker_screen_data(symbol: str) -> dict[str, Any]:
    """Fetch comprehensive ticker data for ticker() screen"""
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
        name = info.get("longName") or info.get("shortName") or symbol

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

        # Calculate RSI
        rsi = None
        try:
            hist = ticker.history(period="1mo", interval="1d")
            if not hist.empty and len(hist) >= RSI_PERIOD:
                rsi = calculate_rsi(hist["Close"])
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
            name = info.get("longName") or info.get("shortName") or symbol

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

            # Calculate RSI
            rsi = None
            try:
                hist = ticker_obj.history(period="1mo", interval="1d")
                if not hist.empty and len(hist) >= RSI_PERIOD:
                    rsi = calculate_rsi(hist["Close"])
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
