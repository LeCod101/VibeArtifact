"""Chat API — 核心对话接口。

提供 SSE 流式的对话 API，集成 VibeArtifactAgent。
这是整个平台最重要的 API 端点。
"""

from __future__ import annotations

import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from platform_data.models.user import User
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.application.services.agent_service import AgentService
from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Chat 请求体。"""

    message: str
    mode: Literal["auto", "discussion", "thinking"] = "auto"
    conversation_id: UUID | None = None


@router.post("/projects/{project_id}/chat")
async def chat(
    project_id: UUID,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """发送消息给 Agent，返回 SSE 流式响应。

    参数：
        project_id: 项目 UUID（路径参数）
        body: Chat 请求体（message + mode + 可选的 conversation_id）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        StreamingResponse（text/event-stream）

    异常：
        404: 项目不存在或不属于当前用户
    """
    # 验证项目所有权
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    # 获取或创建对话
    conv_service = ConversationService(db)
    if body.conversation_id is not None:
        conversation = await conv_service.conversation_repo.get_by_id(body.conversation_id)
        if conversation is None or conversation.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
    else:
        conversation = await conv_service.get_or_create_default(project_id)
        await db.commit()

    # 调用 AgentService 处理消息
    agent_service = AgentService(db)

    return StreamingResponse(
        agent_service.process_message(
            project_id=project_id,
            conversation_id=conversation.id,
            user_message=body.message,
            user=current_user,
            mode=body.mode,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
