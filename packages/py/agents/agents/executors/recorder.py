"""
Agent 运行日志记录器模块。

将每次 Agent 运行的元信息记录下来，用于审计和调试。
Phase 1 先做内存记录，M5 再接入 agent_runs 数据库表。
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from agents.executors.runner import AgentRunResult


class AgentRunRecorder:
    """
    Agent 运行日志记录器。

    将每次 Agent 运行的元信息写入内存列表。
    Phase 1 先做内存记录，M5 再接入数据库。
    """

    def __init__(self) -> None:
        """初始化记录器，创建空的记录列表。"""
        self._records: list[dict] = []

    async def record(
        self, result: AgentRunResult, project_id: UUID
    ) -> None:
        """
        记录一次 Agent 运行。

        从 AgentRunResult 中提取关键信息，存入内存列表。
        - result: Agent 运行结果
        - project_id: 所属项目 ID
        """
        self._records.append(
            {
                "agent_id": result.agent_id,
                "project_id": str(project_id),
                "model": result.meta.model if result.meta else "",
                "prompt_tokens": (
                    result.meta.prompt_tokens if result.meta else 0
                ),
                "completion_tokens": (
                    result.meta.completion_tokens if result.meta else 0
                ),
                "total_cost": (
                    result.meta.total_cost if result.meta else 0.0
                ),
                "latency_ms": (
                    result.meta.latency_ms if result.meta else 0.0
                ),
                "warnings": result.warnings,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_records(self) -> list[dict]:
        """
        获取所有记录（测试用）。

        - 返回: 所有运行记录的字典列表
        """
        return list(self._records)
