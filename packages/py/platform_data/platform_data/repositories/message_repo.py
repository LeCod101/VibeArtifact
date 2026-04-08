"""消息仓储 - 提供消息表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.conversation import Message
from platform_data.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """消息仓储，继承通用 CRUD 并提供按对话查询消息列表等方法。"""

    model_class = Message

    async def list_by_conversation(
        self, conversation_id: UUID, limit: int = 50
    ) -> list[Message]:
        """查询指定对话下的消息列表，按创建时间升序排列。

        参数:
            conversation_id: 对话 UUID
            limit: 返回的最大记录数，默认 50

        返回:
            按 created_at 升序排列的消息列表
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent(
        self, conversation_id: UUID, limit: int = 20
    ) -> list[Message]:
        """查询指定对话最近 N 条消息，按创建时间升序返回。

        先按 created_at DESC 取最近 N 条，再反转为升序以保持对话顺序。

        参数:
            conversation_id: 对话 UUID
            limit: 返回的最大记录数，默认 20

        返回:
            按 created_at 升序排列的最近消息列表
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
