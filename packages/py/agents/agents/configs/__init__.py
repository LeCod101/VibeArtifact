"""
Agent 配置与注册统一导出模块。

集中导出 Agent 配置相关的所有类型和函数，
方便外部一次性 import 所需的配置类和注册表。
"""

from agents.configs.base import AgentConfig, ModelTier, RoleCategory
from agents.configs.definitions import register_all_agents
from agents.configs.registry import AgentRegistry

__all__ = [
    "RoleCategory",
    "ModelTier",
    "AgentConfig",
    "AgentRegistry",
    "register_all_agents",
]
