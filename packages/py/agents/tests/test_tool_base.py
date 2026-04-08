"""测试 @tool 装饰器和类型映射。"""

from __future__ import annotations

from typing import Optional

from agents.tools.base import ToolDefinition, tool


class TestToolDecorator:
    """验证 @tool 装饰器正确提取函数元数据。"""

    def test_extracts_function_name(self) -> None:
        """函数名应作为工具名称。"""

        @tool
        async def my_tool(x: str) -> dict:
            """工具描述。"""
            return {}

        td: ToolDefinition = my_tool._tool_definition  # type: ignore[attr-defined]
        assert td.name == "my_tool"

    def test_extracts_docstring_first_line(self) -> None:
        """docstring 首行应作为工具描述。"""

        @tool
        async def sample(x: str) -> dict:
            """这是首行描述。

            这是详细说明，不应出现在 description 中。
            """
            return {}

        assert sample._tool_definition.description == "这是首行描述。"  # type: ignore[attr-defined]

    def test_maps_str_to_string(self) -> None:
        """str 类型应映射为 JSON Schema string。"""

        @tool
        async def f(name: str) -> dict:
            """工具。"""
            return {}

        props = f._tool_definition.parameters["properties"]  # type: ignore[attr-defined]
        assert props["name"]["type"] == "string"

    def test_maps_int_to_integer(self) -> None:
        """int 类型应映射为 JSON Schema integer。"""

        @tool
        async def f(count: int) -> dict:
            """工具。"""
            return {}

        props = f._tool_definition.parameters["properties"]  # type: ignore[attr-defined]
        assert props["count"]["type"] == "integer"

    def test_maps_list_str_to_array(self) -> None:
        """list[str] 应映射为 array + items string。"""

        @tool
        async def f(tags: list[str]) -> dict:
            """工具。"""
            return {}

        props = f._tool_definition.parameters["properties"]  # type: ignore[attr-defined]
        assert props["tags"]["type"] == "array"
        assert props["tags"]["items"]["type"] == "string"

    def test_optional_not_required(self) -> None:
        """Optional 参数不应出现在 required 列表中。"""

        @tool
        async def f(name: str, note: Optional[str] = None) -> dict:
            """工具。"""
            return {}

        td = f._tool_definition  # type: ignore[attr-defined]
        assert "name" in td.parameters["required"]
        assert "note" not in td.parameters["required"]

    def test_handler_reference(self) -> None:
        """handler 应引用被装饰的原始函数。"""

        @tool
        async def my_func(x: str) -> dict:
            """工具。"""
            return {"ok": True}

        assert my_func._tool_definition.handler is my_func  # type: ignore[attr-defined]

    def test_default_param_not_required(self) -> None:
        """带默认值的参数不应出现在 required 列表中。"""

        @tool
        async def f(lang: str, dialect: str = "postgresql") -> dict:
            """工具。"""
            return {}

        td = f._tool_definition  # type: ignore[attr-defined]
        assert "lang" in td.parameters["required"]
        assert "dialect" not in td.parameters["required"]

    def test_param_description_from_docstring(self) -> None:
        """参数描述应从 Google 风格 docstring 提取。"""

        @tool
        async def f(query: str) -> dict:
            """搜索工具。

            Args:
                query: 搜索关键词
            """
            return {}

        props = f._tool_definition.parameters["properties"]  # type: ignore[attr-defined]
        assert props["query"]["description"] == "搜索关键词"
