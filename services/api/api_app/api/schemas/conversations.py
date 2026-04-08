"""对话相关的请求和响应模型。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    """创建对话请求。"""

    title: str | None = None


class ConversationResponse(BaseModel):
    """对话信息响应。"""

    id: UUID
    project_id: UUID
    title: str | None
    mode: str
    status: str
    summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SaveMessageRequest(BaseModel):
    """保存消息请求。"""

    role: Literal["user", "assistant", "system"]
    content: str


class MessageResponse(BaseModel):
    """消息信息响应。"""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    content_type: str
    tool_calls: dict | None = None
    artifacts_created: list | None = None
    model: str | None = None
    provider: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    """发送消息请求（conversations 路由用，不触发 AI）。"""

    content: str
