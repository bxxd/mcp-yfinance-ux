# yfinance Decoder Ring

**Quick reference**: What each yfinance method returns and when to use it

## TL;DR

**Currently using in MCP**: Price/change data and historical charts

**Available but unused**: Earnings calendars, analyst data, insider transactions, financials, options data, SEC filings

**Key constraint**: Most additional data is **stock-specific only** (not available for indices, futures, crypto)

**Bottom line**: We have access to WAY more data than just prices - when ready to build stock-specific analysis tools (conviction scoring, fundamentals), the capabilities are already there.

## ⚠️ Critical: Usage Constraints

**yfinance is an UNOFFICIAL web scraper, not a sanctioned API.**

### What This Means

**yfinance mimics browser requests** to scrape Yahoo Finance. It's not an official API.

**Implications:**
- **No guarantees** - Can break at any time (Yahoo site changes)
- **No documented rate limits** - Because it's not meant to be used this way
- **Prone to blocking** - Yahoo's anti-scraping measures trigger on suspicious patterns
- **Tightening restrictions** - Yahoo significantly tightened around early 2024
- **No support** - When it breaks, you're on your own

### What Triggers Blocks

**Common causes of 429 errors and IP bans:**
- Frequent requests from same IP address
- Patterns resembling DDoS attacks (bulk downloads, continuous polling)
- High-volume automated requests
- Yahoo site changes can break library entirely

### Safe Usage Pattern

**✅ SAFE (our current implementation):**
- **Ad-hoc, user-initiated queries** - Human asks → MCP call triggered
- **One-off analysis** - "What's TSLA trading at?" → single call
- **Manual research** - Checking markets, analyzing stocks, thesis work
- **Occasional historical data** - Fetching charts for specific analysis
- **Human-in-the-loop** - Every query has user interaction

**This matches hobbyist/prototype/infrequent use that doesn't trigger blocks.**

### Unsafe Usage Pattern

**❌ NEVER DO THIS:**
- **Cron jobs** - Scheduled market data updates
- **Background processes** - Automated monitoring loops
- **Continuous polling** - Real-time portfolio tracking
- **Bulk downloads** - Scraping large datasets
- **Production infrastructure** - Automated trading systems
- **"Set it and forget it"** - Any automation without human interaction

**These patterns trigger Yahoo's anti-scraping measures. 429 errors, IP bans, complete blocks.**

### Appropriate Use Cases

**yfinance is appropriate for:**
- Research and thesis development
- Ad-hoc position analysis
- Manual market checks
- One-off historical analysis
- Prototyping and PMF testing

**yfinance is NOT appropriate for:**
- Real-time portfolio monitoring
- Live P&L tracking
- Automated alerts
- Production trading infrastructure
- Continuous data feeds

**For automation or production use → migrate to official APIs** (Alpha Vantage, Polygon.io, IEX Cloud, etc.)

### Bottom Line

**This MCP server = research tool for occasional queries, not production infrastructure.**

Perfect for PMF testing and ad-hoc analysis. Not suitable for automation or continuous monitoring. If yfinance breaks or gets blocked, that's the signal to migrate to official APIs.

## Asset Type Support Matrix

| Method | Stocks | Indices | Crypto | Futures | Notes |
|--------|--------|---------|--------|---------|-------|
| **Price Data** |
| `.info` | ✅ | ✅ | ✅ | ✅ | 50+ fields, slow |
| `.fast_info` | ✅ | ✅ | ✅ | ✅ | ~20 fields, faster |
| `.history()` | ✅ | ✅ | ✅ | ✅ | OHLCV data |
| **Events** |
| `.calendar` | ✅ | ❌ | ❌ | ❌ | Earnings, dividends |
| **Analyst Data** |
| `.recommendations` | ✅ | ❌ | ❌ | ❌ | Buy/hold/sell counts |
| `.analyst_price_targets` | ✅ | ❌ | ❌ | ❌ | Mean, high, low |
| `.upgrades_downgrades` | ✅ | ❌ | ❌ | ❌ | Recent changes |
| **Ownership** |
| `.institutional_holders` | ✅ | ❌ | ❌ | ❌ | 13F data |
| `.insider_transactions` | ✅ | ❌ | ❌ | ❌ | Form 4 data |
| `.major_holders` | ✅ | ❌ | ❌ | ❌ | Breakdown % |
| **Financials** |
| `.income_stmt` | ✅ | ❌ | ❌ | ❌ | Revenue, earnings |
| `.balance_sheet` | ✅ | ❌ | ❌ | ❌ | Assets, debt |
| `.cash_flow` | ✅ | ❌ | ❌ | ❌ | FCF, buybacks |
| **Options** |
| `.options` | ✅ | ✅ | ❌ | ❌ | Expiration dates |
| `.option_chain(date)` | ✅ | ✅ | ❌ | ❌ | Calls/puts |
| **SEC** |
| `.sec_filings` | ✅ | ❌ | ❌ | ❌ | 10-K, 10-Q, 8-K |

## Price Data

### `.info` - Kitchen Sink (50+ fields, SLOW)

**When to use**: Initial exploration, need obscure fields

**Common fields**:
```python
ticker.info['regularMarketPrice']        # Current price
ticker.info['regularMarketChangePercent'] # Daily change %
ticker.info['marketCap']                 # Market capitalization
ticker.info['volume']                    # Today's volume
ticker.info['averageVolume']             # Average volume
ticker.info['fiftyTwoWeekHigh']          # 52-week high
ticker.info['fiftyTwoWeekLow']           # 52-week low
ticker.info['trailingPE']                # P/E ratio
ticker.info['forwardPE']                 # Forward P/E
ticker.info['dividendYield']             # Dividend yield
ticker.info['beta']                      # Beta vs S&P 500
```

**Warning**: Slow (makes full API call), returns 50+ fields

### `.fast_info` - Common Fields (FAST)

**When to use**: Price checks, volume, market cap (production use)

**Available fields**:
```python
fast = ticker.fast_info

fast['lastPrice']           # Most recent price
fast['previousClose']       # Yesterday's close
fast['open']                # Today's open
fast['dayHigh']             # Intraday high
fast['dayLow']              # Intraday low
fast['volume']              # Today's volume (same as lastVolume)
fast['lastVolume']          # Today's volume
fast['tenDayAverageVolume'] # 10-day avg volume
fast['threeMonthAverageVolume']

fast['marketCap']           # Market cap
fast['shares']              # Shares outstanding

fast['fiftyDayAverage']     # 50-day MA
fast['twoHundredDayAverage']# 200-day MA
fast['yearHigh']            # 52-week high
fast['yearLow']             # 52-week low
fast['yearChange']          # YTD % change

fast['currency']            # e.g., 'USD'
fast['exchange']            # e.g., 'NMS' (Nasdaq)
fast['timezone']            # e.g., 'EST'
fast['quoteType']           # e.g., 'EQUITY'
```

**Use this instead of `.info` for price data**

### `.history(period=..., interval=...)`

**When to use**: Charts, backtesting, technical analysis

**Parameters**:
```python
# Period (lookback)
period='1d'   # 1 day
period='5d'   # 5 days
period='1mo'  # 1 month
period='3mo'  # 3 months (default if omitted)
period='6mo'  # 6 months
period='1y'   # 1 year
period='2y'   # 2 years
period='5y'   # 5 years
period='10y'  # 10 years
period='ytd'  # Year-to-date
period='max'  # All available

# Interval (granularity)
interval='1m'  # 1 minute (only available for recent data)
interval='5m'  # 5 minutes
interval='15m' # 15 minutes
interval='1h'  # 1 hour
interval='1d'  # 1 day (default)
interval='1wk' # 1 week
interval='1mo' # 1 month
```

**Returns**: DataFrame with columns:
- `Open`, `High`, `Low`, `Close`, `Volume`
- `Dividends`, `Stock Splits`

**Example**:
```python
# Get daily data for last 3 months
hist = ticker.history(period='3mo')

# Get intraday 5-minute data for last 5 days
hist = ticker.history(period='5d', interval='5m')
```

## Events & Calendar

### `.calendar` - Upcoming Events

**When to use**: Earnings plays, dividend calendar, event-driven trades

**Returns**: Dictionary with:
```python
{
    'Earnings Date': [datetime.date(2025, 10, 30)],
    'Earnings Average': 1.76,        # Analyst consensus EPS
    'Earnings High': 1.83,           # High estimate
    'Earnings Low': 1.63,            # Low estimate
    'Revenue Average': 101707892750, # Analyst consensus revenue
    'Revenue High': 103220000000,
    'Revenue Low': 97854000000,
    'Dividend Date': datetime.date(2025, 8, 14),   # Payment date
    'Ex-Dividend Date': datetime.date(2025, 8, 11) # Ex-div date
}
```

**Use cases**:
- Next earnings: `calendar['Earnings Date'][0]`
- Earnings surprise potential: compare actual vs `Earnings Average`
- Dividend capture: check `Ex-Dividend Date`

**⚠️ Stocks only** (returns 404 for indices/crypto/futures)

### `.earnings_dates` - Historical Earnings Calendar

**When to use**: Backtest earnings surprise strategy

**Returns**: DataFrame with earnings dates and EPS

**Requires**: `lxml` package (`pip install lxml`)

## Analyst Coverage

### `.recommendations` - Buy/Hold/Sell Breakdown

**When to use**: Track analyst sentiment shifts

**Returns**: DataFrame with counts by period:
```
  period  strongBuy  buy  hold  sell  strongSell
0     0m          5   23    15     2           3   ← Current month
1    -1m          5   23    15     1           3   ← 1 month ago
2    -2m          5   22    15     1           1   ← 2 months ago
```

**Use cases**:
- Sentiment shift: compare 0m vs -1m (upgrades/downgrades)
- Contrarian signal: all strongSell → potential bottom?
- Crowded trade: all strongBuy → potential top?

### `.analyst_price_targets` - Consensus Price Target

**When to use**: Implied upside/downside, dispersion (uncertainty)

**Returns**: Dictionary:
```python
{
    'current': 252.29,  # Current price
    'high': 310.0,      # Highest analyst target
    'low': 175.0,       # Lowest analyst target
    'mean': 248.12,     # Average target
    'median': 245.0     # Median target
}
```

**Use cases**:
- Implied upside: `(mean - current) / current`
- Dispersion: `high - low` (wide = high uncertainty)
- Contrarian: if `current > high` → analysts haven't caught up?

### `.upgrades_downgrades` - Recent Rating Changes

**When to use**: Track momentum in analyst sentiment

**Returns**: DataFrame with firm, action, from, to

## Ownership & Flow

### `.institutional_holders` - Smart Money (13F Data)

**When to use**: Track Vanguard, Blackrock, etc. accumulation

**Returns**: DataFrame:
```
  Date Reported              Holder        Shares          Value  pctChange
0    2025-06-30  Vanguard Group Inc  ...  357225677614     0.0108
1    2025-06-30      Blackrock Inc.  ...  289840581073     0.0076
```

**Columns**:
- `Holder`: Institution name
- `Shares`: Number of shares held
- `Date Reported`: 13F filing date (quarterly, 45-day lag)
- `Value`: Position value ($)
- `pctChange`: Quarter-over-quarter change (e.g., 0.0108 = +1.08%)

**Use cases**:
- Smart money accumulation: positive `pctChange` for top holders
- Institutional support: high concentration = stable base?
- Flow divergence: institutions buying while stock down?

### `.insider_transactions` - Form 4 Data

**When to use**: Track insider buying/selling

**Returns**: DataFrame:
```
   Shares       Value  Transaction Start Date  Ownership
0  129963  33375723.0              2025-10-02          D
```

**Columns**:
- `Shares`: Number of shares transacted
- `Value`: Transaction value ($)
- `Transaction Start Date`: Date of transaction
- `Ownership`: 'D' = direct, 'I' = indirect
- `Text`: Buy/sell indicator (often in 'Text' or 'Transaction' column)

**Use cases**:
- Insider buying: Bullish signal (buying with own money)
- Insider selling: Neutral (could be diversification, not necessarily bearish)
- Cluster buying: Multiple insiders buying = high conviction?

### `.major_holders` - Ownership Breakdown

**When to use**: Quick ownership snapshot

**Returns**: DataFrame with % breakdowns

## Financials

### `.income_stmt` (or `.financials`) - Income Statement

**When to use**: Revenue growth, margin analysis, earnings quality

**Returns**: DataFrame with annual data (most recent 4 years)

**Key rows** (use `.loc[]` to access):
```python
income = ticker.income_stmt

income.loc['Total Revenue']           # Revenue
income.loc['Operating Income']        # Operating profit
income.loc['Net Income']              # Earnings
income.loc['EBITDA']                  # EBITDA
income.loc['Normalized EBITDA']       # EBITDA (normalized)
```

**Quarterly**: `ticker.quarterly_income_stmt`
**TTM** (trailing 12 months): `ticker.ttm_income_stmt`

**Use cases**:
- Revenue growth: compare latest vs prior years
- Operating margin: `Operating Income / Total Revenue`
- Net margin: `Net Income / Total Revenue`

### `.balance_sheet` - Balance Sheet

**When to use**: Leverage, cash position, bankruptcy risk

**Returns**: DataFrame with annual data

**Key rows**:
```python
balance = ticker.balance_sheet

balance.loc['Cash Cash Equivalents And Short Term Investments']
balance.loc['Total Debt']
balance.loc['Net Debt']  # Total Debt - Cash
balance.loc['Total Assets']
balance.loc['Stockholders Equity']
balance.loc['Ordinary Shares Number']  # Shares outstanding
```

**Quarterly**: `ticker.quarterly_balance_sheet`

**Use cases**:
- Leverage: `Total Debt / Stockholders Equity`
- Cash runway: `Cash / (Operating expenses / 4)` (quarters)
- Net debt: `Total Debt - Cash` (negative = net cash position)
- Share count: track buybacks/dilution over time

### `.cash_flow` - Cash Flow Statement

**When to use**: FCF analysis, buyback activity, capital allocation

**Returns**: DataFrame with annual data

**Key rows**:
```python
cashflow = ticker.cash_flow

cashflow.loc['Free Cash Flow']
cashflow.loc['Repurchase Of Capital Stock']  # Buybacks (negative = outflow)
cashflow.loc['Repayment Of Debt']            # Debt paydown (negative = outflow)
cashflow.loc['Issuance Of Debt']             # Debt issuance (positive = inflow)
```

**Quarterly**: `ticker.quarterly_cash_flow`
**TTM**: `ticker.ttm_cash_flow`

**Use cases**:
- FCF yield: `Free Cash Flow / Market Cap`
- Buyback rate: `Repurchase Of Capital Stock / Market Cap`
- Capital allocation: buybacks vs debt paydown vs dividends?

## Options

### `.options` - Available Expiration Dates

**When to use**: Check what expirations are available

**Returns**: Tuple of date strings:
```python
('2025-10-24', '2025-10-31', '2025-11-07', ...)
```

### `.option_chain(date)` - Calls & Puts Data (Raw)

**When to use**: Get raw option chain data

**Returns**: Object with `.calls` and `.puts` DataFrames

**Example**:
```python
dates = ticker.options
chain = ticker.option_chain(dates[0])  # Nearest expiration

calls = chain.calls  # Calls DataFrame
puts = chain.puts    # Puts DataFrame
```

**Columns** (both calls and puts):
- `strike`: Strike price
- `lastPrice`: Last traded price
- `bid`, `ask`: Current bid/ask
- `volume`: Today's volume
- `openInterest`: Open interest
- `impliedVolatility`: Implied volatility

**⚠️ Missing from yfinance:**
- Greeks (delta, gamma, vega, theta, rho) - Yahoo doesn't provide
- Real-time data (15-20 min delay)
- Bid/ask spreads (only last price reliable)
- Historical options data

### `ticker_options()` MCP Tool - Comprehensive Analysis (Implemented)

**Our implementation adds extensive analytics on top of raw yfinance data:**

**Positioning:**
- P/C ratio (OI and volume)
- ITM/OTM breakdown with percentages
- Top 10 strikes by OI (calls + puts side-by-side)
- Top 10 strikes by volume

**IV Analysis:**
- ATM IV for calls/puts
- Vol skew (OTM vs ATM)
- Term structure (near/mid/far expirations)
- Historical IV context (30-day hist vol, 52-week range, IV rank percentile)

**Advanced Analytics:**
- Max pain calculation (strike minimizing option seller losses)
- Unusual activity detection (volume > 2x OI)
- All expirations summary (IV/OI/volume for all dates)
- Context-based interpretation (NO recommendations)

**Example output:**
```
AAPL US EQUITY                          OPTIONS ANALYSIS
Last: $150.25                           Exp: 2025-01-17 (55d)  |  ATM: $150

POSITIONING (Open Interest)
Calls:  125,000 OI
Puts:   95,000 OI
P/C Ratio:  0.76    ← BULLISH (calls 1.3x puts)

TOP POSITIONS BY OI (Top 10)
CALLS
Strike    OI      Vol     Last      IV
──────────────────────────────────────────────
$150   10,250  5,120   $5.20   28.5%
$155    8,500  3,200   $2.80   30.1%
...

IMPLIED VOLATILITY
ATM Calls:     28.5%
ATM Puts:      27.8%
Spread:        +0.7% calls

VOL SKEW
OTM Puts vs ATM:  +2.1%
OTM Calls vs ATM: +1.3%

TERM STRUCTURE
Near (55d):    28.5%       ← Current
Mid (90d):     26.2%
Far (180d):    24.8%
Contango:     +3.7%       ← Market expects compression

UNUSUAL ACTIVITY (Vol > 2x OI)
Unusual Call Strikes: 3
Top Unusual Calls:
  $160  Vol:15,000  OI:5,000  Ratio:3.0x
...

HISTORICAL IV CONTEXT
Current ATM IV:  28.5%
30-Day Hist Vol: 25.2%
52-Week IV Range: 18.5% - 42.3%
IV Rank:  42%  (percentile in 52-week range)

ALL EXPIRATIONS (8 available)
Exp Date       DTE     IV     Total OI    Total Vol
─────────────────────────────────────────────────────
2025-01-17    55d   28.5%    220,000      18,500
2025-02-21    90d   26.2%    185,000      12,300
...
```

**See:** `yfinance_ux/services/options.py` for implementation

## SEC Filings

### `.sec_filings` - Recent Filings

**When to use**: Link to 10-K/10-Q/8-K, track filing dates

**Returns**: List of dictionaries:
```python
[
    {
        'date': datetime.date(2025, 8, 1),
        'type': '10-Q',
        'title': 'Periodic Financial Reports',
        'edgarUrl': 'https://...',  # Yahoo Finance filing page
        'exhibits': {
            '10-Q': 'https://...',  # Direct filing URL
            'EX-31.1': 'https://...',
            ...
        }
    },
    ...
]
```

**Use cases**:
- Find latest 10-K: `[f for f in filings if f['type'] == '10-K'][0]`
- Get 10-Q URL: `filing['exhibits']['10-Q']`
- Track filing schedule: `filing['date']`
- Combine with bitter-edgar MCP for full text analysis

## Deprecated / Broken

### `.news` - Recent News (BROKEN)

**Status**: Returns articles but titles are `None` (API issue)

**Use alternative**: NewsAPI, Google News, or other news sources

### `.earnings` - Earnings History (DEPRECATED)

**Status**: Deprecated warning, use `.income_stmt` instead

**Message**: `'Ticker.earnings' is deprecated as not available via API. Look for "Net Income" in Ticker.income_stmt.`

## Performance Notes

- **`.info` is slow** (~1-2 seconds) - use `.fast_info` for price data
- **`.history()` is fast** for daily data, slower for intraday
- **Financials are slow** (~2-3 seconds) - cache if possible
- **Data is delayed 15-20 minutes** (not real-time)
- **No API key required** (free tier, but rate limits exist)

## Common Patterns

### Get current price (fast)
```python
ticker = yf.Ticker('AAPL')
price = ticker.fast_info['lastPrice']
```

### Get next earnings date
```python
ticker = yf.Ticker('AAPL')
calendar = ticker.calendar
next_earnings = calendar['Earnings Date'][0]  # datetime.date object
```

### Check insider buying
```python
ticker = yf.Ticker('AAPL')
insider = ticker.insider_transactions
recent_buys = insider[insider['Shares'] > 0]  # Positive = buy
```

### Calculate FCF yield
```python
ticker = yf.Ticker('AAPL')
fcf = ticker.cash_flow.loc['Free Cash Flow'].iloc[0]  # Most recent year
market_cap = ticker.fast_info['marketCap']
fcf_yield = fcf / market_cap
```

### Get analyst upside
```python
ticker = yf.Ticker('AAPL')
targets = ticker.analyst_price_targets
current = targets['current']
mean_target = targets['mean']
upside = (mean_target - current) / current  # % upside to target
```

## Implications for Idio Capital Allocation System

### Current MCP Scope (Market Snapshot) ✅

**Appropriate for:**
- Broad market factors (S&P, Nasdaq, Dow)
- Risk factors (Gold, Bitcoin, VIX)
- Commodity factors (Oil, Nat Gas)
- Rate factors (10Y yield)

**Using:** Price/change only (which is all that's available for indices/commodities/crypto)

**Verdict:** Current implementation is appropriate for market snapshot use case

### Stock-Specific Analysis (Future Tools)

**When analyzing individual stock opportunities** (TSLA, MP, etc.), we could add:

1. **Earnings Calendar Tool** - Next earnings date, analyst estimates, surprise potential
2. **Analyst Sentiment Tool** - Consensus, price targets, upgrades/downgrades
3. **Insider Activity Tool** - Recent transactions, buying vs selling
4. **Institutional Flow Tool** - Smart money accumulation (13F data)
5. **Financials Tool** - Revenue growth, margins, FCF, leverage
6. **Options Activity Tool** - IV, put/call ratio, unusual volume
7. **SEC Filings Tool** - Links to 10-K/10-Q/8-K (combine with bitter-edgar MCP)

## Recommended Next Steps

### Phase 1: Current State (Market Snapshot) ✅ Complete

- Market factor view (Paleologo framework)
- Auto-detect market hours
- BBG Lite formatting

### Phase 2: Earnings Calendar (Event-Driven)

**Effort:** Low (1-2 hours)
**Value:** High (timing is critical for event-driven trades)

Add earnings calendar to market snapshot:
```
UPCOMING EARNINGS
Oct 22    TSLA    Est $0.55    Rev $26.6B
Oct 30    AAPL    Est $1.76    Rev $101.7B
```

### Phase 3: Stock Analysis Tools (Conviction Scoring)

**Effort:** Medium (4-8 hours)
**Value:** High (feeds into position sizing)

Add new tool: `analyze_stock(symbol)`

Returns:
- Current price + analyst targets (upside/downside)
- Next earnings (date + estimates)
- Insider activity (recent buying/selling)
- Institutional flow (smart money accumulation?)
- Financials snapshot (revenue growth, FCF, leverage)

Output format: BBG Lite style (concise, scannable)

### Phase 4: Integration with Friction Frontier

**Effort:** High (depends on thesis structure)
**Value:** Very High (core system value)

Combine yfinance data with:
- Friction Frontier analysis (from theses repo)
- Compliance checks (Bridgewater restrictions)
- Position sizing (Paleologo proportional rule)
- Risk management (stop-loss, leverage)

### Phase 5: Options & Advanced

**Effort:** High (complex analysis)
**Value:** Medium (nice-to-have, not critical path)

- Options activity tracking
- Implied volatility analysis
- Put/call ratio sentiment

## References

- Package: https://pypi.org/project/yfinance/
- Source: https://github.com/ranaroussi/yfinance
- Unofficial Yahoo Finance API wrapper (sometimes breaks)
- Exploration script: `explore_yfinance.py` (in this directory)
