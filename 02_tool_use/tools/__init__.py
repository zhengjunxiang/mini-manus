"""工具模块 - 统一的工具基类和具体实现"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，用于生成 schema"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> tuple[bool, str]:
        """执行工具

        Returns:
            (should_stop, output): should_stop 表示是否终止 Agent Loop
        """
        pass

    def schema(self) -> dict[str, Any]:
        """生成工具的 JSON Schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._parameters_schema(),
            },
        }

    def _parameters_schema(self) -> dict[str, Any]:
        """子类可重写此方法定义参数 schema"""
        return {
            "type": "object",
            "properties": {},
        }


# 导出所有工具
from .terminate import TerminateTool
from .datetime import DateTimeTool
from .calculator import CalculatorTool
from .search import SearchTool
from .registry import TOOL_REGISTRY

__all__ = [
    "BaseTool",
    "TerminateTool",
    "DateTimeTool",
    "CalculatorTool",
    "SearchTool",
    "TOOL_REGISTRY",
]
