"""
Ticker formatters - BBG Lite style.

Formats ticker screens with factor exposures, valuation, technicals.
"""

from datetime import datetime
from typing import Any, TypeGuard
from zoneinfo import ZoneInfo

from yfinance_ux.common.constants import (
    BETA_HIGH_THRESHOLD,
    BETA_LOW_THRESHOLD,
    IDIO_VOL_HIGH_THRESHOLD,
    IDIO_VOL_LOW_THRESHOLD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
)


def is_numeric(value: object) -> TypeGuard[int | float]:
    """Check if value is a valid number (not None, not string like 'N/A')."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_options_summary(data: dict[str, Any]) -> str:
    """
    Format brief options summary for ticker() screen.

    Shows only key positioning metrics, not full analysis.
    """
    if "error" in data:
        return f"OPTIONS: No data available ({data['error']})"

    pc_oi = data["pc_ratio_oi"]
    atm_call_iv = data["atm_call_iv"]
    atm_put_iv = data["atm_put_iv"]
    exp = data["expiration"]
    dte = data["dte"]

    # Sentiment
    sentiment = "BULLISH" if pc_oi < 0.8 else "BEARISH" if pc_oi > 1.2 else "NEUTRAL"  # noqa: PLR2004

    lines = [
        "OPTIONS POSITIONING",
        f"P/C Ratio (OI):  {pc_oi:.2f}    ← {sentiment}",
        f"ATM IV:  {atm_call_iv:.1f}% (calls)  {atm_put_iv:.1f}% (puts)",
        f"Nearest Exp:  {exp} ({dte}d)",
    ]

    return "\n".join(lines)


def format_ticker(data: dict[str, Any]) -> str:  # noqa: PLR0912, PLR0915
    """Format ticker() screen - BBG Lite style with complete factor exposures"""
    if data.get("error"):
        return f"ERROR: {data['error']}"

    symbol = data["symbol"]
    name = data.get("name", symbol)
    price = data.get("price")
    change = data.get("change")
    change_pct = data.get("change_percent")
    market_cap = data.get("market_cap")
    volume = data.get("volume")

    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M %Z")

    lines = []

    # Header (simple title for panel)
    header = f"TICKER {symbol}"
    lines.append(header)
    lines.append("")  # Blank line after header

    # Price info + Company name on second line
    if price is not None and change is not None and change_pct is not None:
        lines.append(
            f"LAST PRICE  {price:.2f} {change:+.2f}  {change_pct:+.2f}%"
        )
    lines.append("")

    # Company name + Market cap/Volume
    if market_cap is not None and volume is not None:
        # Format market cap (billions)
        market_cap_b = market_cap / 1e9
        volume_m = volume / 1e6
        lines.append(f"{name[:40]:40} MKT CAP  {market_cap_b:6.1f}B    VOLUME {volume_m:5.1f}M")
    else:
        lines.append(name[:60])
    lines.append("")

    # Factor Exposures
    lines.append("FACTOR EXPOSURES")
    beta_spx = data.get("beta_spx")
    if is_numeric(beta_spx):
        sensitivity = ""
        if beta_spx > BETA_HIGH_THRESHOLD:
            sensitivity = "(High sensitivity)"
        elif beta_spx < BETA_LOW_THRESHOLD:
            sensitivity = "(Low sensitivity)"
        lines.append(f"Beta (SPX)       {beta_spx:4.2f}    {sensitivity}")

    idio_vol = data.get("idio_vol")
    total_vol = data.get("total_vol")
    if is_numeric(idio_vol):
        risk_level = ""
        if idio_vol > IDIO_VOL_HIGH_THRESHOLD:
            risk_level = "(High stock-specific risk)"
        elif idio_vol < IDIO_VOL_LOW_THRESHOLD:
            risk_level = "(Low stock-specific risk)"
        lines.append(f"Idio Vol         {idio_vol:4.1f}%   {risk_level}")
    if is_numeric(total_vol):
        lines.append(f"Total Vol        {total_vol:4.1f}%")

    # Short Interest (positioning risk)
    short_pct_float = data.get("short_pct_float")
    short_ratio = data.get("short_ratio")
    if is_numeric(short_pct_float) or is_numeric(short_ratio):
        if is_numeric(short_pct_float):
            # Convert from decimal to percentage if needed
            short_pct = short_pct_float * 100 if short_pct_float < 1 else short_pct_float
            squeeze_signal = ""
            if short_pct > 20:  # noqa: PLR2004
                squeeze_signal = "(High squeeze risk)"
            elif short_pct > 10:  # noqa: PLR2004
                squeeze_signal = "(Moderate short interest)"
            lines.append(f"Short % Float    {short_pct:4.1f}%   {squeeze_signal}")
        if is_numeric(short_ratio):
            lines.append(f"Days to Cover    {short_ratio:4.1f}")

    lines.append("")

    # Valuation
    has_valuation = False
    trailing_pe = data.get("trailing_pe")
    forward_pe = data.get("forward_pe")
    dividend_yield = data.get("dividend_yield")

    if any(is_numeric(x) for x in [trailing_pe, forward_pe, dividend_yield]):
        lines.append("VALUATION")
        has_valuation = True

    if is_numeric(trailing_pe):
        lines.append(f"P/E Ratio        {trailing_pe:6.2f}")
    if is_numeric(forward_pe):
        lines.append(f"Forward P/E      {forward_pe:6.2f}")
    if is_numeric(dividend_yield):
        lines.append(f"Dividend Yield   {dividend_yield:5.2f}%")

    if has_valuation:
        lines.append("")

    # Earnings and dividend calendar section
    calendar = data.get("calendar")
    has_calendar = False
    if calendar:
        earnings_date = calendar.get("Earnings Date")
        earnings_avg = calendar.get("Earnings Average")
        div_date = calendar.get("Dividend Date")
        ex_div_date = calendar.get("Ex-Dividend Date")

        if earnings_date or div_date or ex_div_date:
            lines.append("CALENDAR")
            has_calendar = True

        if earnings_date and isinstance(earnings_date, list) and earnings_date:
            cal_date_str = earnings_date[0].strftime("%b %d, %Y")
            line = f"Earnings         {cal_date_str}"
            if is_numeric(earnings_avg):
                line += f"  (Est ${earnings_avg:.2f} EPS)"
            lines.append(line)

        if ex_div_date:
            cal_date_str = ex_div_date.strftime("%b %d, %Y")
            lines.append(f"Ex-Dividend      {cal_date_str}")

        if div_date:
            cal_date_str = div_date.strftime("%b %d, %Y")
            lines.append(f"Div Payment      {cal_date_str}")

    if has_calendar:
        lines.append("")

    # Momentum & Technicals
    lines.append("MOMENTUM & TECHNICALS")
    mom_1w = data.get("momentum_1w")
    mom_1m = data.get("momentum_1m")
    mom_1y = data.get("momentum_1y")
    if is_numeric(mom_1w):
        lines.append(f"1-Week           {mom_1w:+6.1f}%")
    if is_numeric(mom_1m):
        lines.append(f"1-Month          {mom_1m:+6.1f}%")
    if is_numeric(mom_1y):
        lines.append(f"1-Year           {mom_1y:+6.1f}%")

    fifty_day = data.get("fifty_day_avg")
    two_hundred_day = data.get("two_hundred_day_avg")
    if is_numeric(fifty_day):
        lines.append(f"50-Day MA        {fifty_day:7.2f}")
    if is_numeric(two_hundred_day):
        lines.append(f"200-Day MA       {two_hundred_day:7.2f}")

    rsi = data.get("rsi")
    if is_numeric(rsi):
        rsi_signal = ""
        if rsi > RSI_OVERBOUGHT:
            rsi_signal = "(Overbought)"
        elif rsi < RSI_OVERSOLD:
            rsi_signal = "(Oversold)"
        lines.append(f"RSI (14D)        {rsi:5.1f}    {rsi_signal}")
    lines.append("")

    # 52-Week Range with visual bar
    fifty_two_high = data.get("fifty_two_week_high")
    fifty_two_low = data.get("fifty_two_week_low")

    if is_numeric(fifty_two_high) and is_numeric(fifty_two_low) and is_numeric(price):
        lines.append("52-WEEK RANGE")
        lines.append(f"High             {fifty_two_high:7.2f}")
        lines.append(f"Low              {fifty_two_low:7.2f}")

        # Visual bar showing position in range
        range_width = fifty_two_high - fifty_two_low
        if range_width > 0:
            range_pct = ((price - fifty_two_low) / range_width) * 100
            bar_width = 20
            filled = int((range_pct / 100) * bar_width)
            bar = "=" * filled + "░" * (bar_width - filled)
            lines.append(f"Current          {price:7.2f}  [{bar}]  {range_pct:.0f}% of range")
        else:
            # Same high and low (no range)
            lines.append(f"Current          {price:7.2f}  [flat - no range]")
        lines.append("")

    # Options Positioning (brief summary)
    options_data = data.get("options_data")
    if options_data and not options_data.get("error"):
        # Format brief summary for ticker overview
        options_summary = format_options_summary(options_data)
        lines.append(options_summary)
        lines.append("")

    # Footer
    lines.append("")
    lines.append(f"Data as of {date_str} {time_str} | Source: yfinance")

    return "\n".join(lines)


def format_ticker_batch(data_list: list[dict[str, Any]]) -> str:
    """Format batch ticker comparison - side-by-side comparison table"""
    if not data_list:
        return "ERROR: No ticker data provided"

    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M %Z")

    # Extract symbols for header
    symbols = [data.get("symbol", "???") for data in data_list]
    symbols_str = ", ".join(symbols)

    lines = []
    lines.append(f"TICKERS {symbols_str}")
    lines.append("")

    # Header
    header = (
        f"{'SYMBOL':8} {'NAME':30} {'PRICE':>10} {'CHG%':>8} "
        f"{'BETA':>6} {'IDIO':>6} {'SHORT%':>8} {'MOM1W':>8} {'MOM1M':>8} {'MOM1Y':>8} "
        f"{'P/E':>8} {'DIV%':>6} {'RSI':>6}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    # Data rows
    for data in data_list:
        if data.get("error"):
            symbol = data.get("symbol", "???")
            lines.append(f"{symbol:8} ERROR: {data['error']}")
            continue

        symbol = data.get("symbol", "")[:8]
        name = data.get("name", "")[:30]
        price = data.get("price")
        change_pct = data.get("change_percent")
        beta_spx = data.get("beta_spx")
        idio_vol = data.get("idio_vol")
        short_pct_float = data.get("short_pct_float")
        mom_1w = data.get("momentum_1w")
        mom_1m = data.get("momentum_1m")
        mom_1y = data.get("momentum_1y")
        trailing_pe = data.get("trailing_pe")
        div_yield = data.get("dividend_yield")
        rsi = data.get("rsi")

        # Format each field with proper handling of None
        price_str = f"{price:10.2f}" if price is not None else " " * 10
        chg_str = f"{change_pct:+7.2f}%" if change_pct is not None else " " * 8
        beta_str = f"{beta_spx:6.2f}" if beta_spx is not None else " " * 6
        idio_str = f"{idio_vol:5.1f}%" if idio_vol is not None else " " * 6
        # Convert short % from decimal to percentage
        if short_pct_float is not None:
            short_pct = short_pct_float * 100 if short_pct_float < 1 else short_pct_float
            short_str = f"{short_pct:7.1f}%"
        else:
            short_str = " " * 8
        mom_1w_str = f"{mom_1w:+7.1f}%" if mom_1w is not None else " " * 8
        mom_1m_str = f"{mom_1m:+7.1f}%" if mom_1m is not None else " " * 8
        mom_1y_str = f"{mom_1y:+7.1f}%" if mom_1y is not None else " " * 8
        pe_str = f"{trailing_pe:8.2f}" if trailing_pe is not None else " " * 8
        div_str = f"{div_yield:5.2f}%" if div_yield is not None else " " * 6
        rsi_str = f"{rsi:6.1f}" if rsi is not None else " " * 6

        line = (
            f"{symbol:8} {name:30} {price_str} {chg_str} "
            f"{beta_str} {idio_str} {short_str} {mom_1w_str} {mom_1m_str} {mom_1y_str} "
            f"{pe_str} {div_str} {rsi_str}"
        )
        lines.append(line)
    lines.append("")

    # Footer
    lines.append(f"Data as of {date_str} {time_str} | Source: yfinance")

    return "\n".join(lines)
