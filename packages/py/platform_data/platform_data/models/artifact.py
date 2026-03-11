"""产物模型 - 定义产物表和产物版本表。

产物（Artifact）是系统生成的代码文件、文档、图表等，
每个产物可有多个版本，支持内容直存或对象存储。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ArtifactStatus(enum.Enum):
    """产物状态枚举：draft=草稿，ready=就绪，exported=已导出。"""

    draft = "draft"
    ready = "ready"
    exported = "exported"


class Artifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """产物表，绑定项目和快照，记录产物类型、路径、状态。"""

    __tablename__ = "artifacts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ir_snapshots.id"), nullable=False, index=True,
    )
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus, name="artifact_status", native_enum=True),
        default=ArtifactStatus.draft,
        server_default="draft",
    )


class ArtifactVersion(UUIDPrimaryKeyMixin, Base):
    """产物版本表，支持 content 直存文本或 storage_key 引用对象存储。"""

    __tablename__ = "artifact_versions"

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifacts.id"), nullable=False, index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
