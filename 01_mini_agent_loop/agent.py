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
from tools import execute_tool, terminate_schema
from log import init_logger, format_json


@dataclass
class MiniManus:
    max_steps: int = 8
    log_dir: Path | None = None

    def _system_prompt(self) -> str:
        return (
            "You are a minimal agent. You have exactly one tool: `terminate(final: string)`.\n"
            "Rules:\n"
            "1) You MUST call `terminate` to return the final answer. Do NOT put the final answer in normal content.\n"
            "2) Keep the final answer concise and directly useful.\n"
        )

    def run(self, *, task: str) -> None:
        if self.log_dir:
            init_logger(self.log_dir)

        find_and_load_env()
        cfg = load_config_from_env()

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": task},
        ]
        tools = [terminate_schema()]

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
                call = tool_calls[0]
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

                logger.info(f"Step {step}: 调用工具 {name}")
                logger.info(format_json({"arguments": args}))

                should_stop, output = execute_tool(name, args)

                logger.info(f"Step {step}: 工具返回")
                logger.info(output)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id") or "toolcall_0",
                        "content": output,
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
                return

        raise RuntimeError(
            f"Agent exceeded max_steps={self.max_steps} without termination."
        )
