"""Workspace 模型 - 定义运行级工作区文件表。

workspace_files 是 Agent 产物（代码/文档/图表）的唯一持久化位置：
每个 delegated run 拥有一组以 (run_id, file_path) 唯一标识的文件，
Agent 重写同一路径时 version 递增（upsert 覆盖，不保留历史行）。
Gate 校验、修复回路、ZIP 导出均以本表为数据源。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin

# 合法的文件类别（对应旧 IR 中 code/doc/diagram 三类节点）
WORKSPACE_FILE_KINDS = ("code", "doc", "diagram")


class WorkspaceFile(UUIDPrimaryKeyMixin, Base):
    """工作区文件表，存储一次 run 产出的所有文件（最新版本）。"""

    __tablename__ = "workspace_files"
    __table_args__ = (
        UniqueConstraint("run_id", "file_path", name="uq_workspace_files_run_path"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_runs.id"), nullable=False, index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    written_by_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    written_by_turn: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )
