from typing import Any

from mcp import Client

from use_cases.enterprise_analytics.mcp_server.server import mcp


class MCPGatewayError(RuntimeError):
    pass


class LocalMCPGateway:
    async def call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        async with Client(mcp, raise_exceptions=False) as client:
            result = await client.call_tool(tool_name, arguments)

        if result.is_error:
            message = "MCP tool call failed"
            if result.content and hasattr(result.content[0], "text"):
                message = result.content[0].text
            raise MCPGatewayError(message)

        if not isinstance(result.structured_content, dict):
            raise MCPGatewayError(
                f"Tool {tool_name} returned no structured content"
            )
        return result.structured_content