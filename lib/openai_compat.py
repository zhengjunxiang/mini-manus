from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from loguru import logger
from openai import OpenAI


@dataclass(frozen=True)
class OpenAICompatConfig:
    api_key: str
    base_url: str
    model: str
    timeout_s: float = 60.0


def chat_completions(
    *,
    cfg: OpenAICompatConfig,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] = "auto",
    temperature: float = 1.0,
) -> dict[str, Any]:
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=cfg.timeout_s)

    kwargs: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools is not None:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    try:
        resp = client.chat.completions.create(**kwargs)
        return resp.model_dump(mode="json")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


def load_config_from_env() -> OpenAICompatConfig:
    api_key = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE") or ""
    model = os.environ.get("OPENAI_MODEL") or ""
    timeout_s = float(os.environ.get("OPENAI_TIMEOUT_S") or "60")

    missing = [
        k
        for k, v in [
            ("OPENAI_KEY", api_key),
            ("OPENAI_BASE_URL", base_url),
            ("OPENAI_MODEL", model),
        ]
        if not v
    ]
    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)} (check exercise/.env)"
        )

    return OpenAICompatConfig(
        api_key=api_key, base_url=base_url, model=model, timeout_s=timeout_s
    )
