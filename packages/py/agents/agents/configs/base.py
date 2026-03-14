"""
Agent 配置基础类型模块。

定义 Agent 配置相关的核心数据结构：
- RoleCategory: Agent 角色类别枚举
- ModelTier: 从 runtime_tools.llm.config 统一导入的模型档位枚举
- AgentConfig: Agent 静态配置数据类
"""

from enum import StrEnum

from pydantic import BaseModel
from runtime_tools.llm.config import ModelTier


class RoleCategory(StrEnum):
    """
    Agent 角色类别。

    将 Agent 按职责划分为不同类别，
    用于分组管理和 DAG 编排。
    """

    INTENT_PLANNING = "intent_planning"
    SCHEMA = "schema"
    BUILD = "build"
    DOCUMENTATION = "documentation"
    QA = "qa"
    DELIVERY = "delivery"


class AgentConfig(BaseModel):
    """
    Agent 配置定义。

    每个 Agent 的静态配置，包含标识、角色、模型档位和 schema 类型信息。
    用于 AgentRegistry 统一管理所有 Agent 元数据。

    - agent_id: 唯一标识，如 "intent"
    - name: 显示名称，如 "Intent Agent"
    - description: 职责描述
    - role_category: 角色类别
    - model_tier: 模型档位
    - input_schema: 输入 schema 类型引用（Pydantic BaseModel 子类）
    - output_schema: 输出 schema 类型引用（Pydantic BaseModel 子类）
    - high_level_key: 输出中高层结构体的字段名，如 "scope_draft"
    - dependencies: 依赖的其他 agent_id 列表（用于 DAG 编排）
    """

    # 允许 type[BaseModel] 类型作为字段值
    # 禁用 model_ 前缀保护，因为 model_tier 等字段需要使用该前缀
    model_config = {
        "arbitrary_types_allowed": True,
        "protected_namespaces": (),
    }

    agent_id: str
    name: str
    description: str
    role_category: RoleCategory
    model_tier: ModelTier
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    high_level_key: str
    dependencies: list[str] = []
