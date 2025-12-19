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
    UNUSUAL_VOLUME_THRESHOLD,
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

    # Fixed column widths for alignment
    name_width = 20
    ticker_width = 8
    price_width = 12
    change_width = 9
    rvol_width = 8
    mom1m_width = 10
    mom1y_width = 10

    # Helper to format line with ticker symbol and optional momentum
    def format_line(  # noqa: PLR0912
        key: str,
        show_ticker: bool = False,
        show_momentum: bool = True,
        show_volume: bool = True
    ) -> str | None:
        info = data.get(key)
        if not info or info.get("error"):
            return None

        price = info.get("price")
        change_pct = info.get("change_percent")

        if price is None or change_pct is None:
            return None

        name = DISPLAY_NAMES.get(key, key)
        ticker = MARKET_SYMBOLS.get(key, "")

        # Build line using fixed column widths
        parts = []

        # Name column (left-aligned)
        parts.append(f"{name:<{name_width}}")

        # Ticker column (left-aligned)
        if show_ticker:
            parts.append(f"{ticker:<{ticker_width}}")
        else:
            parts.append(" " * ticker_width)

        # Price column (right-aligned)
        price_str = f"{price:,.2f}"
        parts.append(f"{price_str:>{price_width}}")

        # Change column (right-aligned)
        change_str = f"{change_pct:+.2f}%"
        parts.append(f"{change_str:>{change_width}}")

        # RVOL column (right-aligned)
        if show_volume:
            rel_vol = info.get("rel_volume")
            if rel_vol is not None and rel_vol > 0:
                rvol_str = f"{rel_vol:.1f}x"
                if rel_vol > UNUSUAL_VOLUME_THRESHOLD:
                    rvol_str += "⚠"
                parts.append(f"{rvol_str:>{rvol_width}}")
            else:
                parts.append(" " * rvol_width)
        else:
            parts.append(" " * rvol_width)

        # Momentum columns (right-aligned)
        if show_momentum:
            mom_1m = info.get("momentum_1m")
            mom_1y = info.get("momentum_1y")

            if mom_1m is not None:
                mom1m_str = f"{mom_1m:+.1f}%"
                parts.append(f"{mom1m_str:>{mom1m_width}}")
            else:
                parts.append(" " * mom1m_width)

            if mom_1y is not None:
                mom1y_str = f"{mom_1y:+.1f}%"
                parts.append(f"{mom1y_str:>{mom1y_width}}")
            else:
                parts.append(" " * mom1y_width)

        return "".join(parts)

    # Helper to build section header
    def make_header(section_name: str, show_ticker: bool = False) -> str:
        parts = []
        parts.append(f"{section_name:<{name_width}}")
        if show_ticker:
            parts.append(f"{'TICKER':<{ticker_width}}")
        else:
            parts.append(" " * ticker_width)
        parts.append(f"{'PRICE':>{price_width}}")
        parts.append(f"{'CHANGE':>{change_width}}")
        parts.append(f"{'RVOL':>{rvol_width}}")
        parts.append(f"{'1M':>{mom1m_width}}")
        parts.append(f"{'1Y':>{mom1y_width}}")
        return "".join(parts)

    # US FUTURES (show only when market closed - forward-looking sentiment)
    # No 1M/1Y momentum for futures (contracts roll over)
    # Only show when market is closed (pre-market, after-hours, weekends)
    if futures_are_open and not market_is_open:
        parts = [
            f"{'US FUTURES':<{name_width}}",
            " " * ticker_width,
            f"{'PRICE':>{price_width}}",
            f"{'CHANGE':>{change_width}}",
        ]
        lines.append("".join(parts))
        for key in ["es_futures", "nq_futures", "ym_futures"]:
            if line := format_line(key, show_momentum=False, show_volume=False):
                lines.append(line)
        lines.append("")

    # US EQUITIES (always show - either live during market or close after hours)
    market_status = "OPEN" if market_is_open else "CLOSED"
    section_name = f"US EQUITIES ({market_status})"
    lines.append(make_header(section_name))
    for key in ["sp500", "nasdaq", "dow", "russell2000"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # GLOBAL (no RVOL - index volume data unreliable)
    lines.append(make_header("GLOBAL"))
    global_keys = [
        "stoxx50", "nikkei", "hangseng", "shanghai",
        "kospi", "nifty50", "asx200", "taiwan", "bovespa"
    ]
    for key in global_keys:
        if line := format_line(key, show_volume=False):
            lines.append(line)
    lines.append("")

    # COMMODITIES
    lines.append(make_header("COMMODITIES"))
    # Metals: hide RVOL (yfinance averageVolume unreliable)
    for key in ["gold", "silver", "platinum", "copper"]:
        if line := format_line(key, show_volume=False):
            lines.append(line)
    # Energy: show RVOL (reliable data)
    for key in ["oil_wti", "natgas"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # CRYPTO
    lines.append(make_header("CRYPTO"))
    for key in ["btc", "eth", "sol"]:
        if line := format_line(key):
            lines.append(line)
    lines.append("")

    # SECTORS - show ticker for drill-down
    lines.append(make_header("SECTORS", show_ticker=True))
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
    lines.append(make_header("STYLES", show_ticker=True))
    for key in ["momentum", "value", "growth", "quality", "small_cap"]:
        if line := format_line(key, show_ticker=True):
            lines.append(line)
    lines.append("")

    # PRIVATE CREDIT
    lines.append(make_header("PRIVATE CREDIT", show_ticker=True))
    if line := format_line("private_credit", show_ticker=True):
        lines.append(line)
    lines.append("")

    # VOLATILITY & RATES (no RVOL - indices, not tradable)
    lines.append(make_header("VOLATILITY & RATES"))
    for key in ["vix", "us10y"]:
        if line := format_line(key, show_volume=False):
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
