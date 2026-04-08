"""测试 Agent 模式系统。"""

from __future__ import annotations

import pytest
from agents.modes import AgentMode, ModeConfig, get_mode_config


class TestAgentMode:
    """验证模式枚举和配置获取。"""

    def test_enum_values(self) -> None:
        """枚举应有 auto / discussion / thinking 三个值。"""
        assert AgentMode.AUTO == "auto"
        assert AgentMode.DISCUSSION == "discussion"
        assert AgentMode.THINKING == "thinking"

    def test_auto_config(self) -> None:
        """auto 模式应启用全部工具，温度 0.7。"""
        cfg = get_mode_config(AgentMode.AUTO)
        assert isinstance(cfg, ModeConfig)
        assert cfg.tools_enabled is True
        assert cfg.allowed_tools is None
        assert cfg.temperature == pytest.approx(0.7)

    def test_discussion_allowed_tools(self) -> None:
        """discussion 模式应仅允许 explain_code 和 ask_clarification。"""
        cfg = get_mode_config(AgentMode.DISCUSSION)
        assert cfg.allowed_tools is not None
        assert cfg.allowed_tools == frozenset({"explain_code", "ask_clarification"})

    def test_thinking_temperature(self) -> None:
        """thinking 模式温度应为 0.3。"""
        cfg = get_mode_config(AgentMode.THINKING)
        assert cfg.temperature == pytest.approx(0.3)

    def test_invalid_mode_enum_raises(self) -> None:
        """构造非法 AgentMode 枚举应抛出 ValueError。"""
        with pytest.raises(ValueError):
            AgentMode("nonexistent")

    def test_get_mode_config_unmapped_raises(self) -> None:
        """get_mode_config 收到未映射的值时应抛出 ValueError。"""
        with pytest.raises(ValueError, match="未知的 Agent 模式"):
            get_mode_config("unmapped_value")  # type: ignore[arg-type]
