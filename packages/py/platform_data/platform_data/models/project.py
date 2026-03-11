"""项目模型 - 定义项目表和项目配置表。"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(enum.Enum):
    """项目状态枚举。"""

    active = "active"
    archived = "archived"


class ModelTier(enum.Enum):
    """模型质量等级枚举，控制 LLM 调用的模型选择。"""

    standard = "standard"
    high_quality = "high_quality"


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """项目表，每个用户可创建多个项目。"""

    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=True),
        default=ProjectStatus.active,
        server_default="active",
    )


class ProjectConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """项目配置表，一对一绑定项目，存储生成栈和模型等级等配置。"""

    __tablename__ = "project_configs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), unique=True, nullable=False,
    )
    generation_stack: Mapped[str] = mapped_column(
        String(100), default="nextjs-fastapi", server_default="nextjs-fastapi",
    )
    model_tier: Mapped[ModelTier] = mapped_column(
        Enum(ModelTier, name="model_tier", native_enum=True),
        default=ModelTier.standard,
        server_default="standard",
    )
