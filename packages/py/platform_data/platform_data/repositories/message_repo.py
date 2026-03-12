"""消息仓储 - 提供消息表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.conversation import Message
from platform_data.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """消息仓储，继承通用 CRUD 并提供按分支查询消息列表等方法。"""

    model_class = Message

    async def list_by_branch(
        self, branch_id: UUID, limit: int = 50
    ) -> list[Message]:
        """查询指定分支下的消息列表，按创建时间降序排列。

        参数:
            branch_id: 分支 UUID
            limit: 返回的最大记录数，默认 50

        返回:
            按 created_at 降序排列的消息列表
        """
        stmt = (
            select(Message)
            .where(Message.branch_id == branch_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
