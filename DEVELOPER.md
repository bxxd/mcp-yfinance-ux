# yfinance MCP Server

MCP server for Yahoo Finance market data.

## Quick Start

```bash
make all        # lint + test (before committing)
make server     # Start HTTP server (port 5011 dev, 5001 prod)
make logs       # Tail logs

./cli ticker TSLA              # Test single
./cli ticker TSLA F GM         # Test batch
./cli options PALL             # Test options
```

## Architecture

Two packages:
- `yfinance_ux/` - Pure library (no MCP deps)
- `mcp_yfinance_ux/` - MCP server (imports yfinance_ux)

Key files:
- `yfinance_ux/fetcher.py` - Historical data (individual `yf.Ticker().history()`)
- `mcp_yfinance_ux/market_data.py` - Business logic (data fetching + formatting)
- `mcp_yfinance_ux/handlers.py` - Tool routing (single source of truth for call_tool)
- `mcp_yfinance_ux/tools.py` - MCP tool definitions
- `mcp_yfinance_ux/server.py` - stdio transport (Claude Code direct)
- `mcp_yfinance_ux/server_http.py` - HTTP/SSE transport (multi-tenant)

## Tools

Four screen-based tools:

**markets()** - Market overview with indices, sectors, styles, commodities, rates. Shows momentum (1M, 1Y).

**sector(name)** - Sector ETF + top 10 holdings with weights, prices, momentum.

**ticker(symbol)** - Single or batch comparison. Shows factors (beta, idio vol), valuation (P/E), momentum (1W, 1M, 1Y), technicals (MA, RSI), 52wk range, options summary.

**ticker_options(symbol, expiration)** - Options analysis. Shows OI positioning, top strikes, IV structure, skew, term structure, max pain, unusual activity (volume > 2x OI).

Output: BBG Lite format (dense, scannable text)

## Core Principles

### Hexagonal Architecture
```
             ┌─────────────┐
             │   cli.py    │  CLI entry point
             └──────┬──────┘
                    │
             ┌──────▼──────┐
┌────────┐   │ handlers.py │   ┌──────────────┐
│server.py│──►│  call_tool  │◄──│server_http.py│
│ (stdio) │   │ (routing)   │   │  (HTTP/SSE)  │
└────────┘   └──────┬──────┘   └──────────────┘
                    │
             ┌──────▼──────┐
             │market_data.py│  Business logic
             └──────┬──────┘
                    │
             ┌──────▼──────┐
             │ yfinance_ux │  Pure data library
             └─────────────┘
```

### Separation of Concerns
Business logic (market_data.py) has zero MCP dependencies. Protocol layer is just routing.

### Single Source of Truth
Import, don't duplicate. Tool routing in handlers.py, data fetching in yfinance_ux, tool definitions in tools.py.

### UI Not API
Screen-based tools match Bloomberg Terminal flow (markets → sector → ticker), not REST endpoints.

### Strict Type Checking
Zero mypy/ruff warnings. Catch errors at dev time.

## Performance

- `fast_info` instead of `ticker.info` (faster)
- Narrow window momentum (22 days vs 252 days)
- Parallel fetching (ThreadPoolExecutor)
- Batch API (`yf.Tickers()`)
- **Market-aware caching** (skip API calls for closed markets)

## Caching (Design Decision)

**markets() uses intelligent caching to reduce API calls without stale data.**

### Why Cache?

After US market close (4pm ET):
- **Session markets** (US equities, global indices, ETFs) → prices frozen until next open
- **24-hour markets** (crypto, futures) → prices continuously updating

Without caching, we'd make 50+ API calls to yfinance for markets() even when most data is stale.

### Caching Strategy

**Session markets** (cache until next market open ~9:30am ET):
- US Equities: ^GSPC, ^IXIC, ^DJI, ^RUT
- Global indices: ^N225, ^HSI, ^STOXX50E, etc.
- Sector/Style ETFs: XLK, XLF, MTUM, VTV, etc.
- Rationale: Prices won't change until market reopens

**24-hour markets** (cache for 2 minutes):
- Crypto: BTC-USD, ETH-USD, SOL-USD
- Commodities futures: GC=F, CL=F, NG=F, etc.
- US Futures: ES=F, NQ=F, YM=F
- Rationale: Prices change 24/7, need fresh data

**VIX & Rates** (cache until next open):
- ^VIX, ^TNX
- Derivatives of session markets, won't change after hours

### Implementation

**Location**: `mcp_yfinance_ux/cache.py` (MCP layer, not pure library)

**How it works**:
1. Before fetching symbol data, check in-memory cache
2. If cached and not expired, return cached data (skip API call)
3. If cache miss, fetch from yfinance and cache with market-aware TTL
4. Cache expires based on symbol type (2 min for 24-hour, next open for session)

**API call savings** (after hours):
- Without cache: ~50 API calls per markets() request
- With cache: ~10 API calls (only 24-hour markets + cache misses)
- Savings: ~80% reduction in API calls during off-hours

### Trade-offs

**Pros**:
- Massive API call reduction during off-hours
- Faster response time (no network latency for cached data)
- Reduced rate limit pressure on yfinance
- Zero staleness risk (session markets literally can't change)

**Cons**:
- Memory usage (minimal - ~50 symbols × ~500 bytes = 25KB)
- Complexity (60 lines of cache logic)

**Decision**: Benefits far outweigh costs. yfinance is an unofficial scraper with rate limits. Caching is essential for production use.

## RVOL Time Windows (Design Decision)

**markets() uses 10-day average, ticker() uses 3-month average - this is intentional!**

### Why Different Time Windows?

**markets() - 10-day average (fast_info.tenDayAverageVolume):**
- **Rationale**: FREE - already fetching fast_info for price data, no extra API call
- **Purpose**: Quick market scan to spot recent momentum shifts
- **Use case**: "What's heating up in the last 2 weeks?"
- **Trade-off**: More sensitive to recent quiet/hot periods

**ticker() - 3-month average (info.averageVolume):**
- **Rationale**: FREE - already fetching info for P/E, market cap, earnings, etc.
- **Purpose**: Detailed analysis with stable baseline to filter noise
- **Use case**: "What's normal volume for this stock?"
- **Trade-off**: Less sensitive to recent shifts, more reliable context

### Example: Why This Matters

XLK on a quiet week (Dec 17, 2025):
- **markets() shows 1.5x RVOL** - "Hot vs recent 2-week trend" (last 10 days were unusually quiet)
- **ticker() shows 0.8x RVOL** - "Below normal vs 3-month baseline" (actually lower than usual)

Both are correct! They answer different questions:
- markets() = "Is this moving NOW?"
- ticker() = "Is this unusual for THIS stock?"

### API Cost

Switching to same time window would require:
- **Extra API call** per symbol (either info or history)
- **Higher latency** (additional network round trip)
- **Rate limit pressure** (yfinance caps requests)
- **No benefit** (different tools serve different purposes)

Current approach: **0 extra API calls** - both averages come free with existing data fetches.

## File Structure

```
mcp-yfinance-ux/
├── yfinance_ux/              # Pure library (no MCP deps)
│   ├── fetcher.py            # Historical data
│   ├── common/               # Symbols, dates, constants
│   ├── calculations/         # Momentum, volatility, RSI
│   └── services/             # Market data, tickers, sectors, options
├── mcp_yfinance_ux/          # MCP server
│   ├── handlers.py           # Tool routing (single source of truth)
│   ├── market_data.py        # Business logic (fetch + format)
│   ├── tools.py              # MCP tool definitions
│   ├── server.py             # stdio transport
│   ├── server_http.py        # HTTP/SSE transport
│   ├── cli.py                # CLI for testing
│   └── formatters/           # BBG Lite output
├── tests/                    # Tests
├── Makefile                  # Dev commands
└── pyproject.toml            # Poetry config
```

## Development Workflow

All commands in @Makefile:

```bash
# Code quality (ALWAYS before committing)
make all        # lint + test (must pass)
make lint       # mypy + ruff
make test       # run tests
make lint-fix   # auto-fix issues

# Server management
make server     # Start server (HTTP port 5011 dev, 5001 prod)
make logs       # Tail logs (logs/server.log)
```

See @Makefile for all commands.

Log format: `[YYYY/MM/DD HH:MM:SS:XXXX] [LEVEL] message`

## Library Maintenance Workflow

When updating `yfinance_ux/` library:

1. Edit the library
2. Test: `make all && ./cli ticker TSLA`
3. System-wide via `.pth` file - changes immediately available to all users

## Installation

`yfinance_ux` library is system-wide installable (zero MCP deps). Other projects can import:

```python
from yfinance_ux.fetcher import fetch_price_at_date
from yfinance_ux.calculations import calculate_momentum
```

MCP server imports from yfinance_ux. Poetry manages dependencies.

## yfinance Constraints

yfinance is an unofficial web scraper.

Safe:
- User-initiated queries only
- One-off analysis
- Human in the loop

Unsafe:
- Cron jobs
- Background processes
- Automated scraping

For automation: migrate to official APIs.
