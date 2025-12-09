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
- `markets()` - Market overview (indices, sectors, styles, commodities, rates)
- `sector(name)` - Sector ETF + top 10 holdings
- `ticker(symbol)` - Single or batch comparison (factors, valuation, technicals, options)
- `ticker_options(symbol, expiration)` - Options analysis (OI, IV, skew, unusual activity)

Output: BBG Lite format (dense, scannable text)

## Core Principles

1. **Separation** - Business logic has zero MCP deps
2. **Single source of truth** - Import, don't duplicate
3. **UI not API** - Screen-based tools (markets → sector → ticker)
4. **Strict types** - Zero mypy/ruff warnings

## Performance

- `fast_info` instead of `ticker.info` (faster)
- Narrow window momentum (22 days vs 252 days)
- Parallel fetching (ThreadPoolExecutor)
- Batch API (`yf.Tickers()`)

## Development

```bash
make all        # lint + test (must pass before commit)
make server     # Start server
make logs       # View logs (logs/server.log)
```

Log format: `[YYYY/MM/DD HH:MM:SS:XXXX] [LEVEL] message`

## Installation

System-wide via `.pth` file: `/usr/local/lib/python3.12/dist-packages/yfinance-ux.pth`

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
