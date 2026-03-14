"""
Agent 间数据传递模块。

定义 StepInput 数据结构，实现 Agent 步骤输入的组装逻辑。
Phase 1 简化实现：直接把 scope_draft + 前置 agent 输出的 JSON 摘要传递。
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


class StepInput(BaseModel):
    """
    Agent 步骤输入数据结构。

    封装单个 agent 执行时需要的所有上下文信息。
    - agent_id: 当前要执行的 agent 标识
    - snapshot_id: 当前 IR 快照 ID
    - scope_draft: 初始的 scope_draft 数据
    - predecessor_outputs: 前置 agent 的输出摘要，key=agent_id, value=输出摘要
    """

    agent_id: str
    snapshot_id: str
    scope_draft: dict[str, Any] = {}
    predecessor_outputs: dict[str, Any] = {}

    def to_json(self) -> str:
        """
        序列化为 JSON 字符串。

        用于通过 Celery 消息传递。
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> StepInput:
        """
        从 JSON 字符串反序列化。

        - json_str: JSON 字符串
        返回 StepInput 实例。
        """
        return cls.model_validate_json(json_str)


class CompletedStep(BaseModel):
    """
    已完成步骤的输出摘要。

    用于记录前置 agent 的执行结果，供后续 agent 使用。
    - agent_id: 已完成的 agent 标识
    - status: 执行状态（completed / failed）
    - output_summary: 输出摘要（JSON 可序列化的字典）
    """

    agent_id: str
    status: str = "completed"
    output_summary: dict[str, Any] = {}


def assemble_step_input(
    agent_id: str,
    snapshot_id: str,
    scope_draft: dict[str, Any],
    completed_steps: list[CompletedStep] | None = None,
) -> StepInput:
    """
    组装单个 agent 步骤的输入。

    Phase 1 简化实现：
    1. 将 scope_draft 直接传递
    2. 将前置 agent 的输出摘要按 agent_id 汇总到 predecessor_outputs

    - agent_id: 当前 agent 标识
    - snapshot_id: 快照 ID
    - scope_draft: 初始 scope_draft 数据
    - completed_steps: 已完成的前置步骤列表
    返回 StepInput 实例。
    """
    predecessor_outputs: dict[str, Any] = {}

    if completed_steps:
        for step in completed_steps:
            # 只收集成功完成的步骤输出
            if step.status == "completed":
                predecessor_outputs[step.agent_id] = step.output_summary

    return StepInput(
        agent_id=agent_id,
        snapshot_id=snapshot_id,
        scope_draft=scope_draft,
        predecessor_outputs=predecessor_outputs,
    )


def parse_scope_draft(scope_draft_json: str) -> dict[str, Any]:
    """
    解析 scope_draft JSON 字符串。

    安全解析，如果 JSON 无效则返回空字典。
    - scope_draft_json: scope_draft 的 JSON 字符串
    返回解析后的字典。
    """
    try:
        return json.loads(scope_draft_json)
    except (json.JSONDecodeError, TypeError):
        return {}
