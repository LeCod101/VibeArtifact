"""项目模型 - 定义项目表。"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(enum.Enum):
    """项目状态枚举。"""

    active = "active"
    archived = "archived"
    deleted = "deleted"


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

    # 项目类型：homework（作业）等
    project_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="homework", server_default="homework",
    )
    # 课程名称
    course_name: Mapped[str | None] = mapped_column(String(100))
    # 技术要求说明
    tech_requirements: Mapped[str | None] = mapped_column(Text)
    # 截止日期
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 指导老师/顾问名称
    advisor_name: Mapped[str | None] = mapped_column(String(100))
