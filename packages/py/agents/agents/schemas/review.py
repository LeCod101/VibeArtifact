"""
Reviewer Agent 的输入输出 Schema 定义。

Reviewer Agent 负责评审配对 author Agent 的产物（代码/文档/图表），
输出结构化评审结论（approve/revise + 具体意见），驱动
author↔reviewer 多轮循环（conversation_graph）。
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from agents.schemas.base import AgentInput, AgentOutput


class ReviewVerdict(StrEnum):
    """评审结论枚举。"""

    APPROVE = "approve"
    REVISE = "revise"


class ReviewComment(BaseModel):
    """
    单条评审意见。

    - severity: 严重程度（critical 必须修复 / suggestion 建议改进）
    - file_path: 相关文件路径（可选，全局意见时为空）
    - comment: 意见内容，需具体、可执行
    """

    severity: Literal["critical", "suggestion"]
    file_path: str = ""
    comment: str


class ReviewFeedback(BaseModel):
    """
    评审反馈（Reviewer Agent 的高层输出）。

    - verdict: 评审结论，approve 表示通过，revise 表示需要修改
    - comments: 具体评审意见列表（revise 时必须非空）
    - summary: 一句话评审总结
    """

    verdict: ReviewVerdict
    comments: list[ReviewComment] = []
    summary: str = ""


class ReviewInput(AgentInput):
    """
    Reviewer Agent 专用输入。

    在 AgentInput 基础上标记被评审的 author Agent。
    workspace_files 携带 author 本轮产出的文件。
    - author_agent_id: 被评审的 author Agent 标识
    - round_number: 当前评审轮次（从 1 开始）
    """

    author_agent_id: str = ""
    round_number: int = 1


class ReviewOutput(AgentOutput):
    """
    Reviewer Agent 专用输出。

    在 AgentOutput 基础上添加结构化评审反馈。
    - review: 评审反馈（verdict + comments + summary）
    """

    review: ReviewFeedback
