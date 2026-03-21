"""快照仓储 - 提供 IR 快照表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.ir import IREdge, IRNode, IRSnapshot, SnapshotStatus
from platform_data.repositories.base import BaseRepository


class SnapshotRepository(BaseRepository[IRSnapshot]):
    """快照仓储，继承通用 CRUD 并提供查询活跃快照、创建空快照等方法。"""

    model_class = IRSnapshot

    async def get_active(self, project_id: UUID) -> IRSnapshot | None:
        """查询指定项目的最新活跃快照。

        按 version 降序排列，取第一条 status=active 的快照。

        参数:
            project_id: 项目 UUID

        返回:
            最新的活跃快照实例，不存在则返回 None
        """
        stmt = (
            select(IRSnapshot)
            .where(
                IRSnapshot.project_id == project_id,
                IRSnapshot.status == SnapshotStatus.active,
            )
            .order_by(IRSnapshot.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_empty(
        self,
        project_id: UUID,
        parent_snapshot_id: UUID | None = None,
    ) -> IRSnapshot:
        """创建一个空的 IR 快照。

        自动计算版本号：如果有父快照则基于父快照版本 +1，否则从 1 开始。

        参数:
            project_id: 所属项目的 UUID
            parent_snapshot_id: 父快照 UUID，可选

        返回:
            新创建的快照实例
        """
        # 计算新版本号
        version = 1
        if parent_snapshot_id is not None:
            parent = await self.get_by_id(parent_snapshot_id)
            if parent is not None:
                version = parent.version + 1

        snapshot = IRSnapshot(
            project_id=project_id,
            parent_snapshot_id=parent_snapshot_id,
            version=version,
            status=SnapshotStatus.active,
        )
        return await self.create(snapshot)

    async def load_snapshot_graph(
        self, snapshot_id: UUID
    ) -> tuple[list[IRNode], list[IREdge]]:
        """加载指定快照的所有节点和边。

        参数:
            snapshot_id: 快照 UUID

        返回:
            (nodes, edges) 元组，分别为 IRNode 和 IREdge ORM 对象列表
        """
        # 查询该快照下的所有节点
        node_stmt = select(IRNode).where(
            IRNode.snapshot_id == snapshot_id
        )
        node_result = await self.session.execute(node_stmt)
        nodes = list(node_result.scalars().all())

        # 查询该快照下的所有边
        edge_stmt = select(IREdge).where(
            IREdge.snapshot_id == snapshot_id
        )
        edge_result = await self.session.execute(edge_stmt)
        edges = list(edge_result.scalars().all())

        return nodes, edges
