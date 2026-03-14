"""
Planner Agent 的输入输出 Schema 定义。

Planner Agent 负责根据收缩后的功能范围草案，
生成任务执行计划（TaskPlan），编排后续 Agent 的执行顺序。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ScopeDraft, TaskPlan


class PlannerInput(AgentInput):
    """
    Planner Agent 专用输入。

    在 AgentInput 基础上添加收缩后的功能范围草案。
    - scope_draft: 来自 Contraction Agent 的收缩后功能范围草案
    """

    scope_draft: ScopeDraft


class PlannerOutput(AgentOutput):
    """
    Planner Agent 专用输出。

    在 AgentOutput 基础上添加任务执行计划。
    - task_plan: 编排后的任务执行计划
    """

    task_plan: TaskPlan
