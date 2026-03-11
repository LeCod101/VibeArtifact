"""IR 模型 - 定义快照、节点、边、操作日志四张核心 IR 表。

IR（Intermediate Representation）是系统核心数据结构，
所有 Agent 通过 IR 间接协作（黑板模式）。
M1 阶段 props 字段为 JSONB，M2 阶段引入 typed props 校验。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin


class SnapshotStatus(enum.Enum):
    """快照状态枚举。"""

    active = "active"
    archived = "archived"


class IRSnapshot(UUIDPrimaryKeyMixin, Base):
    """IR 快照表，采用全量物理快照策略，支持树状版本链（parent_snapshot_id 自引用）。"""

    __tablename__ = "ir_snapshots"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True,
    )
    parent_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ir_snapshots.id"),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SnapshotStatus] = mapped_column(
        Enum(SnapshotStatus, name="snapshot_status", native_enum=True),
        default=SnapshotStatus.active,
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class IRNode(UUIDPrimaryKeyMixin, Base):
    """IR 节点表，存储节点类型、标签、JSONB 属性和画布坐标。"""

    __tablename__ = "ir_nodes"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_snapshots.id"), nullable=False, index=True,
    )
    node_type: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    props: Mapped[dict | None] = mapped_column(JSONB)
    position_x: Mapped[float | None] = mapped_column(Float)
    position_y: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class IREdge(UUIDPrimaryKeyMixin, Base):
    """IR 边表，描述节点间的有向连接关系。"""

    __tablename__ = "ir_edges"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_snapshots.id"), nullable=False, index=True,
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_nodes.id"), nullable=False, index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_nodes.id"), nullable=False, index=True,
    )
    edge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    props: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class IROperation(UUIDPrimaryKeyMixin, Base):
    """IR 操作日志表，记录每次对 IR 的变更操作（由 Translator 翻译生成）。"""

    __tablename__ = "ir_operations"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_snapshots.id"), nullable=False, index=True,
    )
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ir_nodes.id"),
    )
    payload: Mapped[dict | None] = mapped_column(JSONB)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
