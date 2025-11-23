"""
Ticker symbol normalization utilities.

Handles Yahoo Finance symbol format conventions:
- Exchange suffixes (NEO.TO, 0700.HK) - keep dots
- Share classes (BRK.B, BRK.A) - convert to hyphens
"""


def normalize_ticker_symbol(symbol: str) -> str:
    """
    Normalize ticker symbol to Yahoo Finance format.

    Exchange suffixes (keep dots):
    - NEO.TO → NEO.TO (Toronto Stock Exchange)
    - 0700.HK → 0700.HK (Hong Kong)
    - RIO.L → RIO.L (London)
    - BHP.AX → BHP.AX (Australia)

    Share classes (convert to hyphens):
    - BRK.B or BRK/B → BRK-B (Berkshire Class B)
    - BRK.A or BRK/A → BRK-A (Berkshire Class A)
    - BAC.PL or BAC/PL → BAC-PL (Preferred stock)

    Heuristic:
    - If dot followed by known exchange suffix: keep dot
    - If dot followed by 1-2 chars at end: share class (replace with dash)
    """
    # Replace slashes with hyphens first
    symbol = symbol.replace("/", "-")

    # Check if this is an exchange suffix
    # Common exchange suffixes: .TO, .HK, .L, .AX, .PA, .DE, .SW, .F, etc.
    if "." in symbol:
        parts = symbol.split(".")
        if len(parts) == 2:  # noqa: PLR2004
            suffix = parts[1].upper()
            # Known single-letter exchange suffixes
            single_letter_exchanges = {"L", "F", "P"}  # London, Frankfurt, Paris
            # Exchange suffix if:
            # - Single uppercase letter in known set, OR
            # - 2+ uppercase characters
            if (
                (len(suffix) == 1 and suffix in single_letter_exchanges)
                or (len(suffix) >= 2 and suffix.isupper())  # noqa: PLR2004
            ):
                # Exchange suffix - keep the dot
                return symbol
        # Share class - replace dot with dash
        return symbol.replace(".", "-")

    return symbol
