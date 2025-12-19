#!/usr/bin/env python3
"""
yfinance MCP Server - stdio transport

MCP protocol wrapper for Claude Code (stdio mode).
Business logic delegated to handlers.py.

Run with: poetry run python -m mcp_yfinance_ux.server
"""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .handlers import call_tool as handle_tool
from .tools import get_mcp_tools

app = Server("yfinance-mcp")


@app.list_tools()  # type: ignore[misc,no-untyped-call]
async def list_tools() -> list[Tool]:
    """List available MCP tools - imported from tools.py (single source of truth)"""
    return get_mcp_tools()


@app.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: Any) -> list[TextContent]:  # noqa: ANN401
    """Handle tool execution - delegates to handlers.py"""
    result = handle_tool(name, arguments or {})
    return [TextContent(type="text", text=result)]


async def main() -> None:
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
