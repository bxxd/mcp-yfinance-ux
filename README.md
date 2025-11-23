# mcp-yfinance-ux

**For AI agents:** Market data in Bloomberg Terminal format. Not raw JSON - I give you formatted tables you can read directly. Navigate like BBG: `markets()` → `sector('technology')` → `ticker('AAPL')` → `ticker_options('AAPL')`. Smart defaults (auto-detects market hours), progressive disclosure (summary → detail).

**For humans:** Dense, scannable screens. Factor exposures, momentum, options positioning - all formatted like a professional terminal.

**Technical:** Local stdio server, powered by yfinance. All queries user-initiated (no automation - this is a research tool, not production infrastructure).

## Example Output

**Our differentiator: BBG Lite formatted, agent-friendly screens**

```
MARKETS | Sun 2025-10-26 12:42 EDT

US EQUITIES                   PRICE     CHANGE       1M         1Y
S&P 500                      6791.69    +0.79%     +2.2%     +16.9%
Nasdaq                      23204.87    +1.15%     +3.2%     +25.3%
Dow                         47207.12    +1.01%     +2.1%     +12.1%
Russell 2000                 2513.47    +1.24%     +3.3%     +13.8%

SECTORS          TICKER      PRICE     CHANGE       1M         1Y
Technology       XLK          293.58    +1.23%     +5.3%     +28.3%
Financials       XLF           53.11    +0.84%     -1.4%     +15.6%
Healthcare       XLV          146.03    -0.05%     +7.8%      +0.0%
Energy           XLE           88.07    -1.01%     -4.3%      +1.4%
[... all 11 GICS sectors]

COMMODITIES                   PRICE     CHANGE       1M         1Y
Gold                         4137.80    +0.05%     +9.6%     +51.0%
Oil WTI                        61.50    +0.10%     -6.4%     -14.3%

Data as of 2025-10-26 12:42 EDT | Source: yfinance
```

Dense, scannable, professional. Not raw JSON - formatted for humans, AI benefits automatically.

## Features

**Bloomberg Terminal-style navigation screens for market data:**

- **markets()** - Complete factor landscape (US equities, global, sectors, styles, commodities, volatility)
- **sector(name)** - Sector drill-down with top holdings and factor exposures
- **ticker(symbol)** - Individual security analysis with full factor decomposition
- **Batch comparison** - Side-by-side stock analysis with key factors
- **Calendar integration** - Earnings dates, dividend schedules
- **BBG Lite formatting** - Dense, scannable, professional output

## Library Architecture

**mcp-yfinance-ux includes a reusable library for reliable yfinance data fetching.**

### lib/yfinance_fetcher.py

**ONE SOURCE OF TRUTH for yfinance fetching logic:**
- Individual `yf.Ticker().history()` calls with ThreadPoolExecutor (RELIABLE)
- NOT `yf.download()` batch API (UNRELIABLE - timeouts, fails entire batch)

**Used by:**
1. **MCP server** - `mcp_yfinance_ux/historical.py` imports from `lib/`
2. **Portfolio scripts** - Can be copied to portfolio agents for reliable fetching
3. **Any Python code** - Pure logic, no MCP dependencies

**Key functions:**
- `fetch_price_history(symbol, months=12)` - Single symbol history
- `fetch_multiple_histories(symbols, months=12)` - Parallel multi-symbol fetch
- `fetch_ticker_and_market(symbol, months=12)` - Ticker + market data (for factor analysis)
- `fetch_price_at_date(symbol, date)` - Price at specific date (narrow window)

**Why this pattern works:**
- Individual fetches don't fail as a batch
- ThreadPoolExecutor provides parallelism without batch API
- Proven in production use (MCP server serving real users)

**Documentation:** See `lib/README.md` for usage examples and deployment workflow.

## Important: Usage Limitations

**This tool is designed for ad-hoc, user-initiated requests only. Not for automation.**

### What yfinance Is

**yfinance is an unofficial web scraper**, not a sanctioned Yahoo Finance API. It mimics browser requests to fetch financial data.

**Implications:**
- **Can break at any time** - Yahoo site changes can break the library entirely
- **No official rate limits** - Because it's not an official API
- **Prone to blocking** - Automated polling or high-volume requests trigger Yahoo's anti-scraping measures (429 errors, IP bans)
- **No guarantees** - Yahoo tightened restrictions significantly around early 2024

### Safe Usage (What This Tool Does)

**✅ Appropriate use cases:**
- Ad-hoc market checks and analysis
- One-off stock research
- Manual thesis development
- Occasional queries for specific data

All queries are **user-initiated** and interactive.

### Unsafe Usage (Don't Do This)

**❌ Never use this for:**
- Cron jobs or scheduled updates
- Automated monitoring loops
- Background processes polling for data
- Production infrastructure
- Real-time portfolio tracking

**If you need automation or production-grade data, use official APIs instead** (Alpha Vantage, Polygon.io, IEX Cloud, etc.)

### Bottom Line

This MCP server is a **research tool for occasional queries**, not production infrastructure. Perfect for PMF testing and ad-hoc analysis. Not suitable for automation or continuous monitoring.

## Installation

### 1. Clone and install dependencies

```bash
git clone https://github.com/bxxd/idio-mcp-yfinance-ux.git
cd idio-mcp-yfinance-ux
poetry install
```

### 2. Configure MCP Client

**Note:** This is a local stdio MCP server. It runs on your machine and connects to MCP clients via standard I/O (not HTTP/network). All data stays local.

**Method 1: Using make -C (recommended)**

From your project directory:

```bash
claude mcp add idio-yf make -C /absolute/path/to/mcp-yfinance-ux serve
```

Or manually add to `~/.claude.json` under your project's `mcpServers`:

```json
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "idio-yf": {
          "type": "stdio",
          "command": "make",
          "args": ["-C", "/absolute/path/to/mcp-yfinance-ux", "serve"],
          "env": {}
        }
      }
    }
  }
}
```

**Why this approach?**
- Single source of truth (Makefile defines the server command)
- No need to remember poetry/python invocation details
- Self-documenting (Makefile is version controlled)
- Works from any directory (make -C handles working directory)

**Method 2: Direct command (alternative)**

If you prefer not to use make:

```bash
claude mcp add idio-yf poetry run python -m mcp_yfinance_ux.server --cwd /path/to/mcp-yfinance-ux
```

Or manually:

```json
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "idio-yf": {
          "type": "stdio",
          "command": "poetry",
          "args": ["run", "python", "-m", "mcp_yfinance_ux.server"],
          "cwd": "/absolute/path/to/mcp-yfinance-ux",
          "env": {}
        }
      }
    }
  }
}
```

**Note:** For claude CLI users, MCP servers are configured per-project in `~/.claude.json`. Other MCP clients may have different configuration methods.

**Method 3: SSE/HTTP Server (for web-based deployments)**

For web interfaces or when you need a persistent HTTP server:

```bash
# Start HTTP server (runs in background on port 5001)
make server

# Or specify custom port
PORT=8080 make server

# Check logs
make logs
```

Configure Claude Code to use SSE transport:

```json
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "yfinance-ux": {
          "type": "sse",
          "url": "http://127.0.0.1:5001/sse"
        }
      }
    }
  }
}
```

**When to use SSE:**
- Web-based Claude Code deployments (e.g., browser terminals)
- Multiple clients sharing one server instance
- Debugging without restarting Claude Code

**When to use stdio:**
- Local CLI usage (standard approach)
- Single-user development environment

### 3. Restart MCP Client

After configuration, restart your MCP client to load the server.

**How it works:**
- **stdio mode:** MCP client launches server as subprocess, communicates via stdin/stdout
- **SSE mode:** MCP client connects to persistent HTTP server via Server-Sent Events

## Usage

**Navigation hierarchy like Bloomberg Terminal:**

```
markets() → sector('technology') → ticker('AAPL')
```

### markets() - Market Overview

Complete factor landscape with no parameters:

```python
mcp__idio_yf__markets()
```

**Shows:**
- **US EQUITIES** - S&P 500, Nasdaq, Dow, Russell 2000 (with Beta, 1M/1Y momentum)
- **GLOBAL** - Europe (STOXX 50), Asia (Nikkei), China (Shanghai)
- **SECTORS** - All 11 GICS sectors (XLK, XLF, XLV, etc.) with Beta and momentum
- **STYLES** - Momentum (MTUM), Value (VTV), Growth (VUG), Quality (QUAL), Size (IWM)
- **COMMODITIES** - Gold, Oil, Natural Gas (with Beta and momentum)
- **VOLATILITY & RATES** - VIX, 10Y Treasury

Auto-detects market hours (shows futures after hours, indices during market).

### sector(name) - Sector Drill-Down

Detailed sector analysis with top holdings:

```python
mcp__idio_yf__sector(name='technology')
```

**Shows:**
- Sector ETF price and momentum (1M, 1Y)
- Beta to SPX, idiosyncratic volatility
- Top 10 holdings with symbol, name, weight, and individual betas

**Available sectors:**
`technology`, `financials`, `healthcare`, `energy`, `consumer_disc`, `consumer_stpl`, `industrials`, `utilities`, `materials`, `real_estate`, `communication`

### ticker(symbol) - Individual Security Analysis

Complete factor decomposition for stocks:

```python
mcp__idio_yf__ticker(symbol='AAPL')
```

**Shows:**
- **Factor Exposures** - Beta (SPX), idiosyncratic volatility, total volatility
- **Valuation** - P/E ratio, forward P/E, dividend yield
- **Calendar** - Next earnings date with estimates, ex-dividend date, payment date
- **Momentum & Technicals** - 1M/1Y returns, RSI (14D), 50/200-day moving averages
- **52-Week Range** - Visual bar showing current position

### Batch Comparison

Side-by-side stock comparison:

```python
mcp__idio_yf__ticker(symbol=['TSLA', 'F', 'GM'])
```

**Table format showing:** Symbol, Name, Price, Change%, Beta, Idio Vol, 1Y Momentum, P/E, Dividend Yield, RSI

## Output Format

**BBG Lite style** - Dense, scannable, professional formatting like Bloomberg Terminal.

**Example ticker() output:**

```
AAPL US EQUITY                   LAST PRICE  262.24 +9.95  +3.94%
Apple Inc.                               MKT CAP  3891.7B    VOLUME  90.1M

FACTOR EXPOSURES
Beta (SPX)       1.09
Idio Vol         21.7%
Total Vol        32.8%

VALUATION
P/E Ratio         39.85
Forward P/E       31.56
Dividend Yield    0.40%

CALENDAR
Earnings         Oct 30, 2025  (Est $1.77 EPS)
Ex-Dividend      Aug 11, 2025
Div Payment      Aug 14, 2025

MOMENTUM & TECHNICALS
1-Month            +6.8%
1-Year            +11.4%
50-Day MA         241.73
200-Day MA        222.14
RSI (14D)         59.5

52-WEEK RANGE
High              264.38
Low               169.21
Current           262.24  [===================░]  98% of range
```

**Example batch comparison:**

```
TICKER COMPARISON 2025-10-21 08:42 EDT

SYMBOL   NAME                                PRICE     CHG%   BETA   IDIO    MOM1Y      P/E   DIV%    RSI
---------------------------------------------------------------------------------------------------------
AAPL     Apple Inc.                         262.24   +3.94%   1.09  21.7%   +11.4%    39.85  0.40%   59.5
MSFT     Microsoft Corporation              516.79   +0.63%   1.02  17.0%   +24.3%    37.89  0.70%   48.8
GOOGL    Alphabet Inc.                      256.55   +1.28%   1.00  25.5%   +57.1%    27.32  0.33%   66.1
```

Clean, readable, immediately useful.

## Development

### Quick Start

**Using Makefile (recommended):**

```bash
make all        # Run lint + test (ALWAYS before committing)
make test       # Run tests
make lint       # Run type checking + linting
make lint-fix   # Auto-fix linting issues
make serve      # Run MCP server (stdio mode)
make help       # Show all commands
```

**Manual testing (no MCP required):**

```bash
# Test screens via CLI (no MCP restart needed)
./cli markets
./cli sector technology
./cli ticker AAPL
./cli ticker TSLA F GM    # Batch comparison
```

### Documentation

- **DEVELOPER.md** - Design philosophy, engineering principles, development process
- **CLAUDE.md** - Additional context and development notes

### Design Principles

- **Separation of Concerns** - Business logic has zero MCP dependencies
- **Single Source of Truth** - One true path for every piece of data/logic
- **Human-Readable Output** - Format for humans, not machines
- **Keep It Simple** - Match manual testing exactly, no overengineering

## License

MIT
