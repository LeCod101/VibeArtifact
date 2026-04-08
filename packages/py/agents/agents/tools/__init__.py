"""工具注册表。

汇总所有工具模块，提供统一的工具发现和获取接口。
"""

from __future__ import annotations

import inspect
import types as stdlib_types
from typing import Any

from agents.tools.base import ToolDefinition


class ToolRegistry:
    """工具注册表，单例模式。

    负责注册、发现和检索所有可用工具，
    并生成 OpenAI function calling 格式的工具列表。
    """

    _instance: ToolRegistry | None = None

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_tools"):
            self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        """注册一个工具定义。"""
        self._tools[tool_def.name] = tool_def

    def get_all_tools(self) -> list[ToolDefinition]:
        """获取所有已注册的工具定义。"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolDefinition | None:
        """按名称获取工具定义，不存在时返回 None。"""
        return self._tools.get(name)

    def get_openai_tools_schema(self) -> list[dict[str, Any]]:
        """生成 OpenAI function calling 格式的工具列表。

        格式符合 ``tools`` 参数规范：
        ``[{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]``
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": td.name,
                    "description": td.description,
                    "parameters": td.parameters,
                },
            }
            for td in self._tools.values()
        ]


def _discover_tools_from_module(module: stdlib_types.ModuleType) -> list[ToolDefinition]:
    """从模块中发现所有带 _tool_definition 属性的函数。"""
    tools: list[ToolDefinition] = []
    for _name, obj in inspect.getmembers(module, callable):
        tool_def = getattr(obj, "_tool_definition", None)
        if isinstance(tool_def, ToolDefinition):
            tools.append(tool_def)
    return tools


def _auto_register() -> None:
    """导入所有工具模块并自动注册发现的工具。"""
    from agents.tools import code_tools, doc_tools, project_tools, util_tools

    registry = ToolRegistry()
    for module in (code_tools, doc_tools, project_tools, util_tools):
        for tool_def in _discover_tools_from_module(module):
            registry.register(tool_def)


_auto_register()
