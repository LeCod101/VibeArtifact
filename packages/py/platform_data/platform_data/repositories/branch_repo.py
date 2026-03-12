"""分支仓储 - 提供会话分支表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.conversation import ConversationBranch
from platform_data.repositories.base import BaseRepository


class BranchRepository(BaseRepository[ConversationBranch]):
    """分支仓储，继承通用 CRUD 并提供按会话查询分支列表等方法。"""

    model_class = ConversationBranch

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> list[ConversationBranch]:
        """查询指定会话下的所有分支。

        参数:
            conversation_id: 会话 UUID

        返回:
            该会话下的所有分支列表
        """
        stmt = select(ConversationBranch).where(
            ConversationBranch.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
