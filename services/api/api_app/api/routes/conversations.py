"""对话路由模块 - 实现对话创建、列表查询、消息发送和消息历史端点。

核心 AI 对话走 chat.py 路由，本模块仅处理基础消息存储和查询。
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.conversations import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
)
from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.message_service import MessageService
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


async def _verify_project_owner(
    project_id: UUID, current_user: User, db: AsyncSession,
) -> None:
    """验证项目属于当前用户，不属于则抛出 404。"""
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


async def _verify_conversation_access(
    conversation_id: UUID, current_user: User, db: AsyncSession,
) -> UUID:
    """验证对话存在且所属项目属于当前用户，返回 conversation 的 project_id。"""
    conv_service = ConversationService(db)
    conversation = await conv_service.conversation_repo.get_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )

    await _verify_project_owner(conversation.project_id, current_user, db)
    return conversation.project_id


# ──────────────────────────────────────
# 创建对话
# ──────────────────────────────────────

@router.post(
    "/projects/{project_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    project_id: UUID,
    body: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """为指定项目创建新对话。"""
    await _verify_project_owner(project_id, current_user, db)

    service = ConversationService(db)
    conversation = await service.create_conversation(
        project_id=project_id,
        title=body.title,
    )
    await db.commit()
    return conversation  # type: ignore[return-value]


# ──────────────────────────────────────
# 查询对话列表
# ──────────────────────────────────────

@router.get(
    "/projects/{project_id}/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    project_id: UUID,
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    """查询指定项目的对话列表。"""
    await _verify_project_owner(project_id, current_user, db)

    service = ConversationService(db)
    conversations = await service.list_by_project(
        project_id=project_id,
        offset=offset,
        limit=limit,
    )
    return conversations  # type: ignore[return-value]


# ──────────────────────────────────────
# 发送消息（基础存储，不触发 AI）
# ──────────────────────────────────────

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """保存一条消息（不触发 AI 响应，核心 AI 对话走 /chat 端点）。"""
    await _verify_conversation_access(conversation_id, current_user, db)

    msg_service = MessageService(db)
    message = await msg_service.save_message(
        conversation_id=conversation_id,
        role="user",
        content=body.content,
    )
    await db.commit()
    return message  # type: ignore[return-value]


# ──────────────────────────────────────
# 查询消息列表
# ──────────────────────────────────────

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(
    conversation_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    """查询指定对话的消息列表。"""
    await _verify_conversation_access(conversation_id, current_user, db)

    service = MessageService(db)
    messages = await service.list_by_conversation(
        conversation_id=conversation_id,
        limit=limit,
    )
    return messages  # type: ignore[return-value]
