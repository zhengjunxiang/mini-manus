"""Lesson 02: Tool Use - Agent 核心逻辑"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from env import find_and_load_env
from openai_compat import chat_completions, load_config_from_env
from log import init_logger, format_json

# 导入工具
from tools import TOOL_REGISTRY


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """执行工具调用"""
    tool = TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    raise RuntimeError(f"Unknown tool: {name}")


@dataclass
class MiniManus:
    """支持 Tool Use 的 Agent"""

    max_steps: int = 8
    log_dir: Path | None = None

    def _system_prompt(self) -> str:
        return (
            "You are a helpful AI Agent.\n"
            "You have access to several tools:\n"
            "- `search(query: string)` - Search the web for current information\n"
            "- `datetime()` - Get the current date and time\n"
            "- `calculator(expression: string)` - Evaluate a mathematical expression. Use '**' for power, e.g., '2**10' for 2 to the power of 10.\n"
            "- `terminate(final: string)` - End the agent loop and return the final answer\n\n"
            "Rules:\n"
            "1) Use tools to gather information when needed.\n"
            "2) IMPORTANT: After you call a tool, the result will be shown to you. Use that result to form your final answer.\n"
            "3) Once you have the result from a tool, call `terminate` immediately with the final answer. Do NOT call the same tool again.\n"
            "4) Be concise.\n"
        )

    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        # 本课新增：4 个工具
        tools = [tool.schema() for tool in TOOL_REGISTRY.values()]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task},
        ]

        logger.info("=" * 60)
        logger.info("Step 0: 初始上下文 (messages)")
        logger.info("=" * 60)
        logger.info(format_json(messages))
        logger.info("\nStep 0: 可用工具 (tools)")
        logger.info(format_json(tools))

        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM 原始回复")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if tool_calls:
                # 处理多个工具调用（去重，防止 Moonshot API 返回重复）
                seen_tools = set()
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""

                    # 去重：跳过同名的重复工具调用
                    if name in seen_tools:
                        continue
                    seen_tools.add(name)

                    raw_args = fn.get("arguments") or "{}"

                    # 确保有 tool_call_id
                    tool_call_id = call.get("id") or f"toolcall_{step}_{idx}"

                    try:
                        args = (
                            json.loads(raw_args)
                            if isinstance(raw_args, str)
                            else dict(raw_args)
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Invalid tool arguments for {name}: {raw_args}"
                        ) from e

                    logger.info(f"Step {step}: 调用工具 {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: 工具返回")
                    logger.info(output)

                    # Moonshot API workaround: 用 user message 代替 tool message
                    # 因为 Moonshot API 不完全支持 tool role
                    tool_result_msg = (
                        f"[TOOL_CALL {name}] {json.dumps(args)}\n[TOOL_RESULT] {output}"
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": tool_result_msg,
                        }
                    )

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* 最终答案 (Agent Loop 终止)")
                        logger.info("*" * 60)
                        logger.info(output)
                        return

                logger.info(f"Step {step}: 更新后的 messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM 直接返回内容 (未调用工具)")
                logger.info("*" * 60)
                logger.info(content)
                # 没有调用 terminate，直接返回内容
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )
