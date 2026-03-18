"""快照路由模块 - 实现快照的列表查询和详情查询端点。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.ir import IREdge, IRNode, IRSnapshot, SnapshotStatus
from platform_data.models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.snapshots import (
    SnapshotDetailResponse,
    SnapshotSummaryResponse,
)
from api_app.application.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects/{project_id}/snapshots",
    tags=["snapshots"],
)


async def _verify_project_owner(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """验证项目属于当前用户，不属于则抛出 404。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


@router.get("", response_model=list[SnapshotSummaryResponse])
async def list_snapshots(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SnapshotSummaryResponse]:
    """列出项目的所有快照，按创建时间倒序排列。

    返回每个快照的节点数和边数统计。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        快照摘要列表
    """
    await _verify_project_owner(project_id, current_user, db)

    # 查询该项目的所有快照
    result = await db.execute(
        select(IRSnapshot)
        .where(IRSnapshot.project_id == project_id)
        .order_by(IRSnapshot.created_at.desc())
    )
    snapshots = result.scalars().all()

    # 找到当前活跃快照（版本最高的 active 快照）
    active_snapshot = None
    for s in snapshots:
        if s.status == SnapshotStatus.active:
            active_snapshot = s
            break

    responses = []
    for snap in snapshots:
        # 统计节点数
        node_count_result = await db.execute(
            select(func.count())
            .select_from(IRNode)
            .where(IRNode.snapshot_id == snap.id)
        )
        node_count = node_count_result.scalar_one()

        # 统计边数
        edge_count_result = await db.execute(
            select(func.count())
            .select_from(IREdge)
            .where(IREdge.snapshot_id == snap.id)
        )
        edge_count = edge_count_result.scalar_one()

        responses.append(
            SnapshotSummaryResponse(
                id=snap.id,
                created_at=snap.created_at,
                parent_id=snap.parent_snapshot_id,
                node_count=node_count,
                edge_count=edge_count,
                is_current=(
                    active_snapshot is not None
                    and snap.id == active_snapshot.id
                ),
            )
        )

    return responses


@router.get("/{snapshot_id}", response_model=SnapshotDetailResponse)
async def get_snapshot(
    project_id: UUID,
    snapshot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SnapshotDetailResponse:
    """查询快照详情，包含节点和边的摘要信息。

    参数：
        project_id: 项目 UUID
        snapshot_id: 快照 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        快照详情（含节点和边列表）

    异常：
        404: 快照不存在或不属于该项目
    """
    await _verify_project_owner(project_id, current_user, db)

    # 查询快照
    result = await db.execute(
        select(IRSnapshot).where(
            IRSnapshot.id == snapshot_id,
            IRSnapshot.project_id == project_id,
        )
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="快照不存在",
        )

    # 查询节点
    nodes_result = await db.execute(
        select(IRNode).where(IRNode.snapshot_id == snapshot_id)
    )
    nodes = [
        {
            "id": str(n.id),
            "node_type": n.node_type,
            "label": n.label,
        }
        for n in nodes_result.scalars().all()
    ]

    # 查询边
    edges_result = await db.execute(
        select(IREdge).where(IREdge.snapshot_id == snapshot_id)
    )
    edges = [
        {
            "id": str(e.id),
            "edge_type": e.edge_type,
            "source_node_id": str(e.source_node_id),
            "target_node_id": str(e.target_node_id),
        }
        for e in edges_result.scalars().all()
    ]

    return SnapshotDetailResponse(
        id=snapshot.id,
        created_at=snapshot.created_at,
        parent_id=snapshot.parent_snapshot_id,
        nodes=nodes,
        edges=edges,
    )
