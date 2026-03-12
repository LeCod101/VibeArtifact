"""对话路由模块 - 实现对话创建、列表查询和消息保存、查询端点。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from platform_data.models.conversation import Conversation
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.conversations import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SaveMessageRequest,
)
from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.message_service import MessageService
from api_app.application.services.project_service import ProjectService

router = APIRouter(tags=["conversations"])


async def _verify_project_owner(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """验证项目属于当前用户，不属于则抛出 404。

    参数：
        project_id: 项目 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    异常：
        HTTPException 404: 项目不存在或不属于当前用户
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )


async def _get_conversation_with_auth(
    conversation_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Conversation:
    """获取对话并验证所属项目属于当前用户。

    参数：
        conversation_id: 对话 UUID
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        验证通过的 Conversation 实例

    异常：
        HTTPException 404: 对话不存在或所属项目不属于当前用户
    """
    from platform_data.repositories.conversation_repo import ConversationRepository

    conversation_repo = ConversationRepository(db)
    conversation = await conversation_repo.get_by_id(conversation_id)

    # 对话不存在
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )

    # 验证对话所属项目属于当前用户
    await _verify_project_owner(conversation.project_id, current_user, db)

    return conversation


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
    """为指定项目创建新对话。

    自动创建默认分支（branch_name="main"）并设为活跃分支。

    参数：
        project_id: 项目 UUID（路径参数）
        body: 创建对话请求体（包含 title）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        ConversationResponse（新创建的对话信息）

    异常：
        404: 项目不存在或不属于当前用户
    """
    # 验证项目属于当前用户
    await _verify_project_owner(project_id, current_user, db)

    service = ConversationService(db)
    conversation = await service.create_conversation(
        project_id=project_id,
        title=body.title,
    )
    await db.commit()
    return conversation


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
    """查询指定项目的对话列表。

    参数：
        project_id: 项目 UUID（路径参数）
        offset: 跳过的记录数，默认 0
        limit: 返回的最大记录数，默认 100
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        该项目下的对话列表

    异常：
        404: 项目不存在或不属于当前用户
    """
    # 验证项目属于当前用户
    await _verify_project_owner(project_id, current_user, db)

    service = ConversationService(db)
    conversations = await service.list_by_project(
        project_id=project_id,
        offset=offset,
        limit=limit,
    )
    return conversations


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_message(
    conversation_id: UUID,
    body: SaveMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """保存一条消息到指定对话的活跃分支。

    参数：
        conversation_id: 对话 UUID（路径参数）
        body: 保存消息请求体（包含 role、content）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        MessageResponse（新保存的消息信息）

    异常：
        404: 对话不存在或所属项目不属于当前用户
        400: 对话没有活跃分支
    """
    # 验证对话存在并且所属项目属于当前用户
    conversation = await _get_conversation_with_auth(conversation_id, current_user, db)

    # 获取活跃分支 ID
    if conversation.active_branch_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话没有活跃分支",
        )

    service = MessageService(db)
    message = await service.save_message(
        conversation_id=conversation_id,
        branch_id=conversation.active_branch_id,
        role=body.role,
        content=body.content,
    )
    await db.commit()
    return message


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
    """查询指定对话活跃分支下的消息列表。

    参数：
        conversation_id: 对话 UUID（路径参数）
        limit: 返回的最大记录数，默认 50
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        按创建时间降序排列的消息列表

    异常：
        404: 对话不存在或所属项目不属于当前用户
        400: 对话没有活跃分支
    """
    # 验证对话存在并且所属项目属于当前用户
    conversation = await _get_conversation_with_auth(conversation_id, current_user, db)

    # 获取活跃分支 ID
    if conversation.active_branch_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话没有活跃分支",
        )

    service = MessageService(db)
    messages = await service.list_by_branch(
        branch_id=conversation.active_branch_id,
        limit=limit,
    )
    return messages
