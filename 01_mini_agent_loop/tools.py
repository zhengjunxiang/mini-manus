from __future__ import annotations

from typing import Any


def terminate_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "terminate",
            "description": "End the agent loop and return the final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "final": {
                        "type": "string",
                        "description": "The final answer to show the user before exiting.",
                    }
                },
                "required": ["final"],
                "additionalProperties": False,
            },
        },
    }


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """Execute a tool call.

    Returns (should_stop, output_text).
    """
    if name == "terminate":
        final = str(arguments.get("final", "")).strip()
        return True, final
    raise RuntimeError(f"Unknown tool: {name}")

