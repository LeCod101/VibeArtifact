"""测试 ToolRegistry 注册表。"""

from __future__ import annotations

from agents.tools.base import ToolDefinition


class TestToolRegistry:
    """验证 ToolRegistry 的注册、检索和 schema 生成。"""

    def test_register_and_get(self, fresh_registry) -> None:
        """注册后应能按名称获取工具。"""
        td = ToolDefinition(
            name="test_tool",
            description="测试工具",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=lambda: None,
        )
        fresh_registry.register(td)
        assert fresh_registry.get_tool("test_tool") is td

    def test_get_nonexistent_returns_none(self, fresh_registry) -> None:
        """获取不存在的工具应返回 None。"""
        assert fresh_registry.get_tool("no_such_tool") is None

    def test_get_all_tools(self, fresh_registry) -> None:
        """get_all_tools 应返回所有已注册工具。"""
        for i in range(3):
            td = ToolDefinition(
                name=f"tool_{i}",
                description=f"工具 {i}",
                parameters={"type": "object", "properties": {}, "required": []},
                handler=lambda: None,
            )
            fresh_registry.register(td)
        assert len(fresh_registry.get_all_tools()) == 3

    def test_openai_schema_format(self, fresh_registry) -> None:
        """OpenAI schema 应包含 type=function 和 function 子结构。"""
        td = ToolDefinition(
            name="greet",
            description="打招呼",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=lambda: None,
        )
        fresh_registry.register(td)

        schema_list = fresh_registry.get_openai_tools_schema()
        assert len(schema_list) == 1

        entry = schema_list[0]
        assert entry["type"] == "function"
        assert entry["function"]["name"] == "greet"
        assert entry["function"]["description"] == "打招呼"
        assert entry["function"]["parameters"]["properties"]["name"]["type"] == "string"

    def test_auto_discover_13_tools(self) -> None:
        """自动发现应注册 4 个模块共 13 个工具。"""
        from agents.tools import ToolRegistry

        # 获取单例（_auto_register 在模块导入时已执行）
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        assert len(tools) == 13

        names = {t.name for t in tools}
        expected = {
            "generate_code", "edit_code", "explain_code", "review_code",
            "generate_document", "generate_diagram", "generate_sql",
            "list_files", "read_file", "search_code", "export_project",
            "web_search", "ask_clarification",
        }
        assert names == expected
