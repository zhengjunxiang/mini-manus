"""Terminate 工具 - 终止 Agent Loop"""

from __future__ import annotations

from typing import Any

from .base import BaseTool


class TerminateTool(BaseTool):
    """终止工具"""

    @property
    def name(self) -> str:
        return "terminate"

    @property
    def description(self) -> str:
        return "Use this tool when you have completed the task and want to return the final answer. Pass your final answer as the 'final' parameter."

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "final": {
                    "type": "string",
                    "description": "The final answer to return to the user.",
                },
            },
            "required": ["final"],
        }

    def execute(self, **kwargs) -> tuple[bool, str]:
        final = kwargs.get("final", "")
        return True, final
