"""项目模板模型 - 定义模板表和模板类别枚举。

预定义的 IR 快照数据，作为新项目的起点。
snapshot_data 存储完整的 IR 节点和边定义（JSON 格式）。
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TemplateCategory(str, enum.Enum):
    """模板类别枚举。"""

    saas = "saas"
    api = "api"
    landing = "landing"
    dashboard = "dashboard"
    other = "other"


class ProjectTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """项目模板表，存储预定义的 IR 快照数据供快速创建项目使用。

    字段：
        name: 模板名称
        description: 模板描述
        category: 模板类别（saas / api / landing / dashboard / other）
        snapshot_data: IR 快照数据，JSON 格式 {"nodes": [...], "edges": [...]}
        icon: 图标，支持 emoji 或图标名称
        is_public: 是否公开可见
        created_by: 创建者用户 ID（可选，预置模板无创建者）
    """

    __tablename__ = "project_templates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TemplateCategory] = mapped_column(
        Enum(TemplateCategory, name="template_category", native_enum=True),
        nullable=False,
    )
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
    )
