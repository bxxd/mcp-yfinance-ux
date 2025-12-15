#!/usr/bin/env python3
"""
yfinance MCP Server - HTTP/SSE transport

Network server for multi-tenant Claude Code access.
Same MCP protocol as stdio server, different transport.
Business logic delegated to handlers.py.

Run with: make server

Configuration:
- PORT: Server port (default: 5001)
"""

import logging
import os
import signal
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .handlers import call_tool as handle_tool
from .tools import get_mcp_tools

# Configure logging with millisecond precision
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S:%f"
)


# Custom formatter to get milliseconds in the right format
class MillisecondFormatter(logging.Formatter):
    """Custom formatter with milliseconds as :XXXX format"""
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        """Override formatTime to include milliseconds with : separator"""
        ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            # Format without milliseconds first
            s = ct.strftime("%Y/%m/%d %H:%M:%S")
            # Add milliseconds with : separator
            ms = int((record.created % 1) * 10000)  # Get 4 digits of precision
            return f"{s}:{ms:04d}"
        return super().formatTime(record, datefmt)


# Apply custom formatter to root logger
for handler in logging.root.handlers:
    handler.setFormatter(MillisecondFormatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S"
    ))

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_PORT = 5001


def get_port() -> int:
    """Get server port from environment or use default"""
    port_str = os.environ.get("PORT", str(DEFAULT_PORT))
    try:
        return int(port_str)
    except ValueError:
        msg = f"Invalid PORT value: {port_str}"
        raise ValueError(msg) from None


# MCP Server instance (reuses same logic as stdio server)
mcp_server = Server("yfinance-mcp")

# SSE transport for multi-client support
sse_transport = SseServerTransport("/messages")


@mcp_server.list_tools()  # type: ignore[misc,no-untyped-call]
async def list_tools() -> list[Tool]:
    """List available MCP tools - imported from tools.py (single source of truth)"""
    return get_mcp_tools()


@mcp_server.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: Any) -> list[TextContent]:  # noqa: ANN401
    """Handle tool execution - delegates to handlers.py"""
    logger.info(f"call_tool: name={name}, arguments={arguments}")
    result = handle_tool(name, arguments or {})
    logger.info(f"{name}() returning {len(result)} chars")
    return [TextContent(type="text", text=result)]


# Starlette endpoint handlers

async def handle_ping(_request: Request) -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse({"status": "ok"})


async def handle_shutdown(_request: Request) -> JSONResponse:
    """Graceful shutdown endpoint"""
    # Send SIGTERM to self for graceful shutdown
    os.kill(os.getpid(), signal.SIGTERM)
    return JSONResponse({"status": "shutting down"})


async def handle_sse(request: Request) -> Response:
    """
    SSE endpoint for MCP protocol.

    Creates a new SSE connection for each client, runs the MCP server
    with the connection streams, and returns when client disconnects.
    """
    client_addr = request.client.host if request.client else "unknown"
    logger.info(f"New SSE connection from {client_addr}")

    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        logger.info("SSE connected, running MCP server loop")
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )
        logger.info(f"SSE disconnected from {client_addr}")

    # Return empty response to avoid NoneType error (per MCP docs)
    # Add cache headers: 10 seconds for market data (5-10s range)
    return Response(
        headers={
            "Cache-Control": "public, max-age=10, must-revalidate",
            "X-Content-Type-Options": "nosniff",
        }
    )


# Starlette application
app = Starlette(
    routes=[
        Route("/ping", endpoint=handle_ping, methods=["GET"]),
        Route("/shutdown", endpoint=handle_shutdown, methods=["POST"]),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=sse_transport.handle_post_message),
    ]
)
