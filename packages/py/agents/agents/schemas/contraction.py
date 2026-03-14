"""
Contraction Agent 的输入输出 Schema 定义。

Contraction Agent 负责对 Intent Agent 产出的功能范围草案进行收缩，
删减非 MVP 功能，输出精简后的 ScopeDraft。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ScopeDraft


class ContractionInput(AgentInput):
    """
    Contraction Agent 专用输入。

    在 AgentInput 基础上添加待收缩的功能范围草案。
    - scope_draft: 来自 Intent Agent 的初始功能范围草案
    """

    scope_draft: ScopeDraft


class ContractionOutput(AgentOutput):
    """
    Contraction Agent 专用输出。

    在 AgentOutput 基础上添加收缩后的功能范围草案。
    - scope_draft: 经过 MVP 收缩后的功能范围草案
    """

    scope_draft: ScopeDraft
