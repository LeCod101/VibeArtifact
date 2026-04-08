"""测试 System Prompt 构建器。"""

from __future__ import annotations

from agents.system_prompt import SystemPromptBuilder


class TestSystemPromptBuilder:
    """验证 System Prompt 的构建逻辑。"""

    def setup_method(self) -> None:
        self.builder = SystemPromptBuilder()

    def test_identity_keywords(self) -> None:
        """System Prompt 应包含身份关键词。"""
        prompt = self.builder.build(tools_description="无工具")
        assert "VibeArtifact" in prompt
        assert "编程助手" in prompt

    def test_tools_description_injected(self) -> None:
        """tools_description 应被注入到 prompt 中。"""
        prompt = self.builder.build(tools_description="- **my_tool**: 测试用")
        assert "my_tool" in prompt
        assert "测试用" in prompt

    def test_tech_stacks_empty(self) -> None:
        """tech_stacks 为空时不应出现技术栈段落。"""
        prompt = self.builder.build(tools_description="无", tech_stacks="")
        assert "## 技术栈" not in prompt

    def test_tech_stacks_nonempty(self) -> None:
        """tech_stacks 非空时应注入技术栈段落。"""
        prompt = self.builder.build(
            tools_description="无",
            tech_stacks="Python 3.12, FastAPI",
        )
        assert "## 技术栈" in prompt
        assert "FastAPI" in prompt

    def test_coding_standards_empty(self) -> None:
        """coding_standards 为空时不应出现编码规范段落。"""
        prompt = self.builder.build(tools_description="无", coding_standards="")
        assert "## 编码规范" not in prompt

    def test_coding_standards_nonempty(self) -> None:
        """coding_standards 非空时应注入编码规范段落。"""
        prompt = self.builder.build(
            tools_description="无",
            coding_standards="PEP 8",
        )
        assert "## 编码规范" in prompt
        assert "PEP 8" in prompt
