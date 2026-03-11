"""用户模型 - 定义用户账户表。"""

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserStatus(enum.Enum):
    """用户状态枚举。"""

    active = "active"
    disabled = "disabled"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """用户账户表，存储邮箱、密码哈希、显示名称等基本信息。"""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True),
        default=UserStatus.active,
        server_default="active",
    )
