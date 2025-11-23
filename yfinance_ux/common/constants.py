"""
Constants and mappings for yfinance MCP server.

All CAPS variables - display names, symbol mappings, thresholds.
Single source of truth for configuration.
"""

# Weekend and trading day constants
WEEKEND_START_DAY = 5  # Saturday (Monday = 0, Sunday = 6)
FRIDAY = 4  # Friday weekday number
SATURDAY = 5  # Saturday weekday number
SUNDAY = 6  # Sunday weekday number
TRADING_DAYS_PER_MONTH = 21  # Approximate trading days in 1 month
MIN_HISTORY_LEN = 2  # Minimum data points needed for calculations

# Factor thresholds
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
BETA_HIGH_THRESHOLD = 1.2
BETA_LOW_THRESHOLD = 0.8
IDIO_VOL_HIGH_THRESHOLD = 30
IDIO_VOL_LOW_THRESHOLD = 15

# Category to symbol mappings (for get_market_snapshot)
# Aligned with Paleologo factor framework
CATEGORY_MAPPING: dict[str, list[str]] = {
    "us": ["sp500", "nasdaq", "dow", "russell2000"],
    "futures": ["es_futures", "nq_futures", "ym_futures"],
    "volatility": ["vix"],
    "commodities": ["gold", "oil_wti", "natgas"],
    "rates": ["us10y"],
    "crypto": ["btc", "eth", "sol"],
    "europe": ["stoxx50", "dax", "ftse", "cac40"],
    "asia": ["nikkei", "hangseng", "shanghai"],
    "currencies": ["eurusd", "usdjpy", "usdcny", "gbpusd", "usdcad", "audusd"],
    "bonds": ["us10y", "us2y", "us30y"],
    # Industry factors (GICS sectors)
    "sectors": [
        "tech", "financials", "healthcare", "energy", "consumer_disc",
        "industrials", "materials", "utilities", "consumer_stpl", "real_estate", "communication"
    ],
    # Style factors
    "styles": ["momentum", "value", "growth", "quality", "small_cap"],
    # Convenience aggregates
    "factors": ["vix", "gold", "oil_wti", "natgas", "us10y"],  # Core systematic factors
    "all": [
        "es_futures", "nq_futures", "ym_futures",
        "vix", "gold", "oil_wti", "natgas", "us10y",
        "sp500", "nasdaq", "dow", "russell2000",
        "stoxx50", "dax", "ftse", "cac40",
        "nikkei", "hangseng", "shanghai",
        "btc", "eth", "sol",
        "eurusd", "usdjpy", "usdcny", "gbpusd", "usdcad", "audusd",
        "tech", "financials", "healthcare", "energy", "consumer_disc",
        "industrials", "materials", "utilities", "consumer_stpl", "real_estate", "communication",
        "momentum", "value", "growth", "quality", "small_cap",
    ],
}

# Market snapshot symbol mappings
MARKET_SYMBOLS = {
    # US Indices
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    "russell2000": "^RUT",

    # Futures
    "es_futures": "ES=F",      # S&P 500 futures
    "nq_futures": "NQ=F",      # Nasdaq futures
    "ym_futures": "YM=F",      # Dow futures
    "rty_futures": "RTY=F",    # Russell 2000 futures

    # European Indices
    "stoxx50": "^STOXX50E",
    "dax": "^GDAXI",
    "ftse": "^FTSE",
    "cac40": "^FCHI",

    # Asian Indices
    "nikkei": "^N225",
    "hangseng": "^HSI",
    "shanghai": "000001.SS",
    "kospi": "^KS11",        # South Korea
    "nifty50": "^NSEI",      # India
    "asx200": "^AXJO",       # Australia
    "taiwan": "^TWII",       # Taiwan

    # Latin America
    "bovespa": "^BVSP",      # Brazil

    # Crypto
    "btc": "BTC-USD",
    "eth": "ETH-USD",
    "sol": "SOL-USD",

    # Commodities
    "gold": "GC=F",
    "silver": "SI=F",
    "oil_wti": "CL=F",
    "oil_brent": "BZ=F",
    "natgas": "NG=F",

    # Bonds
    "us10y": "^TNX",
    "us2y": "^IRX",
    "us30y": "^TYX",

    # Volatility
    "vix": "^VIX",

    # Currencies
    "eurusd": "EURUSD=X",
    "usdjpy": "JPY=X",
    "usdcny": "CNY=X",
    "gbpusd": "GBPUSD=X",
    "usdcad": "CAD=X",
    "audusd": "AUDUSD=X",

    # Sector ETFs (GICS Industries)
    "tech": "XLK",          # Technology
    "financials": "XLF",    # Financials
    "energy": "XLE",        # Energy
    "healthcare": "XLV",    # Healthcare
    "consumer_disc": "XLY", # Consumer Discretionary
    "consumer_stpl": "XLP", # Consumer Staples
    "industrials": "XLI",   # Industrials
    "utilities": "XLU",     # Utilities
    "materials": "XLB",     # Materials
    "real_estate": "XLRE",  # Real Estate
    "communication": "XLC", # Communication Services

    # Style Factor ETFs
    "momentum": "MTUM",     # iShares MSCI USA Momentum
    "value": "VTV",         # Vanguard Value
    "growth": "VUG",        # Vanguard Growth
    "quality": "QUAL",      # iShares MSCI USA Quality
    "small_cap": "IWM",     # Russell 2000 (size factor)

    # Private Credit / BDCs
    "private_credit": "BIZD",  # VanEck BDC Income ETF (private credit proxy)
}

# Formatting sections (for format_market_snapshot)
# Organized by Paleologo factor framework
FORMATTING_SECTIONS: dict[str, list[str]] = {
    "MARKET": ["sp500", "nasdaq", "dow", "russell2000"],  # During market hours
    "MARKET FUTURES": ["es_futures", "nq_futures", "ym_futures"],  # After hours
    "VOLATILITY": ["vix"],
    "COMMODITIES": ["gold", "oil_wti", "natgas"],
    "RATES": ["us10y"],
    "SECTORS": [
        "tech", "financials", "healthcare", "energy", "consumer_disc",
        "industrials", "materials", "utilities", "consumer_stpl", "real_estate", "communication"
    ],
    "STYLE FACTORS": ["momentum", "value", "growth", "quality", "small_cap"],
    "CRYPTO": ["btc", "eth", "sol"],
    "EUROPE": ["stoxx50", "dax", "ftse", "cac40"],
    "ASIA": ["nikkei", "hangseng", "shanghai"],
    "CURRENCIES": ["eurusd", "usdjpy", "usdcny", "gbpusd", "usdcad", "audusd"],
}

# Section to region mapping (for market status display)
SECTION_REGION_MAP: dict[str, str] = {
    "MARKET": "us",
    "MARKET FUTURES": "us",
    "EUROPE": "europe",
    "ASIA": "asia",
}

# Friendly display names
DISPLAY_NAMES: dict[str, str] = {
    "es_futures": "S&P 500", "nq_futures": "Nasdaq", "ym_futures": "Dow",
    "gold": "Gold", "btc": "Bitcoin", "vix": "VIX",
    "oil_wti": "Oil WTI", "natgas": "Nat Gas",
    "us10y": "US 10Y",
    "sp500": "S&P 500", "nasdaq": "Nasdaq", "dow": "Dow", "russell2000": "Russell 2000",
    # Global indices (region code first for easier scanning)
    "stoxx50": "EU Stoxx50", "dax": "DE DAX", "ftse": "UK FTSE", "cac40": "FR CAC40",
    "nikkei": "JP Nikkei", "hangseng": "HK HSI", "shanghai": "CN Shanghai",
    "kospi": "KR KOSPI", "nifty50": "IN Nifty50", "asx200": "AU ASX200",
    "taiwan": "TW TWSE", "bovespa": "BR Bovespa",
    "eth": "Ethereum", "sol": "Solana",
    "eurusd": "EUR/USD", "usdjpy": "USD/JPY", "usdcny": "USD/CNY",
    "gbpusd": "GBP/USD", "usdcad": "USD/CAD", "audusd": "AUD/USD",
    # Sectors
    "tech": "Technology", "financials": "Financials", "healthcare": "Healthcare",
    "energy": "Energy", "consumer_disc": "Cons Discr", "industrials": "Industrials",
    "materials": "Materials", "utilities": "Utilities", "consumer_stpl": "Cons Staples",
    "real_estate": "Real Estate", "communication": "Communication",
    # Style factors
    "momentum": "Momentum", "value": "Value", "growth": "Growth",
    "quality": "Quality", "small_cap": "Small Cap",
    # Private credit
    "private_credit": "Private Credit",
}

# Factor annotations
FACTOR_ANNOTATIONS: dict[str, str] = {
    "gold": "Safe haven",
    "btc": "Risk-on",
    "vix": "Fear gauge",
    "us10y": "Risk-free rate",
    "momentum": "Winners keep winning (tail risk)",
    "value": "Cheap stocks (quality trap risk)",
    "growth": "Expensive promise (multiple compression risk)",
    "quality": "Stable moats (rate sensitive)",
    "small_cap": "Size premium (liquidity risk)",
}

# Sector ETF symbol to name mapping (for sector drill-down)
# Maps normalized sector keys to ticker symbols
SECTOR_SYMBOLS: dict[str, str] = {
    "tech": "XLK",
    "technology": "XLK",
    "financials": "XLF",
    "healthcare": "XLV",
    "health": "XLV",
    "energy": "XLE",
    "consumer_disc": "XLY",
    "consumer_discretionary": "XLY",
    "industrials": "XLI",
    "materials": "XLB",
    "utilities": "XLU",
    "consumer_stpl": "XLP",
    "consumer_staples": "XLP",
    "real_estate": "XLRE",
    "realestate": "XLRE",
    "communication": "XLC",
    "communications": "XLC",
    "comm": "XLC",
}

# Sector display names (for sector drill-down headers)
SECTOR_DISPLAY_NAMES: dict[str, str] = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLY": "Consumer Discretionary",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}
