"""导出路由模块 - 实现项目产物导出和下载端点。"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.artifact import ArtifactExport
from platform_data.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.artifacts import ExportRequest, ExportResponse
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exports"])


@router.post(
    "/projects/{project_id}/export",
    response_model=ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_export(
    project_id: UUID,
    body: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """触发项目产物导出。

    当前为同步创建导出记录，后续可接入 Celery 异步任务。

    参数：
        project_id: 项目 UUID
        body: 导出请求（export_type: zip / pdf）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        导出记录（202 Accepted）
    """
    # 验证项目所有权
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # 创建导出记录（文件 URL 后续由异步任务填充）
    export_record = ArtifactExport(
        project_id=project_id,
        export_type=body.export_type,
    )
    db.add(export_record)
    await db.commit()
    await db.refresh(export_record)

    # TODO: 此处应发送 Celery 任务来异步打包产物

    return export_record  # type: ignore[return-value]


@router.get(
    "/exports/{export_id}/download",
    response_model=ExportResponse,
)
async def download_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """获取导出记录（含下载地址）。

    参数：
        export_id: 导出记录 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        导出记录详情

    异常：
        404: 导出记录不存在或无权访问
    """
    result = await db.execute(
        select(ArtifactExport).where(ArtifactExport.id == export_id),
    )
    export_record = result.scalar_one_or_none()

    if export_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导出记录不存在",
        )

    # 验证项目所有权
    service = ProjectService(db)
    project = await service.get_project(export_record.project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导出记录不存在",
        )

    if export_record.file_url is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="导出正在处理中，请稍后重试",
        )

    return export_record  # type: ignore[return-value]
