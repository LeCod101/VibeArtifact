"""消息服务 - 封装消息的保存和查询业务逻辑。

M1 阶段只做简单的消息存储，M7 阶段扩展支持快照和 LLM 成本字段。
"""

from decimal import Decimal
from uuid import UUID

from platform_data.models.conversation import Message, MessageRole
from platform_data.repositories.message_repo import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession


class MessageService:
    """消息业务服务层，封装 MessageRepository 的调用。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化消息服务。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.message_repo = MessageRepository(session)

    async def save_message(
        self,
        conversation_id: UUID,
        branch_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """保存一条消息记录。

        参数:
            conversation_id: 所属对话的 UUID
            branch_id: 所属分支的 UUID
            role: 消息角色（"user" / "assistant" / "system"）
            content: 消息文本内容

        返回:
            新创建的 Message 实例
        """
        # 将字符串 role 转换为枚举值
        message_role = MessageRole(role)

        message = Message(
            conversation_id=conversation_id,
            branch_id=branch_id,
            role=message_role,
            content=content,
        )
        return await self.message_repo.create(message)

    async def list_by_branch(
        self,
        branch_id: UUID,
        limit: int = 50,
    ) -> list[Message]:
        """查询指定分支下的消息列表。

        参数:
            branch_id: 分支 UUID
            limit: 返回的最大记录数，默认 50

        返回:
            按创建时间降序排列的消息列表
        """
        return await self.message_repo.list_by_branch(branch_id=branch_id, limit=limit)

    async def save_message_with_snapshot(
        self,
        conversation_id: UUID,
        branch_id: UUID,
        role: str,
        content: str,
        snapshot_before_id: UUID | None = None,
        snapshot_after_id: UUID | None = None,
        model: str | None = None,
        provider: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_cost: float | None = None,
    ) -> Message:
        """保存消息，附带快照和 LLM 成本信息。

        与 save_message 的区别：支持 snapshot 和 cost 字段，
        用于 M7 Chat API 中保存用户消息和助手回复。

        参数:
            conversation_id: 所属对话的 UUID
            branch_id: 所属分支的 UUID
            role: 消息角色（"user" / "assistant" / "system"）
            content: 消息文本内容
            snapshot_before_id: 消息执行前的快照 ID
            snapshot_after_id: 消息执行后的快照 ID
            model: LLM 模型名称
            provider: LLM 提供商
            prompt_tokens: 输入 token 数
            completion_tokens: 输出 token 数
            total_cost: 本次调用总费用

        返回:
            新创建的 Message 实例
        """
        # 将字符串 role 转换为枚举值
        message_role = MessageRole(role)

        # 将 float 类型的 cost 转为 Decimal（与模型字段类型一致）
        cost_decimal = Decimal(str(total_cost)) if total_cost is not None else None

        message = Message(
            conversation_id=conversation_id,
            branch_id=branch_id,
            role=message_role,
            content=content,
            snapshot_before_id=snapshot_before_id,
            snapshot_after_id=snapshot_after_id,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=cost_decimal,
        )
        return await self.message_repo.create(message)
