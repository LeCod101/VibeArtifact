"""Agent 模式定义。

定义 auto、discussion、thinking 三种模式，
每种模式影响可用工具集、模型选择和温度参数。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgentMode(StrEnum):
    """Agent 运行模式枚举。"""

    AUTO = "auto"
    DISCUSSION = "discussion"
    THINKING = "thinking"


@dataclass(frozen=True)
class ModeConfig:
    """模式配置，控制单次对话的工具可用性、模型和温度。

    Attributes:
        name: 模式名称
        description: 模式用途说明
        tools_enabled: 是否允许使用工具
        model_override: 覆盖默认模型的标识，None 表示使用默认模型
        temperature: 采样温度
        allowed_tools: 该模式下允许使用的工具名集合，None 表示全部可用
        use_reasoning_model: 为 True 时 Agent 使用 config.reasoning_model
    """

    name: str
    description: str
    tools_enabled: bool
    model_override: str | None
    temperature: float
    allowed_tools: frozenset[str] | None = None
    use_reasoning_model: bool = False


_DISCUSSION_ALLOWED_TOOLS = frozenset({"explain_code", "ask_clarification"})

_MODE_CONFIGS: dict[AgentMode, ModeConfig] = {
    AgentMode.AUTO: ModeConfig(
        name="auto",
        description="自动模式：所有工具可用，适合一般需求",
        tools_enabled=True,
        model_override=None,
        temperature=0.7,
    ),
    AgentMode.DISCUSSION: ModeConfig(
        name="discussion",
        description="讨论模式：仅保留解释和追问工具，适合概念探讨",
        tools_enabled=True,
        model_override=None,
        temperature=0.8,
        allowed_tools=_DISCUSSION_ALLOWED_TOOLS,
    ),
    AgentMode.THINKING: ModeConfig(
        name="thinking",
        description="深度思考模式：所有工具可用，使用推理模型，低温度",
        tools_enabled=True,
        model_override=None,
        temperature=0.3,
        use_reasoning_model=True,
    ),
}


def get_mode_config(mode: AgentMode) -> ModeConfig:
    """根据模式枚举获取对应的配置。"""
    config = _MODE_CONFIGS.get(mode)
    if config is None:
        raise ValueError(f"未知的 Agent 模式: {mode}")
    return config
