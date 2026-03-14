"""
Schema Agent 的输入输出 Schema 定义。

Schema Agent 负责根据功能范围草案设计数据模型和 API 契约，
输出 SchemaPlan（实体定义 + 端点定义）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import SchemaPlan, ScopeDraft


class SchemaInput(AgentInput):
    """
    Schema Agent 专用输入。

    在 AgentInput 基础上添加功能范围草案作为设计依据。
    - scope_draft: 来自 Contraction Agent 的收缩后功能范围草案
    """

    scope_draft: ScopeDraft


class SchemaOutput(AgentOutput):
    """
    Schema Agent 专用输出。

    在 AgentOutput 基础上添加数据模型与 API 契约。
    - schema_plan: 设计好的数据模型和 API 端点定义
    """

    schema_plan: SchemaPlan
