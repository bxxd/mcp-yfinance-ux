"""
Sector formatter - BBG Lite style.

Formats sector ETF performance with top 10 holdings.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def format_sector(data: dict[str, Any]) -> str:
    """Format sector() screen - BBG Lite style"""
    if data.get("error"):
        return f"ERROR: {data['error']}"

    sector_name = data["sector_name"]
    sector_symbol = data["sector_symbol"]
    sector_data = data["sector_data"]
    holdings = data["holdings"]

    now = datetime.now(ZoneInfo("America/New_York"))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M %Z")

    # Header (simple title for panel)
    header = f"SECTOR {sector_name.upper()}"
    lines = [header, ""]

    # Sector ETF performance (no absolute price - only changes matter)
    change_pct = sector_data.get("change_percent", 0)
    mom_1m = sector_data.get("momentum_1m")
    mom_1y = sector_data.get("momentum_1y")

    # Column headers
    lines.append("TICKER    CHANGE       1M         1Y")

    # Format: XLK      -0.99%     +1.9%     +25.8%
    line = f"{sector_symbol:6}  {change_pct:+6.2f}%"
    if mom_1m is not None:
        line += f"     {mom_1m:+.1f}%"
    if mom_1y is not None:
        line += f"     {mom_1y:+.1f}%"
    lines.append(line)
    lines.append("")

    # Top holdings with performance
    if holdings:
        lines.append("TOP HOLDINGS     SYMBOL    WEIGHT   CHANGE       1M         1Y")
        for h in holdings:
            symbol = h["symbol"]
            weight_pct = h["weight"] * 100
            change_pct = h.get("change_percent")
            mom_1m = h.get("momentum_1m")
            mom_1y = h.get("momentum_1y")

            # Truncate name to fit
            name = h["name"][:16]

            # Build line with performance data
            line = f"{name:16} {symbol:8}  {weight_pct:5.1f}%"
            if change_pct is not None:
                line += f"   {change_pct:+6.2f}%"
            else:
                line += "         "
            if mom_1m is not None:
                line += f"     {mom_1m:+.1f}%"
            else:
                line += "         "
            if mom_1y is not None:
                line += f"     {mom_1y:+.1f}%"

            lines.append(line)
        lines.append("")

    # Footer
    lines.append(f"Data as of {date_str} {time_str} | Source: yfinance")

    return "\n".join(lines)
