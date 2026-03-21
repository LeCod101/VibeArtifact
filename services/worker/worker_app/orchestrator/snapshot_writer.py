"""
IR 快照读写器模块。

封装快照的数据库读写操作，包括加载已有快照的节点和边，
以及创建新快照并批量写入节点和边。

数据库操作使用 SQLAlchemy 2 async session，
与 RunManager 共享同一套 Worker 端会话管理。
"""

from __future__ import annotations

from uuid import UUID, uuid4

from ir_core.schema.data import IREdgeData, IRNodeData
from platform_data.models.ir import (
    IREdge,
    IRNode,
    IRSnapshot,
    SnapshotStatus,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# 复用 RunManager 中定义的 Worker 端会话工厂
from worker_app.orchestrator.run_manager import get_worker_session_factory


class SnapshotWriter:
    """
    IR 快照读写器，封装快照的数据库操作。

    职责：
    - 从数据库加载指定快照的全部节点和边（转为 DTO）
    - 基于父快照创建新快照，批量写入节点和边
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        """
        初始化快照读写器。

        - session_factory: 异步 Session 工厂，为 None 时使用默认工厂
        """
        self._session_factory = (
            session_factory or get_worker_session_factory()
        )

    async def load_snapshot(
        self, snapshot_id: UUID,
    ) -> tuple[list[IRNodeData], list[IREdgeData]]:
        """
        从数据库加载指定快照的所有节点和边。

        查询 ir_nodes 和 ir_edges 表中 snapshot_id 匹配的记录，
        转换为 DTO 对象返回。

        - snapshot_id: 目标快照 ID
        返回 (节点列表, 边列表) 的元组。
        """
        async with self._session_factory() as session:
            # 查询该快照下所有节点
            node_result = await session.execute(
                select(IRNode).where(IRNode.snapshot_id == snapshot_id)
            )
            node_rows = node_result.scalars().all()

            # 查询该快照下所有边
            edge_result = await session.execute(
                select(IREdge).where(IREdge.snapshot_id == snapshot_id)
            )
            edge_rows = edge_result.scalars().all()

        # 将 ORM 对象转换为 DTO
        nodes = [
            IRNodeData(
                id=row.id,
                node_type=row.node_type,
                label=row.label,
                # ORM 层 props 可能为 None，DTO 要求 dict
                props=row.props or {},
                position_x=row.position_x,
                position_y=row.position_y,
            )
            for row in node_rows
        ]

        edges = [
            IREdgeData(
                id=row.id,
                source_node_id=row.source_node_id,
                target_node_id=row.target_node_id,
                edge_type=row.edge_type,
                props=row.props,
            )
            for row in edge_rows
        ]

        return nodes, edges

    async def write_snapshot(
        self,
        project_id: UUID,
        parent_snapshot_id: UUID,
        nodes: list[IRNodeData],
        edges: list[IREdgeData],
    ) -> UUID:
        """
        创建新快照并写入节点和边，返回新快照 ID。

        流程：
        1. 查询父快照的版本号
        2. 创建新 IRSnapshot，版本号 = 父版本 + 1
        3. 批量插入 IRNode 记录
        4. 批量插入 IREdge 记录
        5. 返回新快照 ID

        - project_id: 所属项目 ID
        - parent_snapshot_id: 父快照 ID（用于版本号递增）
        - nodes: 要写入的节点 DTO 列表
        - edges: 要写入的边 DTO 列表
        返回新创建的快照 ID。
        """
        new_snapshot_id = uuid4()

        async with self._session_factory() as session:
            async with session.begin():
                # 查询父快照的版本号
                parent_result = await session.execute(
                    select(IRSnapshot.version).where(
                        IRSnapshot.id == parent_snapshot_id,
                    )
                )
                parent_version = parent_result.scalar_one()

                # 创建新快照记录，版本号递增
                snapshot = IRSnapshot(
                    id=new_snapshot_id,
                    project_id=project_id,
                    parent_snapshot_id=parent_snapshot_id,
                    version=parent_version + 1,
                    status=SnapshotStatus.active,
                )
                session.add(snapshot)

                # 批量插入节点
                for node in nodes:
                    ir_node = IRNode(
                        id=node.id,
                        snapshot_id=new_snapshot_id,
                        node_type=node.node_type,
                        label=node.label,
                        props=node.props,
                        position_x=node.position_x,
                        position_y=node.position_y,
                    )
                    session.add(ir_node)

                # 批量插入边
                for edge in edges:
                    ir_edge = IREdge(
                        id=edge.id,
                        snapshot_id=new_snapshot_id,
                        source_node_id=edge.source_node_id,
                        target_node_id=edge.target_node_id,
                        edge_type=edge.edge_type,
                        props=edge.props,
                    )
                    session.add(ir_edge)

        return new_snapshot_id
