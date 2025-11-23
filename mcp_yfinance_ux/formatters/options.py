"""
Options formatter - BBG Lite style.

Formats comprehensive options chain analysis with positioning, IV, volume.
"""

from typing import Any


def format_options(data: dict[str, Any]) -> str:  # noqa: PLR0915, PLR0912
    """
    Format options data in BBG Lite style.

    Context delivery system - NO recommendations.
    """
    if "error" in data:
        return f"ERROR: {data['error']}"

    # Header (context: ticker, expiration, current price)
    symbol = data["symbol"]
    price = data["current_price"]
    exp = data["expiration"]
    dte = data["dte"]
    atm = data["atm_strike"]

    lines = [
        f"{symbol} US EQUITY                          OPTIONS ANALYSIS",
        f"Last: ${price:.2f}                          Exp: {exp} ({dte}d)  |  ATM: ${atm:.0f}",
        "",
    ]

    # Positioning (most important - hierarchy principle)
    pc_oi = data["pc_ratio_oi"]
    # Thresholds: 0.8 = bullish, 1.2 = bearish
    sentiment = "BULLISH" if pc_oi < 0.8 else "BEARISH" if pc_oi > 1.2 else "NEUTRAL"  # noqa: PLR2004
    call_oi = data["call_oi_total"]
    put_oi = data["put_oi_total"]

    multiplier = ""
    if pc_oi < 0.8 and pc_oi > 0:  # noqa: PLR2004
        multiplier = f" (calls {(1/pc_oi):.1f}x puts)"
    elif pc_oi > 1.2:  # noqa: PLR2004
        multiplier = f" (puts {pc_oi:.1f}x calls)"

    lines.extend(
        [
            "POSITIONING (Open Interest)",
            f"Calls:  {call_oi:,} OI",
            f"Puts:   {put_oi:,} OI",
            f"P/C Ratio:  {pc_oi:.2f}    ← {sentiment}{multiplier}",
            "",
        ]
    )

    # Top positions (stacked layout for better web display)
    top_calls_oi = data["top_calls_oi"]
    top_puts_oi = data["top_puts_oi"]

    # CALLS section
    lines.extend(
        [
            "TOP POSITIONS BY OI (Top 10)",
            "CALLS",
            "Strike    OI      Vol     Last      IV",
            "──────────────────────────────────────────────",
        ]
    )

    # Show top 10 calls (or max available)
    for i in range(min(len(top_calls_oi), 10)):
        c = top_calls_oi.iloc[i]
        strike = c["strike"]
        oi = int(c["openInterest"])
        vol = int(c["volume"])
        last = c["lastPrice"]
        iv = c["impliedVolatility"] * 100
        lines.append(f"${strike:<5.0f}  {oi:>7,} {vol:>7,}   ${last:>5.2f}   {iv:>5.1f}%")

    lines.append("")

    # PUTS section
    lines.extend(
        [
            "PUTS",
            "Strike    OI      Vol     Last      IV",
            "──────────────────────────────────────────────",
        ]
    )

    # Show top 10 puts (or max available)
    for i in range(min(len(top_puts_oi), 10)):
        p = top_puts_oi.iloc[i]
        strike = p["strike"]
        oi = int(p["openInterest"])
        vol = int(p["volume"])
        last = p["lastPrice"]
        iv = p["impliedVolatility"] * 100
        lines.append(f"${strike:<5.0f}  {oi:>7,} {vol:>7,}   ${last:>5.2f}   {iv:>5.1f}%")

    lines.append("")

    # IV structure (context principle - inline interpretation)
    atm_call_iv = data["atm_call_iv"]
    atm_put_iv = data["atm_put_iv"]
    iv_spread = data["iv_spread"]
    unusual = ""
    if abs(iv_spread) > 2:  # noqa: PLR2004
        direction = "calls" if iv_spread > 0 else "puts"
        unusual = f"← UNUSUAL ({direction} typically lower)"

    lines.extend(
        [
            "IMPLIED VOLATILITY",
            f"ATM Calls:     {atm_call_iv:.1f}%",
            f"ATM Puts:      {atm_put_iv:.1f}%",
            f"Spread:        {iv_spread:+.1f}% {'calls' if iv_spread > 0 else 'puts'}  {unusual}",
            "",
        ]
    )

    # Vol skew
    put_skew = data["put_skew"]
    call_skew = data["call_skew"]
    skew_note = ""
    if abs(put_skew) < 1:
        skew_note = "← FLAT (no panic premium)"

    lines.extend(
        [
            "VOL SKEW",
            f"OTM Puts vs ATM:  {put_skew:+.1f}%    {skew_note}",
            f"OTM Calls vs ATM: {call_skew:+.1f}%",
            "",
        ]
    )

    # Term structure (if available)
    if data["term_structure"]:
        lines.append("TERM STRUCTURE")
        for idx, ts in enumerate(data["term_structure"]):
            label = (
                "Near"
                if idx == 0
                else "Mid"
                if idx == 1
                else "Far"
            )
            marker = "← Current" if idx == 0 else ""
            lines.append(f"{label} ({ts['dte']}d):    {ts['iv']:.1f}%       {marker}")

        contango = data["contango"]
        if contango > 5:  # noqa: PLR2004
            far_iv = data["term_structure"][-1]["iv"]
            compression_note = f"← Market expects compression (to {far_iv:.1f}%)"
        elif contango < -5:  # noqa: PLR2004
            compression_note = "← Backwardation (vol expected to rise)"
        else:
            compression_note = "← Flat term structure"
        lines.append(f"Contango:     {contango:+.1f}%       {compression_note}")
        lines.append("")

    # Interpretation (progressive disclosure principle - summary at bottom)
    # Context delivery, NO recommendations
    interp_lines = ["INTERPRETATION"]

    # Positioning insight
    if pc_oi < 0.7 and pc_oi > 0:  # noqa: PLR2004
        interp_lines.append(
            f"• Heavy call positioning: OI P/C {pc_oi:.2f} ({(1/pc_oi):.1f}x calls vs puts)"
        )
    elif pc_oi > 1.3:  # noqa: PLR2004
        interp_lines.append(
            f"• Heavy put positioning: OI P/C {pc_oi:.2f} ({pc_oi:.1f}x puts vs calls)"
        )

    # IV spread insight
    if abs(iv_spread) > 3:  # noqa: PLR2004
        direction = "calls" if iv_spread > 0 else "puts"
        opposite = "puts" if iv_spread > 0 else "calls"
        interp_lines.append(
            f"• {direction.capitalize()} IV elevated: "
            f"{abs(iv_spread):.1f}% above {opposite}"
        )

    # Skew insight
    if abs(put_skew) < 1:
        interp_lines.append("• Flat skew: no panic premium in OTM puts")

    # Term structure insight
    if data["term_structure"] and abs(contango) > 5:  # noqa: PLR2004
        if contango > 5:  # noqa: PLR2004
            near_iv = data["term_structure"][0]["iv"]
            far_iv = data["term_structure"][-1]["iv"]
            interp_lines.append(
                f"• Term structure contango: market pricing vol compression "
                f"from {near_iv:.1f}% → {far_iv:.1f}%"
            )
        else:
            interp_lines.append("• Backwardation: market expects volatility to increase")

    lines.extend(interp_lines)
    lines.append("")

    # ITM/OTM Breakdown
    call_oi_itm = data["call_oi_itm"]
    call_oi_otm = data["call_oi_otm"]
    put_oi_itm = data["put_oi_itm"]
    put_oi_otm = data["put_oi_otm"]

    call_itm_pct = (call_oi_itm/(call_oi_itm+call_oi_otm)*100) if (call_oi_itm+call_oi_otm) > 0 else 0  # noqa: E501
    call_otm_pct = (call_oi_otm/(call_oi_itm+call_oi_otm)*100) if (call_oi_itm+call_oi_otm) > 0 else 0  # noqa: E501
    put_itm_pct = (put_oi_itm/(put_oi_itm+put_oi_otm)*100) if (put_oi_itm+put_oi_otm) > 0 else 0
    put_otm_pct = (put_oi_otm/(put_oi_itm+put_oi_otm)*100) if (put_oi_itm+put_oi_otm) > 0 else 0

    lines.extend([
        "ITM/OTM BREAKDOWN",
        f"Calls ITM:  {call_oi_itm:,}    ({call_itm_pct:.1f}%)" if call_oi_itm > 0 else "Calls ITM:  0",  # noqa: E501
        f"Calls OTM:  {call_oi_otm:,}    ({call_otm_pct:.1f}%)" if call_oi_otm > 0 else "Calls OTM:  0",  # noqa: E501
        f"Puts ITM:   {put_oi_itm:,}    ({put_itm_pct:.1f}%)" if put_oi_itm > 0 else "Puts ITM:   0",  # noqa: E501
        f"Puts OTM:   {put_oi_otm:,}    ({put_otm_pct:.1f}%)" if put_oi_otm > 0 else "Puts OTM:   0",  # noqa: E501
        "",
    ])

    # Volume Analysis
    pc_vol = data["pc_ratio_vol"]
    call_vol = data["call_volume_total"]
    put_vol = data["put_volume_total"]

    vol_sentiment = "BULLISH" if pc_vol < 0.8 else "BEARISH" if pc_vol > 1.2 else "NEUTRAL"  # noqa: PLR2004
    lines.extend([
        "VOLUME ANALYSIS",
        f"Call Volume:  {call_vol:,}",
        f"Put Volume:   {put_vol:,}",
        f"P/C Volume:   {pc_vol:.2f}    ← {vol_sentiment}",
        "",
    ])

    # Max Pain
    max_pain = data["max_pain_strike"]
    price_vs_max_pain = ((price - max_pain) / price * 100) if max_pain > 0 else 0
    lines.extend([
        "MAX PAIN ANALYSIS",
        f"Max Pain Strike:  ${max_pain:.0f}",
        f"Current vs Max Pain:  {price_vs_max_pain:+.1f}%",
        "",
    ])

    # Unusual Activity
    unusual = data["unusual_activity"]
    if unusual:
        unusual_calls = data["unusual_calls"]
        unusual_puts = data["unusual_puts"]
        lines.extend([
            "UNUSUAL ACTIVITY (Vol > 2x OI)",
            f"Unusual Call Strikes: {len(unusual_calls)}",
            f"Unusual Put Strikes: {len(unusual_puts)}",
        ])
        # Show top 3 unusual strikes
        if len(unusual_calls) > 0:
            lines.append("Top Unusual Calls:")
            for _, row in unusual_calls.nlargest(3, "volume").iterrows():
                strike = row["strike"]
                vol = int(row["volume"])
                oi = int(row["openInterest"])
                ratio = (vol / oi) if oi > 0 else float("inf")
                ratio_str = f"{ratio:.1f}x" if ratio != float("inf") else "N/A"
                lines.append(f"  ${strike:.0f}  Vol:{vol:,}  OI:{oi:,}  Ratio:{ratio_str}")
        if len(unusual_puts) > 0:
            lines.append("Top Unusual Puts:")
            for _, row in unusual_puts.nlargest(3, "volume").iterrows():
                strike = row["strike"]
                vol = int(row["volume"])
                oi = int(row["openInterest"])
                ratio = (vol / oi) if oi > 0 else float("inf")
                ratio_str = f"{ratio:.1f}x" if ratio != float("inf") else "N/A"
                lines.append(f"  ${strike:.0f}  Vol:{vol:,}  OI:{oi:,}  Ratio:{ratio_str}")
        lines.append("")
    else:
        lines.extend([
            "UNUSUAL ACTIVITY",
            "No unusual activity detected (Vol < 2x OI)",
            "",
        ])

    # Historical IV Context
    hist_iv = data.get("hist_iv_data")
    if hist_iv:
        lines.extend([
            "HISTORICAL IV CONTEXT",
            f"Current ATM IV:  {atm_call_iv:.1f}%",
            f"30-Day Hist Vol: {hist_iv['hist_vol_30d']:.1f}%",
            f"52-Week IV Range: {hist_iv['iv_low_52w']:.1f}% - {hist_iv['iv_high_52w']:.1f}%",
            f"IV Rank:  {hist_iv['iv_rank']:.0f}%  (percentile in 52-week range)",
            "",
        ])

    # All Expirations Summary
    all_exp = data.get("all_expirations", [])
    if all_exp:
        lines.extend([
            f"ALL EXPIRATIONS ({len(all_exp)} available)",
            "Exp Date       DTE     IV     Total OI    Total Vol",
            "─────────────────────────────────────────────────────",
        ])
        for exp in all_exp[:10]:  # Show first 10
            exp_date = exp["expiration"]
            dte = exp["dte"]
            iv = exp["iv"]
            total_oi = exp["total_oi"]
            total_vol = exp["total_volume"]
            lines.append(f"{exp_date}   {dte:>3}d   {iv:>5.1f}%   {total_oi:>8,}   {total_vol:>9,}")
        if len(all_exp) > 10:  # noqa: PLR2004
            lines.append(f"... and {len(all_exp) - 10} more expirations")
        lines.append("")

    # Footer
    lines.append(f"Data as of {data['timestamp']} | Source: yfinance")

    return "\n".join(lines)
