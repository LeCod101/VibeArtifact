"""测试工具执行器。"""

from __future__ import annotations

import pytest
from agents.tool_executor import ToolExecutor
from agents.tools.base import ToolDefinition


class TestToolExecutor:
    """验证 ToolExecutor 的执行、错误处理和异常捕获。"""

    @pytest.fixture(autouse=True)
    def _setup(self, fresh_registry) -> None:
        self.registry = fresh_registry
        self.executor = ToolExecutor(fresh_registry)

    async def test_execute_success(self) -> None:
        """正常执行应返回 success=True 和工具返回值。"""

        async def handler(name: str) -> dict:
            return {"greeting": f"hello {name}"}

        td = ToolDefinition(
            name="greet",
            description="打招呼",
            parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            handler=handler,
        )
        self.registry.register(td)

        result = await self.executor.execute("greet", {"name": "test"})
        assert result.success is True
        assert result.data == {"greeting": "hello test"}

    async def test_unknown_tool(self) -> None:
        """调用未注册的工具应返回 success=False。"""
        result = await self.executor.execute("no_such_tool", {})
        assert result.success is False
        assert "未找到工具" in (result.error or "")

    async def test_argument_error(self) -> None:
        """参数类型/缺失导致 TypeError 应返回参数错误。"""

        async def handler(count: int) -> dict:
            return {"count": count}

        td = ToolDefinition(
            name="counter",
            description="计数",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=handler,
        )
        self.registry.register(td)

        result = await self.executor.execute("counter", {"wrong": "arg"})
        assert result.success is False
        assert "参数错误" in (result.error or "")

    async def test_exception_captured(self) -> None:
        """handler 内部异常应被捕获，返回执行失败。"""

        async def handler() -> dict:
            raise RuntimeError("boom")

        td = ToolDefinition(
            name="fail_tool",
            description="故意失败",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=handler,
        )
        self.registry.register(td)

        result = await self.executor.execute("fail_tool", {})
        assert result.success is False
        assert "执行失败" in (result.error or "")
        assert "boom" in (result.error or "")
