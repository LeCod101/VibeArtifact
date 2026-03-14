"""
Contraction Agent 的输入输出 Schema 定义。

Contraction Agent 负责对 Intent Agent 产出的功能范围草案进行收缩，
删减非 MVP 功能，输出精简后的 ScopeDraft 和收缩决策详情。
"""

from pydantic import BaseModel

from agents.capacity.calculator import CapacityReport
from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ScopeDraft


class ContractionInput(AgentInput):
    """
    Contraction Agent 专用输入。

    在 AgentInput 基础上添加待收缩的功能范围草案和容量报告。
    - scope_draft: 来自 Intent Agent 的初始功能范围草案
    - capacity_report: 容量评估报告，包含总点数、分档和各维度明细
    """

    scope_draft: ScopeDraft
    capacity_report: CapacityReport


class DeferredFeature(BaseModel):
    """
    被延后的功能描述。

    包含功能名称和延后理由。
    - name: 被延后的功能名称
    - reason: 延后理由，引用收缩决策维度之一
    """

    name: str
    reason: str


class ContractionDecision(BaseModel):
    """
    收缩决策详情。

    记录收缩过程中的所有决策信息，包括保留和延后的功能、
    收缩带来的风险以及整体收缩理由。
    - retained_features: 保留的功能名称列表
    - deferred_features: 延后的功能列表，每项包含名称和理由
    - risks: 收缩带来的风险描述列表
    - rationale: 整体收缩理由
    """

    retained_features: list[str]
    deferred_features: list[DeferredFeature]
    risks: list[str]
    rationale: str


class ContractionOutput(AgentOutput):
    """
    Contraction Agent 专用输出。

    在 AgentOutput 基础上添加收缩后的功能范围草案和收缩决策详情。
    - scope_draft: 经过 MVP 收缩后的功能范围草案
    - decision: 收缩决策详情，包含保留/延后的功能和理由
    """

    scope_draft: ScopeDraft
    decision: ContractionDecision
