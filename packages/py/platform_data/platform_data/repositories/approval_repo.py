"""审批仓储 - 提供审批记录表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.approval import ApprovalRecord
from platform_data.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalRecord]):
    """审批仓储，继承通用 CRUD 并提供按运行查询、获取最新审批等方法。"""

    model_class = ApprovalRecord

    async def get_by_run(self, run_id: UUID) -> list[ApprovalRecord]:
        """查询指定运行的所有审批记录，按创建时间升序排列。

        参数:
            run_id: 运行 UUID

        返回:
            该运行下的审批记录列表
        """
        stmt = (
            select(ApprovalRecord)
            .where(ApprovalRecord.run_id == run_id)
            .order_by(ApprovalRecord.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_run(self, run_id: UUID) -> ApprovalRecord | None:
        """获取指定运行的最新一条审批记录。

        参数:
            run_id: 运行 UUID

        返回:
            最新的审批记录实例，不存在则返回 None
        """
        stmt = (
            select(ApprovalRecord)
            .where(ApprovalRecord.run_id == run_id)
            .order_by(ApprovalRecord.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
