"""
Options chain data service.

Comprehensive options analysis: positioning, IV structure, term structure,
unusual activity, max pain calculation, historical IV context, greeks.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import yfinance as yf  # type: ignore[import-untyped]

from yfinance_ux.calculations.greeks import calculate_greeks
from yfinance_ux.common.symbols import normalize_ticker_symbol


def get_risk_free_rate() -> float:
    """
    Fetch 10Y Treasury yield as risk-free rate.

    Returns:
        Risk-free rate as decimal (0.045 = 4.5%)
    """
    try:
        tnx = yf.Ticker("^TNX")
        # TNX is in %, convert to decimal
        rate = tnx.fast_info.get("lastPrice", 4.5) / 100
        return float(rate)
    except Exception:
        return 0.045  # Fallback to 4.5%


def get_options_data(symbol: str, expiration: str = "nearest") -> dict[str, Any]:  # noqa: PLR0915, PLR0912
    """
    Fetch options chain data for a symbol.

    Args:
        symbol: Ticker symbol (e.g., 'PALL', 'AAPL')
        expiration: 'nearest' or specific date like '2025-11-21'

    Returns:
        dict with options positioning, IV structure, term structure
    """
    symbol = normalize_ticker_symbol(symbol)
    try:
        ticker = yf.Ticker(symbol)

        # Get available expiration dates
        expirations = ticker.options  # List of date strings
        if not expirations:
            return {"error": f"No options data available for {symbol}"}

        # Select expiration
        exp_date = expirations[0] if expiration == "nearest" else expiration
        if exp_date not in expirations:
            return {"error": f"Expiration {expiration} not available"}

        # Fetch option chain
        chain = ticker.option_chain(exp_date)
        calls = chain.calls
        puts = chain.puts

        # Check if we have options data
        if calls.empty or puts.empty:
            return {"error": f"No options data available for {symbol} expiration {exp_date}"}

        # Fill NaN volumes with 0 (some illiquid options have NaN volume)
        calls["volume"] = calls["volume"].fillna(0)
        puts["volume"] = puts["volume"].fillna(0)

        # Current price (for ATM calculation)
        current_price = ticker.fast_info.get("lastPrice", 0)

        # Get risk-free rate and dividend yield for greeks calculation
        risk_free_rate = get_risk_free_rate()
        dividend_yield = ticker.info.get("dividendYield", 0.0) or 0.0

        # Days to expiration
        exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        )
        now = datetime.now(ZoneInfo("America/New_York"))
        dte = (exp_datetime - now).days
        time_to_expiry = max(dte / 365.0, 0.001)  # Prevent division by zero

        # Calculate greeks for each option
        def add_greeks(row: Any, option_type: str) -> Any:
            """Add greeks to option row."""
            try:
                greeks = calculate_greeks(
                    spot=current_price,
                    strike=row["strike"],
                    time_to_expiry=time_to_expiry,
                    volatility=row["impliedVolatility"],
                    risk_free_rate=risk_free_rate,
                    dividend_yield=dividend_yield,
                    option_type=option_type,
                )
                row["delta"] = greeks["delta"]
                row["gamma"] = greeks["gamma"]
                row["vega"] = greeks["vega"]
                row["theta"] = greeks["theta"]
                row["rho"] = greeks["rho"]
            except Exception:
                row["delta"] = 0.0
                row["gamma"] = 0.0
                row["vega"] = 0.0
                row["theta"] = 0.0
                row["rho"] = 0.0
            return row

        calls = calls.apply(lambda row: add_greeks(row, "call"), axis=1)
        puts = puts.apply(lambda row: add_greeks(row, "put"), axis=1)

        # Calculate positioning metrics
        call_oi_total = int(calls["openInterest"].sum())
        put_oi_total = int(puts["openInterest"].sum())
        pc_ratio_oi = put_oi_total / call_oi_total if call_oi_total > 0 else 0

        call_volume_total = int(calls["volume"].sum())
        put_volume_total = int(puts["volume"].sum())
        pc_ratio_vol = put_volume_total / call_volume_total if call_volume_total > 0 else 0

        # Find ATM strike (closest to current price)
        atm_strike = calls["strike"].iloc[(calls["strike"] - current_price).abs().argsort()[0]]

        # Get ATM IV and greeks
        atm_call_row = calls[calls["strike"] == atm_strike]
        atm_put_row = puts[puts["strike"] == atm_strike]

        atm_call_iv = float(atm_call_row["impliedVolatility"].values[0] * 100)
        atm_put_iv = float(atm_put_row["impliedVolatility"].values[0] * 100)

        # ATM greeks
        atm_call_greeks = {
            "delta": float(atm_call_row["delta"].values[0]),
            "gamma": float(atm_call_row["gamma"].values[0]),
            "vega": float(atm_call_row["vega"].values[0]),
            "theta": float(atm_call_row["theta"].values[0]),
        }
        atm_put_greeks = {
            "delta": float(atm_put_row["delta"].values[0]),
            "gamma": float(atm_put_row["gamma"].values[0]),
            "vega": float(atm_put_row["vega"].values[0]),
            "theta": float(atm_put_row["theta"].values[0]),
        }

        # Top positions by OI (expand to 10)
        top_calls_oi = calls.nlargest(10, "openInterest")[
            ["strike", "openInterest", "volume", "lastPrice", "impliedVolatility",
             "delta", "gamma", "vega", "theta"]
        ].copy()
        top_puts_oi = puts.nlargest(10, "openInterest")[
            ["strike", "openInterest", "volume", "lastPrice", "impliedVolatility",
             "delta", "gamma", "vega", "theta"]
        ].copy()

        # Top positions by volume
        top_calls_vol = calls.nlargest(10, "volume")[
            ["strike", "openInterest", "volume", "lastPrice", "impliedVolatility",
             "delta", "gamma", "vega", "theta"]
        ].copy()
        top_puts_vol = puts.nlargest(10, "volume")[
            ["strike", "openInterest", "volume", "lastPrice", "impliedVolatility",
             "delta", "gamma", "vega", "theta"]
        ].copy()

        # ITM vs OTM breakdown
        calls_itm = calls[calls["strike"] < current_price]
        calls_otm = calls[calls["strike"] >= current_price]
        puts_itm = puts[puts["strike"] > current_price]
        puts_otm = puts[puts["strike"] <= current_price]

        call_oi_itm = int(calls_itm["openInterest"].sum())
        call_oi_otm = int(calls_otm["openInterest"].sum())
        put_oi_itm = int(puts_itm["openInterest"].sum())
        put_oi_otm = int(puts_otm["openInterest"].sum())

        # Vol skew (OTM vs ATM)
        otm_put_strikes = puts[puts["strike"] < current_price * 0.9]
        otm_call_strikes = calls[calls["strike"] > current_price * 1.1]

        otm_put_iv_avg = (
            float(otm_put_strikes["impliedVolatility"].mean() * 100)
            if len(otm_put_strikes) > 0
            else atm_put_iv
        )
        otm_call_iv_avg = (
            float(otm_call_strikes["impliedVolatility"].mean() * 100)
            if len(otm_call_strikes) > 0
            else atm_call_iv
        )

        put_skew = otm_put_iv_avg - atm_put_iv
        call_skew = otm_call_iv_avg - atm_call_iv

        # Term structure (if multiple expirations available)
        term_structure = []
        if len(expirations) >= 3:  # noqa: PLR2004
            for exp in expirations[:3]:  # Near, mid, far
                chain_exp = ticker.option_chain(exp)
                calls_exp = chain_exp.calls
                atm_exp = calls_exp["strike"].iloc[
                    (calls_exp["strike"] - current_price).abs().argsort()[0]
                ]
                atm_row_exp = calls_exp[calls_exp["strike"] == atm_exp]
                iv_exp = float(atm_row_exp["impliedVolatility"].values[0] * 100)

                # Days to expiration
                exp_datetime = datetime.strptime(exp, "%Y-%m-%d").replace(
                    tzinfo=ZoneInfo("America/New_York")
                )
                now = datetime.now(ZoneInfo("America/New_York"))
                dte = (exp_datetime - now).days

                term_structure.append({"expiration": exp, "dte": dte, "iv": iv_exp})

        contango = (
            term_structure[0]["iv"] - term_structure[-1]["iv"]
            if len(term_structure) >= 2  # noqa: PLR2004
            else 0
        )

        # All expirations summary
        all_expirations = []
        for exp in expirations:
            try:
                chain_exp = ticker.option_chain(exp)
                calls_exp = chain_exp.calls
                puts_exp = chain_exp.puts

                # Fill NaN volumes with 0
                calls_exp["volume"] = calls_exp["volume"].fillna(0)
                puts_exp["volume"] = puts_exp["volume"].fillna(0)

                # ATM IV for this expiration
                atm_exp = calls_exp["strike"].iloc[
                    (calls_exp["strike"] - current_price).abs().argsort()[0]
                ]
                atm_row_exp = calls_exp[calls_exp["strike"] == atm_exp]
                iv_exp = float(atm_row_exp["impliedVolatility"].values[0] * 100)

                # OI for this expiration
                call_oi_exp = int(calls_exp["openInterest"].sum())
                put_oi_exp = int(puts_exp["openInterest"].sum())
                total_oi_exp = call_oi_exp + put_oi_exp

                # Volume for this expiration
                call_vol_exp = int(calls_exp["volume"].sum())
                put_vol_exp = int(puts_exp["volume"].sum())
                total_vol_exp = call_vol_exp + put_vol_exp

                # DTE
                exp_datetime = datetime.strptime(exp, "%Y-%m-%d").replace(
                    tzinfo=ZoneInfo("America/New_York")
                )
                now = datetime.now(ZoneInfo("America/New_York"))
                dte_exp = (exp_datetime - now).days

                all_expirations.append({
                    "expiration": exp,
                    "dte": dte_exp,
                    "iv": iv_exp,
                    "total_oi": total_oi_exp,
                    "total_volume": total_vol_exp,
                    "call_oi": call_oi_exp,
                    "put_oi": put_oi_exp,
                })
            except Exception:
                continue

        # Max pain calculation (strike with most option seller pain)
        # Max pain = strike where sum of (calls ITM value + puts ITM value) is minimized
        max_pain_strike = 0
        min_pain_value = float("inf")

        for strike in sorted(set(calls["strike"]) | set(puts["strike"])):
            # Calculate pain for this strike
            call_pain = sum(
                max(0, strike - c_strike) * c_oi
                for c_strike, c_oi in zip(calls["strike"], calls["openInterest"], strict=False)
                if c_strike < strike
            )
            put_pain = sum(
                max(0, p_strike - strike) * p_oi
                for p_strike, p_oi in zip(puts["strike"], puts["openInterest"], strict=False)
                if p_strike > strike
            )
            total_pain = call_pain + put_pain

            if total_pain < min_pain_value:
                min_pain_value = total_pain
                max_pain_strike = strike

        # Unusual activity detection (volume >> OI)
        unusual_calls = calls[calls["volume"] > calls["openInterest"] * 2]
        unusual_puts = puts[puts["volume"] > puts["openInterest"] * 2]
        unusual_activity = len(unusual_calls) + len(unusual_puts) > 0

        # Historical IV (last 30 days) for IV rank/percentile
        # Fetch historical volatility data
        hist_iv_data = None
        try:
            hist = ticker.history(period="3mo", interval="1d")
            if not hist.empty and len(hist) >= 30:  # noqa: PLR2004
                # Calculate 30-day historical volatility
                returns = hist["Close"].pct_change().dropna()
                hist_vol_30d = float(returns.std() * (252 ** 0.5) * 100)

                # Calculate 52-week IV range (approximate from historical vol)
                hist_90d = ticker.history(period="1y", interval="1d")
                if not hist_90d.empty:
                    returns_1y = hist_90d["Close"].pct_change().dropna()
                    # Rolling 30-day volatility over 1 year
                    rolling_vol = returns_1y.rolling(30).std() * (252 ** 0.5) * 100
                    iv_high_52w = float(rolling_vol.max())
                    iv_low_52w = float(rolling_vol.min())

                    # IV rank (where current IV sits in 52-week range)
                    iv_rank = ((atm_call_iv - iv_low_52w) / (iv_high_52w - iv_low_52w) * 100
                               if iv_high_52w > iv_low_52w else 50)

                    hist_iv_data = {
                        "hist_vol_30d": hist_vol_30d,
                        "iv_high_52w": iv_high_52w,
                        "iv_low_52w": iv_low_52w,
                        "iv_rank": iv_rank,
                    }
        except Exception:
            pass

        # Days to expiration
        exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        )
        now = datetime.now(ZoneInfo("America/New_York"))
        dte = (exp_datetime - now).days

        # Timestamp
        now = datetime.now(ZoneInfo("America/New_York"))
        timestamp = now.strftime("%Y-%m-%d %H:%M %Z")

        return {
            "symbol": symbol,
            "current_price": float(current_price),
            "expiration": exp_date,
            "dte": dte,
            "atm_strike": float(atm_strike),
            # Positioning
            "call_oi_total": call_oi_total,
            "put_oi_total": put_oi_total,
            "pc_ratio_oi": pc_ratio_oi,
            "pc_ratio_vol": pc_ratio_vol,
            "call_volume_total": call_volume_total,
            "put_volume_total": put_volume_total,
            # ITM/OTM breakdown
            "call_oi_itm": call_oi_itm,
            "call_oi_otm": call_oi_otm,
            "put_oi_itm": put_oi_itm,
            "put_oi_otm": put_oi_otm,
            # IV
            "atm_call_iv": atm_call_iv,
            "atm_put_iv": atm_put_iv,
            "iv_spread": atm_call_iv - atm_put_iv,
            # Greeks
            "atm_call_greeks": atm_call_greeks,
            "atm_put_greeks": atm_put_greeks,
            # Skew
            "put_skew": put_skew,
            "call_skew": call_skew,
            # Top positions (OI and volume)
            "top_calls_oi": top_calls_oi,
            "top_puts_oi": top_puts_oi,
            "top_calls_vol": top_calls_vol,
            "top_puts_vol": top_puts_vol,
            # Term structure
            "term_structure": term_structure,
            "contango": contango,
            # All expirations
            "all_expirations": all_expirations,
            # Max pain
            "max_pain_strike": float(max_pain_strike),
            # Unusual activity
            "unusual_activity": unusual_activity,
            "unusual_calls": unusual_calls,
            "unusual_puts": unusual_puts,
            # Historical IV context
            "hist_iv_data": hist_iv_data,
            # Timestamp
            "timestamp": timestamp,
        }
    except Exception as e:
        return {"error": str(e)}
