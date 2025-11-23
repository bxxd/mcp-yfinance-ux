"""
Market formatters - BBG Lite style.

Formats market overview screens with factors and momentum.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from yfinance_ux.common.constants import (
    DISPLAY_NAMES,
    FORMATTING_SECTIONS,
    MARKET_SYMBOLS,
    SECTION_REGION_MAP,
)
from yfinance_ux.common.dates import (
    get_market_status,
    is_futures_open,
    is_market_open,
)


def format_markets(data: dict[str, dict[str, Any]]) -> str:  # noqa: PLR0912, PLR0915
    """Format markets() screen - BBG Lite style with factors"""
    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M %Z")

    # Header - simple day/date/time (data shows if futures trading)
    market_is_open = is_market_open()
    futures_are_open = is_futures_open()
    day_of_week = now.strftime("%a")  # Mon, Tue, Wed, etc.

    lines = [f"MARKETS | {day_of_week} {date_str} {time_str}", ""]

    # Helper to format line with ticker symbol and optional momentum
    def format_line(key: str, show_ticker: bool = False, show_momentum: bool = True) -> str | None:
        info = data.get(key)
        if not info or info.get("error"):
            return None

        price = info.get("price")
        change_pct = info.get("change_percent")

        if price is None or change_pct is None:
            return None

        name = DISPLAY_NAMES.get(key, key)

        # Get ticker symbol for drill-down
        ticker = MARKET_SYMBOLS.get(key, "")

        # Format: NAME  TICKER  PRICE  CHANGE%  [+X.X%  +XX.X%]
        if show_ticker:
            line = f"{name:16} {ticker:8} {price:10.2f}   {change_pct:+6.2f}%"
        else:
            line = f"{name:16}          {price:10.2f}   {change_pct:+6.2f}%"

        # Add momentum columns (only if requested - not for futures)
        if show_momentum:
            mom_1m = info.get("momentum_1m")
            mom_1y = info.get("momentum_1y")

            if mom_1m is not None:
                line += f"   {mom_1m:+6.1f}%"
            else:
                line += "          "

            if mom_1y is not None:
                line += f"   {mom_1y:+7.1f}%"

        return line

    # US FUTURES (show only when market closed - forward-looking sentiment)
    # No 1M/1Y momentum for futures (contracts roll over)
    # Only show when market is closed (pre-market, after-hours, weekends)
    if futures_are_open and not market_is_open:
        lines.append("US FUTURES                    PRICE     CHANGE")
        for key in ["es_futures", "nq_futures", "ym_futures"]:
            if line := format_line(key, show_momentum=False):
                lines.append(line)
        lines.append("")

    # US EQUITIES (always show - either live during market or close after hours)
    market_status = "OPEN" if market_is_open else "CLOSED"
    lines.append(f"US EQUITIES ({market_status})         PRICE     CHANGE       1M         1Y")
    for key in ["sp500", "nasdaq", "dow", "russell2000"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # GLOBAL
    lines.append("GLOBAL                        PRICE     CHANGE       1M         1Y")
    global_keys = [
        "stoxx50", "nikkei", "hangseng", "shanghai",
        "kospi", "nifty50", "asx200", "taiwan", "bovespa"
    ]
    for key in global_keys:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # CRYPTO
    lines.append("CRYPTO                        PRICE     CHANGE       1M         1Y")
    for key in ["btc", "eth", "sol"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # SECTORS - show ticker for drill-down
    lines.append("SECTORS          TICKER      PRICE     CHANGE       1M         1Y")
    sector_keys = [
        "tech", "financials", "healthcare", "energy", "consumer_disc",
        "consumer_stpl", "industrials", "utilities", "materials",
        "real_estate", "communication"
    ]
    for key in sector_keys:
        if line := format_line(key, show_ticker=True):
            lines.append(line)
    lines.append("")

    # STYLES - show ticker for drill-down
    lines.append("STYLES           TICKER      PRICE     CHANGE       1M         1Y")
    for key in ["momentum", "value", "growth", "quality", "small_cap"]:
        if line := format_line(key, show_ticker=True):
            lines.append(line)
    lines.append("")

    # PRIVATE CREDIT
    lines.append("PRIVATE CREDIT   TICKER      PRICE     CHANGE       1M         1Y")
    if line := format_line("private_credit", show_ticker=True):
        lines.append(line)
    lines.append("")

    # COMMODITIES
    lines.append("COMMODITIES                   PRICE     CHANGE       1M         1Y")
    for key in ["gold", "oil_wti", "natgas"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # VOLATILITY & RATES
    lines.append("VOLATILITY & RATES            PRICE     CHANGE       1M         1Y")
    for key in ["vix", "us10y"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # Footer
    lines.append("Source: yfinance")

    return "\n".join(lines)


def format_market_snapshot(data: dict[str, dict[str, Any]]) -> str:  # noqa: PLR0912
    """Format market data into concise readable text (BBG Lite style)"""
    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M %Z")

    # Header with timestamp
    lines = [f"MARKETS {date_str} {time_str}"]

    # Determine which market section to show (MARKET vs MARKET FUTURES)
    market_is_open = is_market_open()

    for section_name, symbols in FORMATTING_SECTIONS.items():
        # Skip MARKET section if market closed (show MARKET FUTURES instead)
        if section_name == "MARKET" and not market_is_open:
            continue
        # Skip MARKET FUTURES section if market open (show MARKET instead)
        if section_name == "MARKET FUTURES" and market_is_open:
            continue

        # Check if any symbols in this section are in our data
        section_data = {k: v for k, v in data.items() if k in symbols}
        if not section_data:
            continue

        # Add market status to section header if applicable
        region = SECTION_REGION_MAP.get(section_name)
        if region:
            status = get_market_status(region)
            section_header = f"{section_name} ({status})"
        else:
            section_header = section_name

        lines.append(section_header)
        for symbol, info in section_data.items():
            if info.get("error"):
                display_name = DISPLAY_NAMES.get(symbol, symbol)
                lines.append(f"{display_name:12} ERROR - {info['error']}")
            else:
                price = info.get("price")
                change_pct = info.get("change_percent")
                momentum_1m = info.get("momentum_1m")
                momentum_1y = info.get("momentum_1y")

                # Check if we have momentum data
                has_momentum = momentum_1m is not None or momentum_1y is not None

                if price is not None and change_pct is not None:
                    display_name = DISPLAY_NAMES.get(symbol, symbol)
                    line = f"{display_name:12} {price:10.2f}  {change_pct:+6.2f}%"

                    # Add momentum columns if available
                    if has_momentum:
                        mom_1m_str = (
                            f"{momentum_1m:+6.1f}%" if momentum_1m is not None else "   N/A"
                        )
                        mom_1y_str = (
                            f"{momentum_1y:+6.1f}%" if momentum_1y is not None else "   N/A"
                        )
                        line += f"  {mom_1m_str} (1M)  {mom_1y_str} (1Y)"

                    lines.append(line)
                elif price is not None:
                    display_name = DISPLAY_NAMES.get(symbol, symbol)
                    lines.append(f"{display_name:12} {price:10.2f}")
                else:
                    display_name = DISPLAY_NAMES.get(symbol, symbol)
                    lines.append(f"{display_name:12} N/A")
        lines.append("")  # blank line between sections

    # Footer with guidance
    lines.append("Source: yfinance")
    lines.append(
        "Try: symbol='TSLA' for ticker | categories=['europe'] for regions | "
        "period='3mo' for history"
    )

    return "\n".join(lines)
