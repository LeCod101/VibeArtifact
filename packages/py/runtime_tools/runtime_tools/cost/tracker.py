"""
成本追踪器模块。

记录每次 LLM 调用的 token/cost 数据，支持按项目筛选查询。
Phase 1 先做内存记录，M5 再接入 cost_ledger 数据库表。
"""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel


class CostRecord(BaseModel):
    """
    单条成本记录。

    存储一次 LLM 调用的完整计费信息。
    - agent_id: 调用方 Agent 的唯一标识
    - project_id: 所属项目 ID
    - model: 使用的模型标识
    - provider: 模型提供商名称
    - prompt_tokens: 输入 token 数
    - completion_tokens: 输出 token 数
    - total_cost: 本次调用费用（美元）
    - latency_ms: 调用耗时（毫秒）
    - recorded_at: 记录时间
    """

    agent_id: str
    project_id: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    latency_ms: float
    recorded_at: datetime


class CostTracker:
    """
    成本追踪器。

    记录每次 LLM 调用的 token/cost 数据。
    Phase 1 先做内存记录，M5 再接入 cost_ledger 数据库表。
    """

    def __init__(self) -> None:
        """初始化成本追踪器，创建空的记录列表。"""
        self._records: list[CostRecord] = []

    async def record(
        self,
        agent_id: str,
        project_id: UUID,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_cost: float,
        latency_ms: float,
    ) -> None:
        """
        记录一次 LLM 调用的成本。

        当前为内存实现，预留 async 接口供未来数据库持久化使用（M5 接入 cost_ledger 表）。

        - agent_id: 调用方 Agent 的唯一标识
        - project_id: 所属项目 ID
        - model: 使用的模型标识
        - provider: 模型提供商名称
        - prompt_tokens: 输入 token 数
        - completion_tokens: 输出 token 数
        - total_cost: 本次调用费用（美元）
        - latency_ms: 调用耗时（毫秒）
        """
        self._records.append(
            CostRecord(
                agent_id=agent_id,
                project_id=str(project_id),
                model=model,
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost=total_cost,
                latency_ms=latency_ms,
                recorded_at=datetime.now(timezone.utc),
            )
        )

    def get_total_cost(self, project_id: str | None = None) -> float:
        """
        获取总成本（可按项目筛选）。

        - project_id: 项目 ID，为 None 时返回所有项目的总成本
        - 返回: 总成本金额（美元）
        """
        records = self._records
        if project_id:
            records = [r for r in records if r.project_id == project_id]
        return sum(r.total_cost for r in records)

    def get_records(
        self, project_id: str | None = None
    ) -> list[CostRecord]:
        """
        获取成本记录列表。

        - project_id: 项目 ID，为 None 时返回所有记录
        - 返回: CostRecord 列表
        """
        if project_id:
            return [r for r in self._records if r.project_id == project_id]
        return list(self._records)

    def get_total_tokens(self, project_id: str | None = None) -> int:
        """
        获取总 token 数。

        - project_id: 项目 ID，为 None 时返回所有项目的总 token 数
        - 返回: prompt_tokens + completion_tokens 的总和
        """
        records = self.get_records(project_id)
        return sum(r.prompt_tokens + r.completion_tokens for r in records)
