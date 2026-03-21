"""审批路由 - 获取待审批项、批准、拒绝、调整委托运行。

提供以下端点：
- GET    /delegated-runs/{run_id}/approvals  获取待审批项
- POST   /delegated-runs/{run_id}/approve    批准继续
- POST   /delegated-runs/{run_id}/reject     拒绝终止
- POST   /delegated-runs/{run_id}/adjust     调整反馈
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.execution import JobRun
from platform_data.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.approvals import (
    AdjustRequest,
    ApprovalActionResponse,
    ApprovalItemResponse,
    ApproveRequest,
    RejectRequest,
)
from api_app.application.services.approval_service import ApprovalService
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects/{project_id}/delegated-runs/{run_id}",
    tags=["approvals"],
)


# ============================================================
# 辅助函数
# ============================================================


async def _validate_project_owner(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """验证项目属于当前用户，不属于则抛出 404。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    异常：
        HTTPException 404: 项目不存在或不属于当前用户
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)

    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


async def _validate_run_belongs_to_project(
    run_id: UUID,
    project_id: UUID,
    db: AsyncSession,
) -> JobRun:
    """验证 run 属于指定项目。

    参数：
        run_id: 运行 UUID
        project_id: 项目 UUID
        db: 异步数据库会话

    返回：
        JobRun ORM 对象

    异常：
        HTTPException 404: run 不存在或不属于该项目
    """
    result = await db.execute(
        select(JobRun).where(
            JobRun.id == run_id,
            JobRun.project_id == project_id,
        )
    )
    job_run = result.scalar_one_or_none()
    if job_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运行记录不存在",
        )
    return job_run


# ============================================================
# 获取待审批项
# ============================================================


@router.get("/approvals", response_model=ApprovalItemResponse)
async def get_pending_approvals(
    project_id: UUID,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalItemResponse:
    """获取运行的待审批项汇总。

    包含高风险节点、待决策节点和审批历史记录。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ApprovalItemResponse 审批项汇总
    """
    await _validate_project_owner(project_id, current_user, db)
    await _validate_run_belongs_to_project(run_id, project_id, db)

    service = ApprovalService(db)
    result = await service.get_pending_approvals(run_id)

    return ApprovalItemResponse(**result)


# ============================================================
# 批准运行
# ============================================================


@router.post("/approve", response_model=ApprovalActionResponse)
async def approve_run(
    project_id: UUID,
    run_id: UUID,
    body: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalActionResponse:
    """批准运行继续执行。

    仅在 run 状态为 waiting_approval 时可操作。
    批准后 IR 中的高风险和待决策节点状态变为 accepted，
    run 状态变为 completed。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        body: 批准请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ApprovalActionResponse 操作结果

    异常：
        400: run 状态不是 waiting_approval
    """
    await _validate_project_owner(project_id, current_user, db)
    await _validate_run_belongs_to_project(run_id, project_id, db)

    service = ApprovalService(db)
    try:
        result = await service.approve_run(
            run_id=run_id,
            user_id=current_user.id,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ApprovalActionResponse(**result)


# ============================================================
# 拒绝运行
# ============================================================


@router.post("/reject", response_model=ApprovalActionResponse)
async def reject_run(
    project_id: UUID,
    run_id: UUID,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalActionResponse:
    """拒绝运行，将其终止。

    仅在 run 状态为 waiting_approval 时可操作。
    拒绝后 run 状态变为 failed。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        body: 拒绝请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ApprovalActionResponse 操作结果

    异常：
        400: run 状态不是 waiting_approval
    """
    await _validate_project_owner(project_id, current_user, db)
    await _validate_run_belongs_to_project(run_id, project_id, db)

    service = ApprovalService(db)
    try:
        result = await service.reject_run(
            run_id=run_id,
            user_id=current_user.id,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ApprovalActionResponse(**result)


# ============================================================
# 调整运行
# ============================================================


@router.post("/adjust", response_model=ApprovalActionResponse)
async def adjust_run(
    project_id: UUID,
    run_id: UUID,
    body: AdjustRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalActionResponse:
    """调整运行，附带反馈让用户在对话中继续迭代。

    仅在 run 状态为 waiting_approval 时可操作。
    调整后 run 状态变为 needs_attention。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        body: 调整请求体
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ApprovalActionResponse 操作结果

    异常：
        400: run 状态不是 waiting_approval
    """
    await _validate_project_owner(project_id, current_user, db)
    await _validate_run_belongs_to_project(run_id, project_id, db)

    service = ApprovalService(db)
    try:
        result = await service.adjust_run(
            run_id=run_id,
            user_id=current_user.id,
            feedback=body.feedback,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ApprovalActionResponse(**result)
