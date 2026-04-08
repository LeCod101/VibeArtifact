"""产物路由模块 - 实现产物的列表查询、详情、编辑和版本历史端点。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.artifact import Artifact
from platform_data.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.artifacts import (
    ArtifactListItem,
    ArtifactResponse,
    ArtifactUpdateRequest,
    ArtifactVersionResponse,
)
from api_app.application.services.project_service import ProjectService

router = APIRouter(tags=["artifacts"])


async def _verify_project_owner(
    project_id: UUID, current_user: User, db: AsyncSession,
) -> None:
    """验证项目属于当前用户。"""
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


async def _get_artifact_with_auth(
    artifact_id: UUID, current_user: User, db: AsyncSession,
) -> Artifact:
    """获取产物并验证所属项目属于当前用户。"""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id),
    )
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产物不存在",
        )

    await _verify_project_owner(artifact.project_id, current_user, db)
    return artifact


# ──────────────────────────────────────
# 列出项目产物
# ──────────────────────────────────────

@router.get(
    "/projects/{project_id}/artifacts",
    response_model=list[ArtifactListItem],
)
async def list_artifacts(
    project_id: UUID,
    artifact_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactListItem]:
    """列出项目的所有产物（仅最新版本）。

    参数：
        project_id: 项目 UUID
        artifact_type: 按类型过滤，可选
        offset: 分页偏移
        limit: 分页大小

    返回：
        产物列表（不含 content 正文）
    """
    await _verify_project_owner(project_id, current_user, db)

    stmt = (
        select(Artifact)
        .where(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if artifact_type is not None:
        stmt = stmt.where(Artifact.artifact_type == artifact_type)

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ──────────────────────────────────────
# 产物详情
# ──────────────────────────────────────

@router.get(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def get_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """获取产物详情（含完整 content）。"""
    artifact = await _get_artifact_with_auth(artifact_id, current_user, db)
    return artifact  # type: ignore[return-value]


# ──────────────────────────────────────
# 编辑产物（创建新版本）
# ──────────────────────────────────────

@router.put(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def update_artifact(
    artifact_id: UUID,
    body: ArtifactUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    """编辑产物，创建新版本。

    不修改原记录，而是创建一条新记录（parent_id 指向原记录，version_num +1），
    保持完整版本历史。
    """
    original = await _get_artifact_with_auth(artifact_id, current_user, db)

    new_artifact = Artifact(
        project_id=original.project_id,
        artifact_type=original.artifact_type,
        title=body.title if body.title is not None else original.title,
        content=body.content if body.content is not None else original.content,
        file_path=body.file_path if body.file_path is not None else original.file_path,
        language=body.language if body.language is not None else original.language,
        version_num=original.version_num + 1,
        parent_id=original.id,
    )
    db.add(new_artifact)
    await db.commit()
    await db.refresh(new_artifact)

    return new_artifact  # type: ignore[return-value]


# ──────────────────────────────────────
# 版本历史
# ──────────────────────────────────────

@router.get(
    "/artifacts/{artifact_id}/versions",
    response_model=list[ArtifactVersionResponse],
)
async def list_artifact_versions(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactVersionResponse]:
    """获取产物的版本历史链。

    从指定产物沿 parent_id 链回溯，返回所有版本。
    """
    artifact = await _get_artifact_with_auth(artifact_id, current_user, db)

    # 收集版本链：从当前版本沿 parent_id 回溯
    versions: list[Artifact] = [artifact]
    current = artifact
    while current.parent_id is not None:
        result = await db.execute(
            select(Artifact).where(Artifact.id == current.parent_id),
        )
        parent = result.scalar_one_or_none()
        if parent is None:
            break
        versions.append(parent)
        current = parent

    # 同时查找以 artifact_id 为 parent 的后续版本
    result = await db.execute(
        select(Artifact)
        .where(Artifact.parent_id == artifact_id)
        .order_by(Artifact.version_num.asc()),
    )
    children = list(result.scalars().all())
    versions.extend(children)

    # 按 version_num 排序后返回
    versions.sort(key=lambda a: a.version_num)

    return versions  # type: ignore[return-value]
