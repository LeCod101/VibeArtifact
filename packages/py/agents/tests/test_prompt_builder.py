"""
PromptBuilder 测试模块。

测试 PromptBuilder 的 6 层拼装逻辑：
- 空 builder 行为
- 单层设置
- 全层设置
- build_messages 格式
- get_role_prompt 工厂函数
"""

import pytest
from agents.prompts.builder import (
    PromptBuilder,
)
from agents.prompts.templates.role_prompts import get_role_prompt


class TestPromptBuilderEmpty:
    """空 PromptBuilder 的行为测试。"""

    def test_empty_builder_returns_empty_string(self):
        """空 builder 的 build_system_prompt() 返回空字符串（所有层均未设置）。"""
        builder = PromptBuilder()
        result = builder.build_system_prompt()
        assert result == ""

    def test_empty_builder_messages_no_system(self):
        """空 builder 的 build_messages() 不包含 system 消息。"""
        builder = PromptBuilder()
        messages = builder.build_messages("你好")
        # 无 system prompt 时，messages 只有 user 消息
        assert len(messages) == 1
        assert messages[0]["role"] == "user"


class TestPromptBuilderLayers:
    """PromptBuilder 各层设置测试。"""

    def test_set_role_includes_role_content(self):
        """设置 role 后 system prompt 包含 role 内容。"""
        builder = PromptBuilder()
        builder.set_role("你是一个测试 Agent。")
        result = builder.build_system_prompt()
        assert "你是一个测试 Agent。" in result
        # 应包含角色设定的标题
        assert "角色设定" in result

    def test_all_six_layers_in_order(self):
        """设置所有 6 层后 system prompt 按顺序包含各层。"""
        builder = PromptBuilder()
        builder.set_platform_policy("平台策略内容")
        builder.set_role("角色内容")
        builder.set_task("任务内容")
        builder.set_output_contract("输出格式内容")
        builder.set_tool_rules("工具规则内容")
        builder.set_context_slice("上下文内容")

        result = builder.build_system_prompt()

        # 验证所有层都存在
        assert "平台策略内容" in result
        assert "角色内容" in result
        assert "任务内容" in result
        assert "输出格式内容" in result
        assert "工具规则内容" in result
        assert "上下文内容" in result

        # 验证顺序：平台策略在角色之前，角色在任务之前
        policy_pos = result.index("平台策略内容")
        role_pos = result.index("角色内容")
        task_pos = result.index("任务内容")
        output_pos = result.index("输出格式内容")
        tool_pos = result.index("工具规则内容")
        context_pos = result.index("上下文内容")

        assert policy_pos < role_pos < task_pos < output_pos < tool_pos < context_pos

    def test_build_messages_format(self):
        """build_messages() 返回正确的 system + user 消息列表。"""
        builder = PromptBuilder()
        builder.set_role("测试角色")
        messages = builder.build_messages("用户消息")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "测试角色" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "用户消息"

    def test_chain_style(self):
        """set_xxx 方法支持链式调用。"""
        builder = PromptBuilder()
        result = (
            builder
            .set_platform_policy("policy")
            .set_role("role")
            .set_task("task")
        )
        # 链式调用返回的是同一个 builder 实例
        assert result is builder


class TestGetRolePrompt:
    """get_role_prompt 工厂函数测试。"""

    def test_get_role_prompt_intent(self):
        """get_role_prompt('intent') 返回非空字符串。"""
        prompt = get_role_prompt("intent")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Intent Agent" in prompt

    def test_get_role_prompt_all_agents(self):
        """所有 10 个 agent 的 role prompt 均可正常获取。"""
        agent_names = [
            "intent", "contraction", "planner", "schema",
            "backend", "frontend", "doc", "diagram", "qa", "export",
        ]
        for name in agent_names:
            prompt = get_role_prompt(name)
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_get_role_prompt_nonexistent_raises(self):
        """get_role_prompt('nonexistent') 抛出 KeyError。"""
        with pytest.raises(KeyError, match="未知的 Agent 名称"):
            get_role_prompt("nonexistent")
