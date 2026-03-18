"""产物路由模块 - 实现产物的列表查询端点。

Phase 1 阶段暂无独立的 artifacts 数据表，返回空列表。
TODO: Phase 2 引入 artifacts 表后替换为真实数据查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.artifacts import ArtifactResponse
from api_app.application.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["artifacts"],
)


@router.get("", response_model=list[ArtifactResponse])
async def list_artifacts(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactResponse]:
    """列出项目的所有产物。

    Phase 1 阶段暂无独立的 artifacts 数据表，返回空列表。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        产物列表（Phase 1 返回空列表）
    """
    # 验证项目归属
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # TODO: Phase 2 引入 artifacts 表后，替换为真实数据查询
    return []
