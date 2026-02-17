"""日志模块 - 统一的日志配置"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from loguru import logger


def init_logger(log_dir: Path | str | None = None, level: str = "INFO") -> None:
    """初始化日志器

    Args:
        log_dir: 日志文件目录，如果为 None 则只输出到控制台
        level: 日志级别，默认为 INFO
    """
    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
    )

    # 文件输出
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件名使用时间戳，避免覆盖
        from datetime import datetime

        log_file = log_dir / f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logger.add(
            log_file,
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            encoding="utf-8",
        )


def format_json(data: Any) -> str:
    """格式化 JSON 数据用于日志输出"""
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)
