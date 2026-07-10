"""快照路由模块（已废弃）+ 工作区文件查询端点。

IR 快照体系已被工作区文件（workspace_files）取代：
- GET /projects/{id}/snapshots 保留为废弃 stub（恒返回空列表），
  待前端移除快照统计后删除。
- GET /projects/{id}/runs/{run_id}/files 提供工作区文件清单查询。
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.execution import JobRun
from platform_data.models.user import User
from platform_data.repositories.workspace_repo import WorkspaceRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.application.services.project_service import ProjectService

router = APIRouter(
    prefix="/projects/{project_id}",
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


@router.get("/snapshots", response_model=list[dict], deprecated=True)
async def list_snapshots(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """已废弃：IR 快照体系已移除，恒返回空列表。

    保留此端点仅为兼容旧版前端的快照统计展示，
    前端改造后将删除。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        空列表
    """
    await _verify_project_owner(project_id, current_user, db)
    return []


@router.get("/runs/{run_id}/files")
async def list_run_files(
    project_id: UUID,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """查询指定运行的工作区文件清单。

    返回文件路径、类别、版本和产出 Agent，不含文件内容
    （完整内容通过 ZIP 下载端点获取）。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        工作区文件摘要列表

    异常：
        404: 运行不存在或不属于该项目
    """
    await _verify_project_owner(project_id, current_user, db)

    # 验证 run 归属项目
    run_result = await db.execute(
        select(JobRun).where(
            JobRun.id == run_id,
            JobRun.project_id == project_id,
        )
    )
    if run_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运行不存在",
        )

    repo = WorkspaceRepository(db)
    files = await repo.read_all(run_id)

    return [
        {
            "file_path": f.file_path,
            "file_kind": f.file_kind,
            "version": f.version,
            "written_by_agent": f.written_by_agent,
            "updated_at": f.updated_at.isoformat(),
        }
        for f in files
    ]
