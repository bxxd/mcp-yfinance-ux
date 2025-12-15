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
