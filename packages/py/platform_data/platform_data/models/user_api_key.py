"""
用户 API Key 与模型偏好模型。

- UserApiKey: 存储用户配置的第三方 LLM API 密钥（加密存储）
- UserModelPreference: 存储用户的模型偏好（推理模型/生成模型）
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    用户 API 密钥表。

    存储用户为各 LLM Provider 配置的 API Key（Fernet 加密存储）。
    每个用户每个 provider 只能有一个密钥。
    """

    __tablename__ = "user_api_keys"

    # 所属用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 提供商标识: anthropic / openai / google / azure
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # 加密后的 API 密钥
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)

    # 掩码后的密钥（存储时生成，避免每次列出都解密）
    masked_key: Mapped[str] = mapped_column(String(100), nullable=False, server_default="***")

    # 用户自定义的标签名称
    display_label: Mapped[str | None] = mapped_column(String(100))

    # 是否启用
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # 是否通过验证（None 表示尚未验证）
    is_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)

    # 上次验证时间
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )


class UserModelPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    用户模型偏好表。

    存储用户对推理模型和生成模型的选择，每个用户只有一条记录。
    """

    __tablename__ = "user_model_preferences"

    # 所属用户（一对一）
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # 推理模型标识（如 anthropic/claude-sonnet-4-20250514）
    reasoning_model: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 生成模型标识
    generation_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
