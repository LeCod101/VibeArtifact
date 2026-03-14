"""
Doc Agent 的输入输出 Schema 定义。

Doc Agent 负责根据数据模型与 API 契约生成项目文档，
输出 DocPlan（文档文件列表）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import DocPlan, SchemaPlan


class DocInput(AgentInput):
    """
    Doc Agent 专用输入。

    在 AgentInput 基础上添加数据模型与 API 契约作为文档生成依据。
    - schema_plan: 来自 Schema Agent 的数据模型和 API 端点定义
    """

    schema_plan: SchemaPlan


class DocOutput(AgentOutput):
    """
    Doc Agent 专用输出。

    在 AgentOutput 基础上添加文档计划。
    - doc_plan: 生成的文档文件列表
    """

    doc_plan: DocPlan
