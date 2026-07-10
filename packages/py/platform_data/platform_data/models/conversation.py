"""会话模型 - 定义对话、分支、消息三张表。

会话支持树状分支（Tree Conversation），
每条消息记录 LLM 调用成本，分支支持树状回溯。
"""

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
    # 当前活跃分支 ID（不设 FK 避免与 conversation_branches 循环依赖）
    active_branch_id: Mapped[uuid.UUID | None] = mapped_column()


class ConversationBranch(UUIDPrimaryKeyMixin, Base):
    """会话分支表，支持树状分叉。"""

    __tablename__ = "conversation_branches"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True,
    )
    parent_branch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversation_branches.id"),
    )
    branch_name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )


class Message(UUIDPrimaryKeyMixin, Base):
    """消息表，记录对话内容及关联的 LLM 调用成本。"""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True,
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversation_branches.id"), nullable=False, index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", native_enum=True),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(50), default="text", server_default="text",
    )
    affected_node_ids: Mapped[list | None] = mapped_column(JSONB)
    # agent_run_id 不设 FK，消息可能在 agent_run 创建前写入
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column()
    # LLM 调用元数据
    model: Mapped[str | None] = mapped_column(String(100))
    provider: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
