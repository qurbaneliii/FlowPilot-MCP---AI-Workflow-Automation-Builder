from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def mcp_endpoint(request: Request) -> JSONResponse:
    payload = await request.json()
    method = payload.get("method")
    request_id = payload.get("id", 1)
    if method == "initialize":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"protocolVersion": "2025-03-26", "serverInfo": {}},
            }
        )
    if method == "tools/list":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "dummy_tool",
                            "description": "A fake MCP tool for integration tests.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"value": {"type": "string"}},
                            },
                        }
                    ]
                },
            }
        )
    if method == "tools/call":
        params = payload.get("params", {})
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tool": params.get("name"),
                    "arguments": params.get("arguments", {}),
                },
            }
        )
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "Method not found"},
        }
    )


def create_fake_mcp_app() -> Starlette:
    return Starlette(routes=[Route("/mcp", mcp_endpoint, methods=["POST"])])
