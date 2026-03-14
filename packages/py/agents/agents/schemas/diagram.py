"""
Diagram Agent 的输入输出 Schema 定义。

Diagram Agent 负责根据数据模型与 API 契约生成 Mermaid 图表，
输出 DiagramPlan（图表定义列表）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import DiagramPlan, SchemaPlan


class DiagramInput(AgentInput):
    """
    Diagram Agent 专用输入。

    在 AgentInput 基础上添加数据模型与 API 契约作为图表生成依据。
    - schema_plan: 来自 Schema Agent 的数据模型和 API 端点定义
    """

    schema_plan: SchemaPlan


class DiagramOutput(AgentOutput):
    """
    Diagram Agent 专用输出。

    在 AgentOutput 基础上添加图表计划。
    - diagram_plan: 生成的 Mermaid 图表列表
    """

    diagram_plan: DiagramPlan
