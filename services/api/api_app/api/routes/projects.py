"""项目路由模块 - 实现项目的创建、列表查询和详情查询端点。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.projects import CreateProjectRequest, ProjectResponse
from api_app.application.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """创建新项目。

    自动初始化关联资源：空 IR 快照、默认对话和默认分支。

    参数：
        body: 创建项目请求体（包含 name、description）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ProjectResponse（新创建的项目信息）
    """
    service = ProjectService(db)
    project = await service.create_project(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    await db.commit()
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """查询当前用户的项目列表。

    参数：
        offset: 跳过的记录数，默认 0
        limit: 返回的最大记录数，默认 100
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        当前用户拥有的项目列表
    """
    service = ProjectService(db)
    projects = await service.list_projects(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """查询项目详情。

    需验证项目属于当前用户，不属于则返回 404。

    参数：
        project_id: 项目 UUID（路径参数）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ProjectResponse（项目详情）

    异常：
        404: 项目不存在或不属于当前用户
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)

    # 项目不存在或不属于当前用户
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    return project
