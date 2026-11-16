"""
Streamable HTTP transport for the Instagram MCP server.

Serves MCP statelessly at ``/<MCP_SECRET>/mcp`` as a plain ASGI app, suitable for
serverless platforms such as Vercel. Run locally with:

    uvicorn src.http_app:app --port 8000
"""

import hmac
import os
from functools import lru_cache

import structlog
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Scope, Send

from .instagram_client import InstagramClient
from .instagram_mcp_server import InstagramMCPServer, request_instagram_client

logger = structlog.get_logger(__name__)

MCP_PATH = "/mcp"


@lru_cache(maxsize=1)
def _get_mcp_server() -> Server:
    return InstagramMCPServer().server


def _is_authorized(path: str) -> bool:
    secret = os.environ.get("MCP_SECRET", "")
    if not secret:
        logger.error("MCP_SECRET is not set; rejecting all requests")
        return False
    expected = f"/{secret}{MCP_PATH}"
    return hmac.compare_digest(path.rstrip("/").encode(), expected.encode())


async def _handle_lifespan(receive: Receive, send: Send) -> None:
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    """ASGI entry point."""
    if scope["type"] == "lifespan":
        await _handle_lifespan(receive, send)
        return
    if scope["type"] != "http":
        return

    if not _is_authorized(scope["path"]):
        await PlainTextResponse("Not Found", status_code=404)(scope, receive, send)
        return

    # Hide the secret from everything downstream of this check.
    scope = {**scope, "path": MCP_PATH, "raw_path": MCP_PATH.encode()}

    # A session manager can only be run once, so each request gets its own; this
    # also avoids relying on ASGI lifespan events, which serverless runtimes may skip.
    session_manager = StreamableHTTPSessionManager(
        app=_get_mcp_server(), stateless=True, json_response=True
    )
    client = InstagramClient()
    token = request_instagram_client.set(client)
    try:
        async with session_manager.run():
            await session_manager.handle_request(scope, receive, send)
    finally:
        request_instagram_client.reset(token)
        await client.close()
