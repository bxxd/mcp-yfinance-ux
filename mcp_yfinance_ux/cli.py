#!/usr/bin/env python3
"""
CLI for yfinance MCP - test screens without MCP restart

Usage:
  ./cli list-tools           # Show MCP tool definitions
  ./cli markets              # Market overview screen
  ./cli sector technology    # Sector drill-down screen
  ./cli ticker TSLA          # Individual ticker screen (detailed)
  ./cli ticker TSLA F GM     # Batch comparison (table format)
  ./cli options PALL         # Options chain analysis (nearest expiration)
  ./cli options PALL 2025-12-20  # Options for specific expiration

Fast iteration: Calls market_data.py functions directly (no MCP layer)
"""

import argparse
import asyncio
import json
import sys

from .market_data import (
    format_markets,
    format_options,
    format_sector,
    format_ticker,
    format_ticker_batch,
    get_markets_data,
    get_options_data,
    get_sector_data,
    get_ticker_screen_data,
    get_ticker_screen_data_batch,
)
from .server import list_tools


async def list_tools_command() -> int:
    """Show MCP tool definitions"""
    tools = await list_tools()

    print("=" * 80)
    print("MCP TOOL DEFINITIONS")
    print("=" * 80)
    print()

    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"Claude sees: mcp__idio-yf__{tool.name}")
        print()
        print("Description:")
        print(tool.description)
        print()
        print("Input Schema:")
        print(json.dumps(tool.inputSchema, indent=2))
        print()

    return 0


def markets_command() -> int:
    """Show markets() screen"""
    data = get_markets_data()
    output = format_markets(data)
    print(output)
    return 0


def sector_command(name: str) -> int:
    """Show sector() screen"""
    data = get_sector_data(name)
    output = format_sector(data)
    print(output)
    return 0


def ticker_command(symbols: list[str]) -> int:
    """Show ticker() screen - single or batch mode"""
    if len(symbols) == 1:
        # Single ticker mode
        data = get_ticker_screen_data(symbols[0])
        output = format_ticker(data)
        print(output)
    else:
        # Batch comparison mode - use batch API (same as MCP server)
        data_list = get_ticker_screen_data_batch(symbols)
        output = format_ticker_batch(data_list)
        print(output)
    return 0


def options_command(symbol: str, expiration: str = "nearest") -> int:
    """Show options() screen"""
    data = get_options_data(symbol, expiration)
    output = format_options(data)
    print(output)
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="CLI for yfinance MCP screens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-tools
  %(prog)s markets
  %(prog)s sector technology
  %(prog)s ticker TSLA                # Single ticker (detailed)
  %(prog)s ticker TSLA F GM           # Batch comparison (table)
  %(prog)s options PALL               # Options analysis (nearest expiration)
  %(prog)s options PALL 2025-12-20    # Options for specific expiration
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list-tools command
    subparsers.add_parser("list-tools", help="Show MCP tool definitions")

    # markets command
    subparsers.add_parser("markets", help="Market overview screen")

    # sector command
    sector_parser = subparsers.add_parser("sector", help="Sector drill-down screen")
    sector_parser.add_argument("name", help="Sector name (e.g., technology)")

    # ticker command
    ticker_parser = subparsers.add_parser(
        "ticker", help="Individual ticker screen or batch comparison"
    )
    ticker_parser.add_argument(
        "symbols", nargs="+", help="Ticker symbol(s) (e.g., TSLA or TSLA F GM)"
    )

    # options command
    options_parser = subparsers.add_parser("options", help="Options chain analysis")
    options_parser.add_argument("symbol", help="Ticker symbol (e.g., PALL)")
    options_parser.add_argument(
        "expiration",
        nargs="?",
        default="nearest",
        help="Expiration date (default: nearest, or YYYY-MM-DD)",
    )

    return parser.parse_args()


async def async_main() -> int:  # noqa: PLR0911
    args = parse_args()

    if not args.command:
        print("Error: No command specified")
        print(
            "Usage: ./cli list-tools | markets | sector <name> | "
            "ticker <symbol> | options <symbol> [expiration]"
        )
        return 1

    if args.command == "list-tools":
        return await list_tools_command()

    if args.command == "markets":
        return markets_command()

    if args.command == "sector":
        return sector_command(args.name)

    if args.command == "ticker":
        return ticker_command(args.symbols)

    if args.command == "options":
        return options_command(args.symbol, args.expiration)

    print(f"Unknown command: {args.command}")
    return 1


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())
