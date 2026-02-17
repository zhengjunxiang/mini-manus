"""MCP Client - Auto-discover and load tools from MCP servers"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from .base import BaseTool


def load_mcp_servers(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "mcp_servers.json"

    config_path = Path(config_path)
    if not config_path.exists():
        return []

    with open(config_path) as f:
        data = json.load(f)
    return data.get("mcp_servers", [])


class MCPServer:
    def __init__(self, name: str, url: str, description: str = "", env_key: str = ""):
        self.name = name
        self.url = url
        self.description = description
        self.env_key = env_key
        self._tools: list[dict[str, Any]] | None = None

    def _get_api_key(self) -> str:
        if self.env_key:
            return os.getenv(self.env_key, "")
        return ""

    def list_tools(self) -> list[dict[str, Any]]:
        if self._tools is not None:
            return self._tools

        api_key = self._get_api_key()
        if not api_key:
            return []

        headers = {
            self.env_key: api_key,
            "Accept": "application/json, text/event-stream",
        }

        try:
            with httpx.Client(headers=headers, timeout=30.0) as client:
                resp = client.post(
                    self.url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {},
                    },
                )
                result = resp.json()

                if "result" in result and "tools" in result["result"]:
                    self._tools = result["result"]["tools"]
                    return self._tools
        except Exception:
            pass

        return []

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        api_key = self._get_api_key()
        if not api_key:
            return {"error": "No API key configured"}

        headers = {
            self.env_key: api_key,
            "Accept": "application/json, text/event-stream",
        }

        with httpx.Client(headers=headers, timeout=30.0) as client:
            resp = client.post(
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                },
            )
            return resp.json()


class MCPTool(BaseTool):
    def __init__(self, server: MCPServer, tool_schema: dict[str, Any]):
        self.server = server
        self._schema = tool_schema

    @property
    def name(self) -> str:
        return self._schema.get("name", "")

    @property
    def description(self) -> str:
        return self._schema.get("description", "")

    def _parameters_schema(self) -> dict[str, Any]:
        input_schema = self._schema.get("inputSchema", {})
        return {
            "type": "object",
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", []),
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        try:
            result = self.server.call_tool(self.name, kwargs)

            if "result" in result:
                content = result["result"].get("content", [])
                if content and content[0].get("type") == "text":
                    return False, content[0].get("text", "")

            if "error" in result:
                return False, f"MCP error: {result['error']}"

            return False, str(result)
        except Exception as e:
            return False, f"Error: {str(e)}"


def load_mcp_tools() -> dict[str, BaseTool]:
    from env import find_and_load_env

    find_and_load_env()

    servers = load_mcp_servers()
    tools: dict[str, BaseTool] = {}

    for server_config in servers:
        server = MCPServer(
            name=server_config["name"],
            url=server_config["url"],
            description=server_config.get("description", ""),
            env_key=server_config.get("env_key", ""),
        )

        tool_schemas = server.list_tools()
        for schema in tool_schemas:
            tool = MCPTool(server, schema)
            tools[tool.name] = tool

    return tools
