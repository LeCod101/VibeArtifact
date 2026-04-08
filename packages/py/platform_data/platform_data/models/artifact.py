"""产物模型 - 定义产物表和产物导出表。

产物（Artifact）是系统生成的代码文件、文档、图表等，
通过 parent_id 自引用实现版本链，支持导出为 ZIP/PDF 等格式。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ArtifactType(enum.Enum):
    """产物类型枚举。"""

    code = "code"
    document = "document"
    diagram = "diagram"
    database_schema = "database_schema"
    explanation = "explanation"


class Artifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """产物表，存储项目生成的代码、文档、图表等内容。"""

    __tablename__ = "artifacts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    # 产物类型标识
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 文件路径（可选，用于代码类产物）
    file_path: Mapped[str | None] = mapped_column(String(500))
    # 编程语言（可选，用于代码类产物）
    language: Mapped[str | None] = mapped_column(String(30))
    # 版本号，同一产物链上递增
    version_num: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
    )
    # 父版本 ID，通过自引用形成版本链
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("artifacts.id"))


class ArtifactExport(UUIDPrimaryKeyMixin, Base):
    """产物导出记录表，记录项目产物的导出历史（ZIP/PDF 等）。"""

    __tablename__ = "artifact_exports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    # 导出格式：zip / pdf 等
    export_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # 导出文件 URL
    file_url: Mapped[str | None] = mapped_column(String(1000))
    # 导出文件大小（字节）
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
