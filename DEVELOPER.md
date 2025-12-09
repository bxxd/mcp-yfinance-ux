# yfinance MCP Server

MCP server for Yahoo Finance market data.

## Quick Start

```bash
make all        # lint + test (before committing)
make server     # Start HTTP server (port 5001)
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
- `mcp_yfinance_ux/market_data.py` - Business logic
- `mcp_yfinance_ux/tools.py` - MCP tool definitions
- `mcp_yfinance_ux/server_http.py` - HTTP/SSE transport

## Tools

Four screen-based tools:

**markets()** - Market overview with indices, sectors, styles, commodities, rates. Shows momentum (1M, 1Y).

**sector(name)** - Sector ETF + top 10 holdings with weights, prices, momentum.

**ticker(symbol)** - Single or batch comparison. Shows factors (beta, idio vol), valuation (P/E), momentum (1W, 1M, 1Y), technicals (MA, RSI), 52wk range, options summary.

**ticker_options(symbol, expiration)** - Options analysis. Shows OI positioning, top strikes, IV structure, skew, term structure, max pain, unusual activity (volume > 2x OI).

Output: BBG Lite format (dense, scannable text)

## Core Principles

### Separation of Concerns
Business logic (market_data.py) has zero MCP dependencies. Protocol layer is just routing.

### Single Source of Truth
Import, don't duplicate. Data fetching in yfinance_ux, tool definitions in tools.py.

### UI Not API
Screen-based tools match Bloomberg Terminal flow (markets → sector → ticker), not REST endpoints.

### Strict Type Checking
Zero mypy/ruff warnings. Catch errors at dev time.

## Performance

- `fast_info` instead of `ticker.info` (faster)
- Narrow window momentum (22 days vs 252 days)
- Parallel fetching (ThreadPoolExecutor)
- Batch API (`yf.Tickers()`)

## File Structure

```
mcp-yfinance-ux/
├── yfinance_ux/              # Pure library
│   ├── fetcher.py            # Historical data
│   ├── common/               # Symbols, dates, constants
│   ├── calculations/         # Momentum, volatility, RSI
│   └── services/             # Market data, tickers, sectors, options
├── mcp_yfinance_ux/          # MCP server
│   ├── server_http.py        # HTTP/SSE transport
│   ├── market_data.py        # Business logic
│   ├── tools.py              # MCP tool definitions
│   ├── cli.py                # CLI for testing
│   └── formatters/           # BBG Lite output
├── tests/                    # Tests
├── Makefile                  # Dev commands
└── pyproject.toml            # Poetry config
```

## Development Workflow

```bash
# Code quality (ALWAYS before committing)
make all        # lint + test (must pass)
make lint       # mypy + ruff
make test       # run tests
make lint-fix   # auto-fix issues

# Server management
make server     # Start server (HTTP port 5001)
make logs       # Tail logs (logs/server.log)
```

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
