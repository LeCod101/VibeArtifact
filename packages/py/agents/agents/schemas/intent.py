"""
Intent Agent 的输入输出 Schema 定义。

Intent Agent 负责从用户的原始想法中提取产品意图，
生成初始的功能范围草案（ScopeDraft）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ScopeDraft


class IntentInput(AgentInput):
    """
    Intent Agent 专用输入。

    在 AgentInput 基础上添加用户的原始想法。
    - user_idea: 用户输入的原始产品想法
    """

    user_idea: str


class IntentOutput(AgentOutput):
    """
    Intent Agent 专用输出。

    在 AgentOutput 基础上添加功能范围草案。
    - scope_draft: 从用户想法中提取的功能范围草案
    """

    scope_draft: ScopeDraft
