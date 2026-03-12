"""会话仓储 - 提供对话表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.conversation import Conversation
from platform_data.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """会话仓储，继承通用 CRUD 并提供按项目查询对话列表等方法。"""

    model_class = Conversation

    async def list_by_project(
        self, project_id: UUID, offset: int = 0, limit: int = 100
    ) -> list[Conversation]:
        """查询指定项目的对话列表（分页）。

        参数:
            project_id: 项目 UUID
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100

        返回:
            该项目下的对话列表
        """
        stmt = (
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
