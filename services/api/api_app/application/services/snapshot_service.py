"""快照服务 - 封装 IR 快照的创建和查询业务逻辑。"""

from uuid import UUID

from platform_data.models.ir import IRSnapshot
from platform_data.repositories.snapshot_repo import SnapshotRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SnapshotService:
    """快照业务服务层，封装 SnapshotRepository 的调用。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化快照服务。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.snapshot_repo = SnapshotRepository(session)

    async def create_empty(
        self,
        project_id: UUID,
        parent_snapshot_id: UUID | None = None,
    ) -> IRSnapshot:
        """创建一个空的 IR 快照。

        参数:
            project_id: 所属项目的 UUID
            parent_snapshot_id: 父快照 UUID，可选

        返回:
            新创建的快照实例
        """
        return await self.snapshot_repo.create_empty(
            project_id=project_id,
            parent_snapshot_id=parent_snapshot_id,
        )

    async def get_active(self, project_id: UUID) -> IRSnapshot | None:
        """查询指定项目的最新活跃快照。

        参数:
            project_id: 项目 UUID

        返回:
            最新的活跃快照实例，不存在则返回 None
        """
        return await self.snapshot_repo.get_active(project_id)
