import traceback
import sys
import os
import uvicorn

from dotenv import load_dotenv
from pydantic import Field

from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context
import mcp.types as types

from src.duckduckgo.searcher import DuckDuckGoSearcher
from src.duckduckgo.fetcher import WebContentFetcher

from starlette.applications import Starlette
from starlette.routing import Mount

load_dotenv(override=True)

MAX_RESULTS = int(os.getenv('MAX_RESULTS', '5'))
PORT = int(os.getenv('PORT', '8080'))

# Initialize FastMCP server
mcp = FastMCP(
    name='duck-duck-go-mcp-server',
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
)

searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()

@mcp.custom_route("/actuator/health", methods=["GET"])
async def health():
    return {"status":"ok"}

app = Starlette(
    routes = [
        Mount(
            path="/",
            app=mcp.streamable_http_app()
        )
    ]
)

@mcp.tool()
async def search(
    query: str = Field(..., description="The search query string"), 
    ctx: Context = Field(..., description="MCP context for logging"), 
) -> str:
    """
    Search DuckDuckGo and return formatted results.
    """
    try:
        results = await searcher.search(query, ctx, max_results=MAX_RESULTS)
        result = searcher.format_results_for_llm(results)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise

    return types.TextContent(
        type="text",
        text=result
    )


@mcp.tool()
async def fetch_content(
    url: str = Field(..., description='The webpage URL to fetch content from'),
    ctx: Context = Field(..., description='MCP context for logging')
) -> str:
    """Fetch and parse content from a webpage URL.
    """
    try:
        result = await fetcher.fetch_and_parse(url, ctx)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise

    return types.TextContent(
        type="text",
        text=result
    )


uvicorn.run(mcp, host="0.0.0.0", port=PORT)