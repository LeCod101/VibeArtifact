"""消息服务 - 封装消息的保存和查询业务逻辑。"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from platform_data.models.conversation import Message, MessageRole
from platform_data.repositories.message_repo import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession


class MessageService:
    """消息业务服务层。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.message_repo = MessageRepository(session)

    async def save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """保存一条消息记录。

        参数:
            conversation_id: 所属对话的 UUID
            role: 消息角色（"user" / "assistant" / "system"）
            content: 消息文本内容

        返回:
            新创建的 Message 实例
        """
        message = Message(
            conversation_id=conversation_id,
            role=MessageRole(role),
            content=content,
        )
        return await self.message_repo.create(message)

    async def save_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        tool_calls: dict[str, Any] | None = None,
        artifacts_created: list[str] | None = None,
        model: str | None = None,
        provider: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_cost: float | None = None,
    ) -> Message:
        """保存助手消息，附带工具调用和 LLM 成本信息。

        参数:
            conversation_id: 所属对话的 UUID
            content: 消息文本内容
            tool_calls: 工具调用记录
            artifacts_created: 本轮产生的产物 ID 列表
            model: LLM 模型名称
            provider: LLM 提供商
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            total_cost: 本次调用总费用

        返回:
            新创建的 Message 实例
        """
        cost_decimal = Decimal(str(total_cost)) if total_cost is not None else None

        message = Message(
            conversation_id=conversation_id,
            role=MessageRole.assistant,
            content=content,
            tool_calls=tool_calls,
            artifacts_created=artifacts_created,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=cost_decimal,
        )
        return await self.message_repo.create(message)

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> list[Message]:
        """查询指定对话的消息列表（按时间升序）。

        参数:
            conversation_id: 对话 UUID
            limit: 返回的最大记录数，默认 50

        返回:
            按创建时间升序排列的消息列表
        """
        return await self.message_repo.list_by_conversation(
            conversation_id=conversation_id, limit=limit,
        )

    async def list_recent(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> list[Message]:
        """查询指定对话最近 N 条消息（按时间升序）。

        参数:
            conversation_id: 对话 UUID
            limit: 返回的最大记录数，默认 20

        返回:
            按创建时间升序排列的最近消息列表
        """
        return await self.message_repo.list_recent(
            conversation_id=conversation_id, limit=limit,
        )
