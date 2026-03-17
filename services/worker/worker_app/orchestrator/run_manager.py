"""
DelegatedRun 管理器模块。

管理 job_runs 和 agent_runs 表的生命周期，提供状态机
（pending → running → completed / failed）和 CRUD 操作。

数据库操作使用 SQLAlchemy 2 async session。
Worker 进程独立于 API 进程，因此拥有自己的数据库会话工厂。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ──────────────────────────────────────────────
# Worker 端独立的数据库会话管理
# ──────────────────────────────────────────────

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_database_url() -> str:
    """
    获取数据库连接 URL。

    优先读取环境变量 DATABASE_URL，否则使用本地默认值。
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact",
    )


def get_worker_engine() -> AsyncEngine:
    """
    获取 Worker 端数据库引擎（单例）。

    与 API 端的 session.py 分离，Worker 进程独立管理自己的连接池。
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(_get_database_url(), echo=False)
    return _engine


def get_worker_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    获取 Worker 端异步 Session 工厂（单例）。
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_worker_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


# ──────────────────────────────────────────────
# ORM 模型（与 API 端 migration 保持一致）
# ──────────────────────────────────────────────

class Base(DeclarativeBase):
    """Worker 端 ORM 基类。仅用于映射已有数据库表，不做迁移。"""


class RunStatus(StrEnum):
    """运行状态枚举，对应数据库中的 run_status 类型。"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_ATTENTION = "needs_attention"


class JobRun(Base):
    """
    job_runs 表的 ORM 映射。

    记录一次完整的 DAG 运行，包含项目 ID、快照 ID、
    运行类型、状态和时间信息。
    """
    __tablename__ = "job_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    snapshot_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "running", "completed", "failed",
            name="run_status",
            create_type=False,
        ),
        server_default="pending",
        nullable=False,
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AgentRun(Base):
    """
    agent_runs 表的 ORM 映射。

    记录 DAG 运行中每个 agent 步骤的执行状态、
    模型信息、token 用量和成本。
    """
    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    total_cost: Mapped[float | None] = mapped_column(
        Numeric(12, 6), nullable=True,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "running", "completed", "failed",
            name="run_status",
            create_type=False,
        ),
        server_default="pending",
        nullable=False,
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ──────────────────────────────────────────────
# RunManager
# ──────────────────────────────────────────────

class RunManager:
    """
    DelegatedRun 管理器。

    负责创建和管理 job_runs / agent_runs 记录，
    实现状态机流转（pending → running → completed / failed）。
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        """
        初始化运行管理器。

        - session_factory: 异步 Session 工厂，为 None 时使用默认工厂
        """
        self._session_factory = (
            session_factory or get_worker_session_factory()
        )

    # ──────── 创建 ────────

    async def create_run(
        self,
        project_id: UUID,
        snapshot_id: UUID,
        agent_ids: list[str],
        input_payload: dict | None = None,
    ) -> UUID:
        """
        创建一条 DAG 运行记录和对应的 agent 步骤记录。

        在 job_runs 表中创建一条 job_type='delegated' 的记录，
        并为每个 agent 在 agent_runs 表中创建一条 pending 状态的记录。

        - project_id: 项目 ID
        - snapshot_id: 快照 ID
        - agent_ids: 需要执行的 agent 列表
        - input_payload: 初始输入负载（可选）
        返回新建的 job_run ID。
        """
        run_id = uuid4()
        async with self._session_factory() as session:
            async with session.begin():
                job_run = JobRun(
                    id=run_id,
                    project_id=project_id,
                    snapshot_id=snapshot_id,
                    job_type="delegated",
                    status=RunStatus.PENDING,
                    input_payload=input_payload,
                )
                session.add(job_run)

                # 为每个 agent 创建步骤记录
                for agent_id in agent_ids:
                    agent_run = AgentRun(
                        id=uuid4(),
                        job_run_id=run_id,
                        agent_name=agent_id,
                        status=RunStatus.PENDING,
                    )
                    session.add(agent_run)

        return run_id

    # ──────── 状态更新 ────────

    async def mark_run_started(self, run_id: UUID) -> None:
        """
        将 run 标记为 running。

        - run_id: job_run ID
        """
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(JobRun)
                    .where(JobRun.id == run_id)
                    .values(
                        status=RunStatus.RUNNING,
                        started_at=now,
                    )
                )

    async def update_step_status(
        self,
        run_id: UUID,
        agent_id: str,
        status: RunStatus,
        error_message: str | None = None,
        output_payload: dict | None = None,
        model: str | None = None,
        provider: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_cost: float | None = None,
        latency_ms: int | None = None,
    ) -> None:
        """
        更新某个 agent 步骤的状态。

        - run_id: 所属 job_run ID
        - agent_id: agent 名称
        - status: 目标状态
        - error_message: 失败时的错误消息
        - output_payload: agent 输出负载
        - model: 使用的模型名称
        - provider: 模型提供商
        - prompt_tokens: 输入 token 数
        - completion_tokens: 输出 token 数
        - total_cost: 本次调用总费用
        - latency_ms: 调用耗时（毫秒）
        """
        now = datetime.now(timezone.utc)
        values: dict = {"status": status}

        if status == RunStatus.RUNNING:
            values["started_at"] = now
        elif status in (RunStatus.COMPLETED, RunStatus.FAILED):
            values["completed_at"] = now

        if error_message is not None:
            values["error_message"] = error_message
        if output_payload is not None:
            values["output_payload"] = output_payload
        if model is not None:
            values["model"] = model
        if provider is not None:
            values["provider"] = provider
        if prompt_tokens is not None:
            values["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            values["completion_tokens"] = completion_tokens
        if total_cost is not None:
            values["total_cost"] = total_cost
        if latency_ms is not None:
            values["latency_ms"] = latency_ms

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(AgentRun)
                    .where(
                        AgentRun.job_run_id == run_id,
                        AgentRun.agent_name == agent_id,
                    )
                    .values(**values)
                )

    async def mark_run_completed(
        self,
        run_id: UUID,
        output_payload: dict | None = None,
    ) -> None:
        """
        将 run 标记为 completed。

        - run_id: job_run ID
        - output_payload: 整体输出负载
        """
        now = datetime.now(timezone.utc)
        values: dict = {
            "status": RunStatus.COMPLETED,
            "completed_at": now,
        }
        if output_payload is not None:
            values["output_payload"] = output_payload

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(JobRun)
                    .where(JobRun.id == run_id)
                    .values(**values)
                )

    async def mark_run_failed(
        self,
        run_id: UUID,
        error_message: str,
    ) -> None:
        """
        将 run 标记为 failed。

        - run_id: job_run ID
        - error_message: 失败原因
        """
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(JobRun)
                    .where(JobRun.id == run_id)
                    .values(
                        status=RunStatus.FAILED,
                        error_message=error_message,
                        completed_at=now,
                    )
                )

    # ──────── 查询 ────────

    async def get_run_status(self, run_id: UUID) -> dict:
        """
        获取 run 的当前状态。

        返回 job_run 的关键字段组成的字典：
        id, project_id, job_type, status, started_at, completed_at, error_message。
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(JobRun).where(JobRun.id == run_id)
            )
            job_run = result.scalar_one()
            return {
                "id": str(job_run.id),
                "project_id": str(job_run.project_id),
                "job_type": job_run.job_type,
                "status": job_run.status,
                "started_at": (
                    job_run.started_at.isoformat()
                    if job_run.started_at
                    else None
                ),
                "completed_at": (
                    job_run.completed_at.isoformat()
                    if job_run.completed_at
                    else None
                ),
                "error_message": job_run.error_message,
            }

    async def get_run_steps(self, run_id: UUID) -> list[dict]:
        """
        获取 run 下所有 agent 步骤的状态。

        返回 agent_runs 记录列表，每条包含：
        id, agent_name, status, model, started_at, completed_at, error_message。
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentRun)
                .where(AgentRun.job_run_id == run_id)
                .order_by(AgentRun.created_at)
            )
            rows = result.scalars().all()
            return [
                {
                    "id": str(row.id),
                    "agent_name": row.agent_name,
                    "status": row.status,
                    "model": row.model,
                    "started_at": (
                        row.started_at.isoformat()
                        if row.started_at
                        else None
                    ),
                    "completed_at": (
                        row.completed_at.isoformat()
                        if row.completed_at
                        else None
                    ),
                    "error_message": row.error_message,
                }
                for row in rows
            ]

    async def mark_run_needs_attention(
        self,
        run_id: UUID,
        error_message: str,
        gate_result: dict | None = None,
    ) -> None:
        """
        将 run 标记为 needs_attention 状态。

        Gate 检查失败且自动修复无效时调用，表示需要人工介入。
        将 gate_result 写入 output_payload 供前端展示。

        - run_id: job_run ID
        - error_message: 失败原因摘要
        - gate_result: Gate 检查结果字典（可选）
        """
        now = datetime.now(timezone.utc)
        values: dict = {
            "status": RunStatus.NEEDS_ATTENTION,
            "error_message": error_message,
            "completed_at": now,
        }
        if gate_result is not None:
            values["output_payload"] = {"gate_result": gate_result}

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(JobRun)
                    .where(JobRun.id == run_id)
                    .values(**values)
                )
