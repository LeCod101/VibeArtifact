"""会话模型 - 定义对话和消息两张表。"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationMode(enum.Enum):
    """对话模式枚举：chat=一问一答，delegated=全权委托。"""

    chat = "chat"
    delegated = "delegated"


class ConversationStatus(enum.Enum):
    """对话状态枚举。"""

    active = "active"
    archived = "archived"


class MessageRole(enum.Enum):
    """消息角色枚举。"""

    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """对话表，每个项目可有多个对话，支持 chat 和 delegated 两种模式。"""

    __tablename__ = "conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True,
    )
    title: Mapped[str | None] = mapped_column(String(300))
    mode: Mapped[ConversationMode] = mapped_column(
        Enum(ConversationMode, name="conversation_mode", native_enum=True),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status", native_enum=True),
        default=ConversationStatus.active,
        server_default="active",
    )


class Message(UUIDPrimaryKeyMixin, Base):
    """消息表，记录对话内容及 LLM 调用成本。"""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", native_enum=True),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(50), default="text", server_default="text",
    )
    # 工具调用记录（JSON 格式）
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    # 本轮消息产生的产物 ID 列表
    artifacts_created: Mapped[list | None] = mapped_column(JSONB)
    # LLM 调用元数据
    model: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
