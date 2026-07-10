"""评审轮次仓储 - 提供 conversation_turns 表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.review import ReviewTurn
from platform_data.repositories.base import BaseRepository


class ReviewTurnRepository(BaseRepository[ReviewTurn]):
    """评审轮次仓储，worker 写入轮次记录、API 查询轮次历史。"""

    model_class = ReviewTurn

    async def write_turns(self, run_id: UUID, turns: list[dict]) -> int:
        """批量写入评审轮次记录。

        每个轮次字典需包含 agent_id、role、round_number 键，
        可选 verdict、content_summary。

        参数:
            run_id: 所属 job_run 的 UUID
            turns: 轮次字典列表

        返回:
            写入的记录数
        """
        for t in turns:
            self.session.add(
                ReviewTurn(
                    run_id=run_id,
                    agent_id=t.get("agent_id", ""),
                    role=t.get("role", ""),
                    round_number=t.get("round_number", 0),
                    verdict=t.get("verdict", ""),
                    content_summary=t.get("content_summary"),
                )
            )
        await self.session.flush()
        return len(turns)

    async def list_by_run(self, run_id: UUID) -> list[ReviewTurn]:
        """按运行查询全部轮次记录（按 agent、轮次、角色排序）。

        参数:
            run_id: job_run 的 UUID

        返回:
            ReviewTurn 实例列表
        """
        stmt = (
            select(ReviewTurn)
            .where(ReviewTurn.run_id == run_id)
            .order_by(
                ReviewTurn.agent_id,
                ReviewTurn.round_number,
                ReviewTurn.created_at,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
