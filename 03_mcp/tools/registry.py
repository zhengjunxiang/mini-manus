"""MCP 工具注册表 - 自动从 MCP 服务器加载工具"""

from .search import SearchTool
from .terminate import TerminateTool
from .mcp_client import load_mcp_tools

_search = SearchTool()
_terminate = TerminateTool()

mcp_tools = load_mcp_tools()

MCP_TOOL_REGISTRY = {
    "search": _search,
    "terminate": _terminate,
    **mcp_tools,
}
