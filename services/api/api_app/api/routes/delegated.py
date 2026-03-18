"""全权委托运行路由 - 创建、查询 delegated-run 和 SSE 事件流。

提供以下端点：
- POST   /delegated-runs          创建全权委托运行
- GET    /delegated-runs/{run_id} 查询运行状态
- GET    /delegated-runs/{run_id}/events   SSE 事件流
- GET    /delegated-runs/{run_id}/download ZIP 下载
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from platform_data.models.execution import AgentRun, JobRun, RunStatus
from platform_data.models.user import User
from platform_data.repositories.snapshot_repo import SnapshotRepository
from runtime_tools.exporters.storage import get_zip_path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user, get_current_user_sse
from api_app.api.deps.db import get_db
from api_app.api.schemas.delegated import (
    CreateDelegatedRunRequest,
    CreateDelegatedRunResponse,
    DelegatedRunResponse,
    DelegatedStepResponse,
)
from api_app.api.sse.publisher import get_redis
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects/{project_id}/delegated-runs",
    tags=["delegated-runs"],
)


# ============================================================
# 辅助函数
# ============================================================


async def _get_user_project(
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


async def _get_job_run(
    run_id: UUID,
    project_id: UUID,
    db: AsyncSession,
) -> JobRun:
    """获取指定 run，确认它属于指定项目。

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


def _calc_duration_ms(
    started_at,
    completed_at,
) -> int | None:
    """计算持续时间（毫秒）。

    参数：
        started_at: 开始时间（datetime 或 None）
        completed_at: 结束时间（datetime 或 None）

    返回：
        持续毫秒数，任一参数为 None 则返回 None
    """
    if started_at is None or completed_at is None:
        return None
    delta = completed_at - started_at
    return int(delta.total_seconds() * 1000)


# ============================================================
# 8.3 创建全权委托运行
# ============================================================


@router.get("", response_model=list[DelegatedRunResponse])
async def list_delegated_runs(
    project_id: UUID,
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DelegatedRunResponse]:
    """列出项目的全部委托运行记录，按创建时间倒序排列。

    参数：
        project_id: 项目 UUID
        offset: 分页偏移量，默认 0
        limit: 每页数量，默认 50
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        DelegatedRunResponse 列表
    """
    await _get_user_project(project_id, current_user, db)

    result = await db.execute(
        select(JobRun)
        .where(JobRun.project_id == project_id)
        .order_by(JobRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    job_runs = result.scalars().all()

    responses = []
    for job_run in job_runs:
        run_status = (
            job_run.status.value
            if hasattr(job_run.status, "value")
            else str(job_run.status)
        )
        responses.append(
            DelegatedRunResponse(
                run_id=str(job_run.id),
                status=run_status,
                steps=[],
                created_at=(
                    job_run.created_at.isoformat()
                    if job_run.created_at
                    else None
                ),
                completed_at=(
                    job_run.completed_at.isoformat()
                    if job_run.completed_at
                    else None
                ),
                error_message=job_run.error_message,
            )
        )

    return responses


# ============================================================
# 8.3b 创建全权委托运行
# ============================================================


@router.post("", response_model=CreateDelegatedRunResponse)
async def create_delegated_run(
    project_id: UUID,
    body: CreateDelegatedRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateDelegatedRunResponse:
    """创建全权委托运行。

    前置校验：
    1. 项目存在且属于当前用户
    2. 同项目无正在进行的 run（status=running 或 pending）
    3. 获取快照（传入 snapshot_id 或使用最新快照）

    校验通过后创建 job_run 并触发 Celery DAG 编排任务。

    参数：
        project_id: 项目 UUID
        body: 请求体（可选 snapshot_id）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        CreateDelegatedRunResponse（run_id + status）

    异常：
        409: 同项目已有进行中的运行
        422: 快照不存在
    """
    # 步骤 1：验证项目归属
    await _get_user_project(project_id, current_user, db)

    # 步骤 2：检查并发冲突 - 同项目不能有 running 或 pending 的 run
    conflict_result = await db.execute(
        select(JobRun).where(
            JobRun.project_id == project_id,
            JobRun.status.in_([
                RunStatus.running,
                RunStatus.pending,
            ]),
        )
    )
    if conflict_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该项目已有进行中的运行，请等待完成后再试",
        )

    # 步骤 3：获取快照
    snapshot_repo = SnapshotRepository(db)
    if body.snapshot_id is not None:
        snapshot = await snapshot_repo.get_by_id(UUID(body.snapshot_id))
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="指定的快照不存在",
            )
        snapshot_id = snapshot.id
    else:
        # 使用最新活跃快照
        snapshot = await snapshot_repo.get_active(project_id)
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="项目没有可用的快照",
            )
        snapshot_id = snapshot.id

    # 步骤 4：创建 job_run 记录
    import uuid as uuid_mod

    run_id = uuid_mod.uuid4()
    job_run = JobRun(
        id=run_id,
        project_id=project_id,
        snapshot_id=snapshot_id,
        job_type="delegated",
        status=RunStatus.pending,
    )
    db.add(job_run)
    await db.commit()

    # 步骤 5：触发 Celery 编排任务
    try:
        from worker_app.tasks.orchestrate import run_delegated_dag

        run_delegated_dag.delay(
            run_id=str(run_id),
            project_id=str(project_id),
            snapshot_id=str(snapshot_id),
            scope_draft_json="{}",
        )
    except Exception as exc:
        # Celery 不可用时记录日志但不阻塞 API 响应
        # 前端可通过 SSE/轮询发现 run 一直停在 pending
        logger.warning("触发 Celery 任务失败: %s", exc)

    return CreateDelegatedRunResponse(
        run_id=str(run_id),
        status="pending",
    )


# ============================================================
# 8.4 查询全权委托运行状态
# ============================================================


@router.get("/{run_id}", response_model=DelegatedRunResponse)
async def get_delegated_run(
    project_id: UUID,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DelegatedRunResponse:
    """查询全权委托运行的状态和各步骤信息。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        DelegatedRunResponse（run 状态 + steps 列表）
    """
    await _get_user_project(project_id, current_user, db)
    job_run = await _get_job_run(run_id, project_id, db)

    # 查询该 run 下的所有 agent 步骤
    steps_result = await db.execute(
        select(AgentRun)
        .where(AgentRun.job_run_id == run_id)
        .order_by(AgentRun.created_at)
    )
    steps = steps_result.scalars().all()

    step_responses = [
        DelegatedStepResponse(
            agent_id=step.agent_name,
            status=step.status.value if hasattr(step.status, "value") else str(step.status),
            started_at=(
                step.started_at.isoformat() if step.started_at else None
            ),
            completed_at=(
                step.completed_at.isoformat() if step.completed_at else None
            ),
            duration_ms=_calc_duration_ms(
                step.started_at, step.completed_at
            ),
        )
        for step in steps
    ]

    # 获取 run 状态字符串
    run_status = (
        job_run.status.value
        if hasattr(job_run.status, "value")
        else str(job_run.status)
    )

    return DelegatedRunResponse(
        run_id=str(job_run.id),
        status=run_status,
        steps=step_responses,
        created_at=(
            job_run.created_at.isoformat() if job_run.created_at else None
        ),
        completed_at=(
            job_run.completed_at.isoformat()
            if job_run.completed_at
            else None
        ),
        error_message=job_run.error_message,
    )


# ============================================================
# 8.2 SSE 事件流端点
# ============================================================


@router.get("/{run_id}/events")
async def stream_run_events(
    project_id: UUID,
    run_id: UUID,
    current_user: User = Depends(get_current_user_sse),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE 事件流 - 实时推送 run 进度到前端。

    使用 get_current_user_sse 依赖，支持从 Authorization Header
    或 URL 查询参数 ?token=xxx 读取认证 token。
    浏览器 EventSource 不支持自定义 Header，需要 query 参数回退。

    订阅 Redis pub/sub 频道 sse:{run_id}，
    将收到的消息转为标准 SSE 格式推送给客户端。
    客户端断开时自动取消 Redis 订阅。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        current_user: 当前认证用户（支持 Header 和 query 参数两种方式）
        db: 异步数据库会话

    返回：
        StreamingResponse（text/event-stream）
    """
    # 先验证权限
    await _get_user_project(project_id, current_user, db)
    await _get_job_run(run_id, project_id, db)

    async def event_generator():
        """SSE 事件生成器。

        订阅 Redis 频道，将消息转换为 SSE 格式输出。
        遇到 run_complete 或 run_failed 事件时自动关闭流。
        """
        r = await get_redis()
        pubsub = r.pubsub()
        channel = f"sse:{run_id}"

        try:
            await pubsub.subscribe(channel)

            # 先发送一个连接成功事件
            yield _format_sse("connected", {"run_id": str(run_id)})

            while True:
                # 非阻塞获取消息，超时 1 秒
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is not None and message["type"] == "message":
                    data = message["data"]
                    # data 已经是 JSON 字符串（decode_responses=True）
                    yield _format_sse_raw(data)

                    # 检查是否是终结事件
                    try:
                        parsed = json.loads(data)
                        event_type = parsed.get("event", "")
                        if event_type in ("run_complete", "run_failed"):
                            break
                    except (json.JSONDecodeError, TypeError):
                        pass
                else:
                    # 超时未收到消息时发送心跳保持连接
                    yield ": heartbeat\n\n"

                # 允许事件循环处理其他协程
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            # 客户端断开连接
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event_type: str, data: dict) -> str:
    """格式化 SSE 事件。

    参数：
        event_type: 事件类型名称
        data: 事件数据字典

    返回：
        符合 SSE 规范的事件字符串
    """
    payload = json.dumps(
        {"event": event_type, "data": data},
        ensure_ascii=False,
    )
    return f"data: {payload}\n\n"


def _format_sse_raw(raw_json: str) -> str:
    """直接将 JSON 字符串包装为 SSE 格式。

    参数：
        raw_json: 已序列化的 JSON 字符串

    返回：
        符合 SSE 规范的事件字符串
    """
    return f"data: {raw_json}\n\n"


# ============================================================
# 8.5 ZIP 下载端点
# ============================================================


@router.get("/{run_id}/download")
async def download_run_zip(
    project_id: UUID,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """下载已完成 run 的 ZIP 产物。

    检查 run 状态为 completed 后，从本地存储获取 ZIP 文件并返回。

    参数：
        project_id: 项目 UUID
        run_id: 运行 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        FileResponse（application/zip）

    异常：
        404: run 未完成或 ZIP 文件不存在
    """
    await _get_user_project(project_id, current_user, db)
    job_run = await _get_job_run(run_id, project_id, db)

    # 检查 run 是否已完成
    run_status = (
        job_run.status.value
        if hasattr(job_run.status, "value")
        else str(job_run.status)
    )
    if run_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运行尚未完成，无法下载产物",
        )

    # 获取 ZIP 文件路径
    zip_path = get_zip_path(str(run_id))
    if zip_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZIP 产物文件不存在",
        )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"delegated-run-{run_id}.zip",
    )
