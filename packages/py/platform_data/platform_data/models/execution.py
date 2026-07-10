"""执行与审计模型 - 定义任务运行、Agent 调用、成本账本、审计事件四张表。

job_runs 记录 Celery 任务级别的运行状态，
agent_runs 记录单次 Agent/LLM 调用的详细信息和成本，
cost_ledger 汇总所有 LLM 调用成本，
audit_events 记录系统级审计事件。
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin


class RunStatus(enum.Enum):
    """任务/Agent 运行状态枚举。"""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# 共享枚举实例，job_runs 和 agent_runs 复用同一个 PostgreSQL ENUM 类型
run_status_enum = Enum(RunStatus, name="run_status", native_enum=True)


class JobRun(UUIDPrimaryKeyMixin, Base):
    """任务运行表，对应一次 Celery 任务执行（可包含多个 agent_runs）。"""

    __tablename__ = "job_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True,
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        run_status_enum,
        default=RunStatus.pending,
        server_default="pending",
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB)
    output_payload: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class AgentRun(UUIDPrimaryKeyMixin, Base):
    """Agent 调用记录表，记录单次 LLM 调用的模型、token 用量、成本、延迟。"""

    __tablename__ = "agent_runs"

    job_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_runs.id"), nullable=False, index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[RunStatus] = mapped_column(
        run_status_enum,
        default=RunStatus.pending,
        server_default="pending",
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB)
    output_payload: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class CostLedger(UUIDPrimaryKeyMixin, Base):
    """成本账本表，汇总每次 LLM 调用的 token 用量和费用，用于成本分析和计费。"""

    __tablename__ = "cost_ledger"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True,
    )
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_runs.id"),
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    """审计事件表，记录系统级操作日志（用户操作、权限变更等）。"""

    __tablename__ = "audit_events"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"), index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
