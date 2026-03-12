"""对话相关的请求和响应模型 - 定义创建对话、消息保存等数据结构。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    """创建对话请求。

    字段：
        title: 对话标题，可选
    """

    title: str | None = None


class ConversationResponse(BaseModel):
    """对话信息响应 - 返回对话基本信息。

    字段：
        id: 对话唯一标识
        project_id: 所属项目 UUID
        title: 对话标题
        mode: 对话模式（chat / delegated）
        status: 对话状态（active / archived）
        active_branch_id: 当前活跃分支 UUID
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: UUID
    project_id: UUID
    title: str | None
    mode: str
    status: str
    active_branch_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SaveMessageRequest(BaseModel):
    """保存消息请求。

    字段：
        role: 消息角色，只接受 "user" / "assistant" / "system"
        content: 消息文本内容
    """

    role: Literal["user", "assistant", "system"]
    content: str


class MessageResponse(BaseModel):
    """消息信息响应 - 返回消息基本信息。

    字段：
        id: 消息唯一标识
        conversation_id: 所属对话 UUID
        branch_id: 所属分支 UUID
        role: 消息角色
        content: 消息文本内容
        content_type: 内容类型（默认 "text"）
        created_at: 创建时间
    """

    id: UUID
    conversation_id: UUID
    branch_id: UUID
    role: str
    content: str
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
