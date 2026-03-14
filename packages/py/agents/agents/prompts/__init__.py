"""
Prompt 系统模块。

提供 Prompt 分层拼装器和角色模板，用于构建 Agent 的 system prompt。

主要导出：
- PromptBuilder: 6 层 Prompt 拼装器
- PromptLayer: Prompt 层枚举
- DEFAULT_PLATFORM_POLICY: 默认平台策略文本
- get_role_prompt: 根据 Agent 名称获取角色 prompt
- ROLE_PROMPTS: 所有 Agent 的角色 prompt 字典
"""

from agents.prompts.builder import (
    DEFAULT_PLATFORM_POLICY,
    PromptBuilder,
    PromptLayer,
)
from agents.prompts.templates.role_prompts import (
    ROLE_PROMPTS,
    get_role_prompt,
)

__all__ = [
    "PromptBuilder",
    "PromptLayer",
    "DEFAULT_PLATFORM_POLICY",
    "get_role_prompt",
    "ROLE_PROMPTS",
]
