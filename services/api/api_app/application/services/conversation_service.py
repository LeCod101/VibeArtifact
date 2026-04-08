"""对话服务 - 封装对话创建、查询等业务逻辑。"""

from uuid import UUID

from platform_data.models.conversation import Conversation, ConversationMode
from platform_data.repositories.conversation_repo import ConversationRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ConversationService:
    """对话业务服务层。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.conversation_repo = ConversationRepository(session)

    async def create_conversation(
        self,
        project_id: UUID,
        title: str | None = None,
        mode: ConversationMode = ConversationMode.chat,
    ) -> Conversation:
        """创建对话。

        参数:
            project_id: 所属项目的 UUID
            title: 对话标题，可选
            mode: 对话模式，默认 chat

        返回:
            新创建的 Conversation 实例
        """
        conversation = Conversation(
            project_id=project_id,
            title=title,
            mode=mode,
        )
        return await self.conversation_repo.create(conversation)

    async def list_by_project(
        self,
        project_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        """查询指定项目的对话列表。

        参数:
            project_id: 项目 UUID
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100

        返回:
            该项目下的对话列表
        """
        return await self.conversation_repo.list_by_project(
            project_id=project_id, offset=offset, limit=limit,
        )

    async def get_or_create_default(self, project_id: UUID) -> Conversation:
        """获取项目的默认对话，不存在则创建。

        参数:
            project_id: 项目 UUID

        返回:
            默认对话实例
        """
        conversations = await self.conversation_repo.list_by_project(
            project_id=project_id, offset=0, limit=1,
        )
        if conversations:
            return conversations[0]

        return await self.create_conversation(
            project_id=project_id,
            title="默认对话",
        )
