"""Lesson 04: Skills - Agent 核心逻辑"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from env import find_and_load_env
from openai_compat import chat_completions, load_config_from_env
from log import init_logger, format_json

from tools import TOOL_REGISTRY


def execute_tool(name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    tool = TOOL_REGISTRY.get(name)
    if tool:
        return tool.execute(**arguments)
    raise RuntimeError(f"Unknown tool: {name}")


@dataclass
class MiniManus:
    max_steps: int = 10
    log_dir: Path | None = None
    skill_context: str = ""

    def _system_prompt(self) -> str:
        tool_descriptions = []
        for name, tool in TOOL_REGISTRY.items():
            tool_descriptions.append(f"- `{tool.name}` - {tool.description}")

        tools_list = "\n".join(tool_descriptions)

        skill_instruction = ""
        if self.skill_context:
            skill_instruction = f"\n\n# Active Skill Context\n{self.skill_context}\n"

        return (
            "You are MiniManus, an AI Agent with access to Skills and MCP tools.\n"
            "Skills let you install and load domain-specific expertise.\n\n"
            f"You have access to these tools:\n{tools_list}\n\n"
            "Skills Management:\n"
            "- Use `skill` tool to install, list, load, or create skills\n"
            "- Skills can include instructions, helpers, and even call MCP tools internally\n\n"
            f"{skill_instruction}"
            "Rules:\n"
            "1) Use appropriate tools to accomplish the task.\n"
            "2) Use skills to extend your capabilities when needed.\n"
            "3) When you have the final answer, call `terminate`.\n"
        )

    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        tools = [tool.schema() for tool in TOOL_REGISTRY.values()]

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task},
        ]

        logger.info("=" * 60)
        logger.info("Step 0: 初始上下文")
        logger.info("=" * 60)
        logger.info(format_json(messages))
        logger.info(f"\nAvailable tools: {len(tools)}")
        logger.info(f"Tools: {[t['function']['name'] for t in tools]}")

        for step in range(1, self.max_steps + 1):
            logger.info("#" * 60)
            logger.info(f"# Step {step}")
            logger.info("#" * 60)

            resp = chat_completions(
                cfg=cfg, messages=messages, tools=tools, tool_choice="auto"
            )

            logger.info(f"Step {step}: LLM response")
            logger.info(format_json(resp))

            msg = (resp.get("choices") or [{}])[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            # 检查是否有 skill load 带来的新上下文
            for msg_in_history in messages:
                if isinstance(msg_in_history.get("content"), str):
                    if "[SKILL_CONTEXT]" in msg_in_history["content"]:
                        # 更新 skill context
                        for t_call in tool_calls:
                            fn = t_call.get("function") or {}
                            if fn.get("name") == "skill":
                                skill_instruction = fn.get("arguments", "{}")
                                if "load" in skill_instruction:
                                    logger.info("Skill loaded, updating context...")
                                    messages[0]["content"] = self._system_prompt()

            if tool_calls:
                for idx, call in enumerate(tool_calls):
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""

                    raw_args = fn.get("arguments") or "{}"

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

                    logger.info(f"Step {step}: Calling tool {name}")
                    logger.info(format_json({"arguments": args}))

                    should_stop, output = execute_tool(name, args)

                    logger.info(f"Step {step}: Tool returned")
                    logger.info(output[:500] + "..." if len(output) > 500 else output)

                    # 检查是否是 skill load
                    if name == "skill" and args.get("action") == "load":
                        # 将 skill 内容作为系统提示的一部分
                        self.skill_context = (
                            f"## Skill: {args.get('skill_name')}\n{output}"
                        )
                        messages[0]["content"] = self._system_prompt()
                        tool_result_msg = f"[SKILL_LOADED]\n{output}"
                    else:
                        tool_result_msg = f"[TOOL_CALL {name}] {json.dumps(args)}\n[TOOL_RESULT] {output}"

                    messages.append({"role": "user", "content": tool_result_msg})

                    if should_stop:
                        logger.info("*" * 60)
                        logger.info("* Final Answer (Agent Loop Terminated)")
                        logger.info("*" * 60)
                        logger.info(output)
                        return

                logger.info(f"Step {step}: Updated messages")
                logger.info(format_json(messages))
                continue

            if content:
                logger.info("*" * 60)
                logger.info("* LLM returned content directly (no tool call)")
                logger.info("*" * 60)
                logger.info(content)
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )
