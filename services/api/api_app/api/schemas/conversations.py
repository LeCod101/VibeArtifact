"""对话相关的请求和响应模型 - 定义创建对话、消息保存等数据结构。

包含：
- 创建对话请求/响应
- 保存消息请求/响应
- 发送消息请求/响应（M7 Chat API 升级）
- 变更摘要响应
"""

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


# ──────────────────────────────────────────────
# M7 Chat API 升级新增 schema
# ──────────────────────────────────────────────


class SendMessageRequest(BaseModel):
    """发送消息请求 — 用户在对话中发送一条消息。

    字段：
        content: 用户输入的消息文本
    """

    content: str


class ChangeSummaryResponse(BaseModel):
    """变更摘要响应 — 描述本次编排产生的变更。

    字段：
        summary: 变更摘要文本
        affected_areas: 受影响的模块/领域列表
        operations_count: IR 操作总数
        agents_executed: 实际执行的 Agent 列表
        new_snapshot_id: 新快照 ID（Phase 1 可能为空）
        warnings: 警告信息列表
    """

    summary: str
    affected_areas: list[str]
    operations_count: int
    agents_executed: list[str]
    new_snapshot_id: str | None = None
    warnings: list[str] = []


class SendMessageResponse(BaseModel):
    """发送消息响应 — 包含用户消息、助手回复和变更摘要。

    字段：
        user_message: 用户消息记录
        assistant_message: 助手回复消息记录
        change_summary: 本次编排的变更摘要
    """

    user_message: MessageResponse
    assistant_message: MessageResponse
    change_summary: ChangeSummaryResponse

    model_config = {"from_attributes": True}
