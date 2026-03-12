"""消息服务 - 封装消息的保存和查询业务逻辑。

M1 阶段只做简单的消息存储，M7 阶段再对接 Agent 联动。
"""

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
