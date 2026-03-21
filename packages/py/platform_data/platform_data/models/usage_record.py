"""
用量记录模型。

记录每次 LLM 调用的 token 用量和费用，
用于用量统计和余额监控。
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin


class UsageRecord(UUIDPrimaryKeyMixin, Base):
    """
    LLM 用量记录表。

    每次 LLM 调用后写入一条记录，包含 token 用量、费用和来源。
    """

    __tablename__ = "usage_records"

    # 所属用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 所属项目（可选）
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 提供商标识
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # 模型标识
    model: Mapped[str] = mapped_column(String(200), nullable=False)

    # 输入 token 数
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 输出 token 数
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 总费用（美元，使用 Decimal 精确计算）
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=6),
        default=Decimal("0"),
    )

    # 密钥来源: "user" 表示用户自己的 key, "platform" 表示平台 key
    key_source: Mapped[str] = mapped_column(
        String(20), default="user", server_default="user",
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
