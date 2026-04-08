"""工具调用执行器。

统一执行 LLM 返回的工具调用，包含工具查找、参数校验、
异步执行、错误处理和结果格式化。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.tools import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果。

    Attributes:
        success: 执行是否成功
        data: 成功时的返回数据
        error: 失败时的错误信息
    """

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class ToolExecutor:
    """工具执行器，负责查找工具、校验参数、执行并捕获异常。"""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """执行指定工具。

        查找注册表中的工具定义，调用其 handler，
        捕获所有异常并以 ToolResult 形式返回，不向上抛出。

        Args:
            tool_name: 要调用的工具名
            arguments: 传递给工具的参数字典

        Returns:
            包含成功/失败信息的 ToolResult
        """
        tool_def = self._registry.get_tool(tool_name)
        if tool_def is None:
            return ToolResult(success=False, error=f"未找到工具: {tool_name}")

        try:
            result = await tool_def.handler(**arguments)
            return ToolResult(success=True, data=result)
        except TypeError as exc:
            logger.warning("工具 %s 参数校验失败: %s", tool_name, exc)
            return ToolResult(success=False, error=f"参数错误: {exc}")
        except Exception as exc:
            logger.exception("工具 %s 执行异常", tool_name)
            return ToolResult(success=False, error=f"执行失败: {exc}")
