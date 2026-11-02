"""Lista o llama tools del servidor MCP que dice el .env (MCP_URL, MCP_AUTH_PROVIDER): el mock local o el compartido.

Uso:
  uv run python dev/mcp/mcp_tools.py                                              lista las tools que ve tu token
  uv run python dev/mcp/mcp_tools.py get_transactions customer_id=CUS-1001 limit=2   llama una tool
"""

import asyncio
import json
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError

from agent.infrastructure.config.settings import Settings
from agent.infrastructure.mcp.auth import mcp_bearer


def argument(value: str):
    """customer_id=CUS-1001 → texto; limit=2 → número; los valores JSON se leen como JSON."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def main(args: list[str]) -> int:
    mcp = Settings().mcp
    async with Client(mcp.url, auth=mcp_bearer(mcp)) as client:
        if not args:
            tools = await client.list_tools()
            print(f"{mcp.url} · {mcp.auth_provider} · {len(tools)} tools")
            for tool in sorted(tools, key=lambda tool: tool.name):
                kind = "consulta" if tool.annotations and tool.annotations.read_only_hint else "acción sensible"
                print(f"  {tool.name:<30} {kind:<16} {', '.join(tool.input_schema.get('properties', {}))}")
            return 0
        name, pairs = args[0], dict(pair.split("=", 1) for pair in args[1:])
        try:
            result = await client.call_tool(name, {key: argument(value) for key, value in pairs.items()})
        except ToolError as error:
            print(f"  Error de la tool: {error}")
            return 1
        print(json.dumps(result.structured_content, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(main(sys.argv[1:])))
