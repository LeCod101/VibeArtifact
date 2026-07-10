"""对话路由模块 - 实现对话创建、列表查询、消息发送/查询和 SSE 事件流端点。

M7 升级：
- POST /conversations/{id}/messages 升级为完整 Chat API（调用编排器）
- 新增 GET /conversations/{id}/events SSE 端点
- 保留原有的创建对话、列表查询端点
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from platform_data.models.conversation import Conversation
from platform_data.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user, get_current_user_sse
from api_app.api.deps.db import get_db
from api_app.api.schemas.conversations import (
    ChangeSummaryResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from api_app.api.sse.publisher import get_redis
from api_app.application.services.chat_orchestrator import ChatOrchestrator
from api_app.application.services.conversation_service import ConversationService
from api_app.application.services.message_service import MessageService
from api_app.application.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


# ============================================================
# 辅助函数
# ============================================================


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


# ============================================================
# 创建对话
# ============================================================


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


# ============================================================
# 查询对话列表
# ============================================================


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


# ============================================================
# M7: 发送消息并触发 Agent 响应
# ============================================================


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
)
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """发送消息并触发 Agent 响应。

    完整对话处理流程：
    1. 验证权限（项目所有者）
    2. 获取会话和活跃分支
    3. 加载当前快照（从 branch.head_snapshot_id）
    4. 保存用户消息（snapshot_before = 当前 head_snapshot）
    5. 调用 ChatOrchestrator.handle_message()
    6. 保存助手消息（snapshot_before = 旧快照, snapshot_after = 新快照）
    7. 更新 branch.head_snapshot_id = 新快照
    8. 返回 SendMessageResponse

    参数：
        conversation_id: 对话 UUID（路径参数）
        body: 发送消息请求体（包含 content）
        current_user: 当前认证用户
        db: 异步数据库会话

    返回：
        SendMessageResponse（用户消息 + 助手回复 + 变更摘要）

    异常：
        404: 对话不存在或所属项目不属于当前用户
        400: 对话没有活跃分支
    """
    # ── 步骤 1: 验证对话存在并且所属项目属于当前用户 ──
    conversation = await _get_conversation_with_auth(
        conversation_id, current_user, db,
    )

    # ── 步骤 2: 获取活跃分支 ──
    if conversation.active_branch_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话没有活跃分支",
        )

    branch_id = conversation.active_branch_id
    conv_service = ConversationService(db)
    branch = await conv_service.get_branch(branch_id)

    if branch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分支不存在",
        )

    # ── 步骤 3: 保存用户消息 ──
    msg_service = MessageService(db)
    user_message = await msg_service.save_message_with_cost(
        conversation_id=conversation_id,
        branch_id=branch_id,
        role="user",
        content=body.content,
    )

    # ── 步骤 4: 调用 ChatOrchestrator ──
    # 获取 Redis 连接用于 SSE 事件推送
    try:
        redis = await get_redis()
    except Exception:
        # Redis 不可用时跳过 SSE
        redis = None

    orchestrator = ChatOrchestrator(db_session=db)
    result = await orchestrator.handle_message(
        project_id=conversation.project_id,
        conversation_id=conversation_id,
        branch_id=branch_id,
        user_message=body.content,
        workspace_files=[],
        redis=redis,
    )

    # ── 步骤 5: 保存助手消息 ──
    assistant_message = await msg_service.save_message_with_cost(
        conversation_id=conversation_id,
        branch_id=branch_id,
        role="assistant",
        content=result.assistant_message,
        total_cost=result.cost_total if result.cost_total > 0 else None,
    )

    # ── 步骤 6: 提交事务并返回 ──
    await db.commit()

    # 构建变更摘要响应
    change_summary = ChangeSummaryResponse(
        summary=result.change_summary.summary,
        affected_areas=result.change_summary.affected_areas,
        operations_count=result.change_summary.operations_count,
        agents_executed=result.change_summary.agents_executed,
        new_snapshot_id=None,
        warnings=result.change_summary.warnings,
    )

    return SendMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
        change_summary=change_summary,
    )


# ============================================================
# 查询消息列表（保留旧端点）
# ============================================================


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


# ============================================================
# M7: SSE 事件流端点
# ============================================================


def _format_sse(event_type: str, data: dict) -> str:
    """格式化 SSE 事件。

    参数：
        event_type: 事件类型名称
        data: 事件数据字典

    返回：
        符合 SSE 规范的事件字符串
    """
    payload = json.dumps(
        {"event": event_type, "data": data},
        ensure_ascii=False,
    )
    return f"data: {payload}\n\n"


def _format_sse_raw(raw_json: str) -> str:
    """直接将 JSON 字符串包装为 SSE 格式。

    参数：
        raw_json: 已序列化的 JSON 字符串

    返回：
        符合 SSE 规范的事件字符串
    """
    return f"data: {raw_json}\n\n"


@router.get("/conversations/{conversation_id}/events")
async def conversation_events(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_sse),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """对话模式 SSE 事件流。

    订阅 Redis pub/sub 频道 sse:chat:{conversation_id}，
    将收到的消息转为标准 SSE 格式推送给客户端。

    支持从 Authorization Header 或 URL 查询参数 ?token=xxx 认证
    （浏览器 EventSource 不支持自定义 Header）。

    终结事件（complete / failed）收到后自动关闭流。

    参数：
        conversation_id: 对话 UUID（路径参数）
        current_user: 当前认证用户（支持 Header 和 query 参数两种方式）
        db: 异步数据库会话

    返回：
        StreamingResponse（text/event-stream）

    异常：
        404: 对话不存在或所属项目不属于当前用户
    """
    # 验证对话存在并且所属项目属于当前用户
    await _get_conversation_with_auth(conversation_id, current_user, db)

    async def event_generator():
        """SSE 事件生成器。

        订阅 Redis 频道 sse:chat:{conversation_id}，
        将消息转换为 SSE 格式输出。
        遇到 complete 或 failed 事件时自动关闭流。
        """
        r = await get_redis()
        pubsub = r.pubsub()
        channel = f"sse:chat:{conversation_id}"

        try:
            await pubsub.subscribe(channel)

            # 发送连接成功事件
            yield _format_sse("connected", {
                "conversation_id": str(conversation_id),
            })

            while True:
                # 非阻塞获取消息，超时 1 秒
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is not None and message["type"] == "message":
                    data = message["data"]
                    # data 已经是 JSON 字符串（decode_responses=True）
                    yield _format_sse_raw(data)

                    # 检查是否是终结事件
                    try:
                        parsed = json.loads(data)
                        event_type = parsed.get("event", "")
                        if event_type in ("complete", "failed"):
                            break
                    except (json.JSONDecodeError, TypeError):
                        pass
                else:
                    # 超时未收到消息时发送心跳保持连接
                    yield ": heartbeat\n\n"

                # 允许事件循环处理其他协程
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            # 客户端断开连接
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
