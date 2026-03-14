"""
Backend Agent 的输入输出 Schema 定义。

Backend Agent 负责根据数据模型与 API 契约生成后端代码文件，
输出 BackendPlan（后端代码文件列表）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import BackendPlan, SchemaPlan


class BackendInput(AgentInput):
    """
    Backend Agent 专用输入。

    在 AgentInput 基础上添加数据模型与 API 契约作为编码依据。
    - schema_plan: 来自 Schema Agent 的数据模型和 API 端点定义
    """

    schema_plan: SchemaPlan


class BackendOutput(AgentOutput):
    """
    Backend Agent 专用输出。

    在 AgentOutput 基础上添加后端代码计划。
    - backend_plan: 生成的后端代码文件列表
    """

    backend_plan: BackendPlan
