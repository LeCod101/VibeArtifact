"""分支仓储 - 提供会话分支表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import func, or_, select

from platform_data.models.conversation import ConversationBranch, Message
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

    async def get_ancestry(
        self, branch_id: UUID
    ) -> list[ConversationBranch]:
        """获取分支的祖先链（从当前分支到根）。

        从指定分支开始，沿 parent_branch_id 逐级向上遍历，
        直到到达根分支（parent_branch_id 为 None）。

        参数:
            branch_id: 起始分支 UUID

        返回:
            从当前分支到根分支的有序列表
        """
        ancestry: list[ConversationBranch] = []
        current_id: UUID | None = branch_id

        while current_id is not None:
            branch = await self.get_by_id(current_id)
            if branch is None:
                break
            ancestry.append(branch)
            current_id = branch.parent_branch_id

        return ancestry

    async def count_messages(self, branch_id: UUID) -> int:
        """获取分支下的消息数量。

        参数:
            branch_id: 分支 UUID

        返回:
            该分支下的消息总数
        """
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.branch_id == branch_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_branch_by_snapshot(
        self, conversation_id: UUID, snapshot_id: UUID
    ) -> ConversationBranch | None:
        """查找包含指定快照的分支。

        查找顺序：
        1. 检查分支的 head_snapshot_id 或 base_snapshot_id 是否匹配
        2. 检查消息表中 snapshot_before_id 或 snapshot_after_id 是否匹配

        参数:
            conversation_id: 会话 UUID
            snapshot_id: 目标快照 UUID

        返回:
            包含该快照的分支，未找到则返回 None
        """
        # 优先检查分支自身的 head / base snapshot
        stmt_branch = select(ConversationBranch).where(
            ConversationBranch.conversation_id == conversation_id,
            or_(
                ConversationBranch.head_snapshot_id == snapshot_id,
                ConversationBranch.base_snapshot_id == snapshot_id,
            ),
        )
        result = await self.session.execute(stmt_branch)
        branch = result.scalars().first()
        if branch is not None:
            return branch

        # 再查消息表中引用了该快照的分支
        stmt_msg = (
            select(ConversationBranch)
            .join(Message, Message.branch_id == ConversationBranch.id)
            .where(
                ConversationBranch.conversation_id == conversation_id,
                or_(
                    Message.snapshot_before_id == snapshot_id,
                    Message.snapshot_after_id == snapshot_id,
                ),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt_msg)
        return result.scalars().first()

    async def snapshot_in_branch_history(
        self, branch_id: UUID, snapshot_id: UUID
    ) -> bool:
        """检查快照是否在指定分支的消息历史中。

        通过查询该分支下 snapshot_before_id 或 snapshot_after_id
        匹配目标快照的消息来判断。

        参数:
            branch_id: 分支 UUID
            snapshot_id: 目标快照 UUID

        返回:
            True 表示快照在该分支历史中
        """
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.branch_id == branch_id,
                or_(
                    Message.snapshot_before_id == snapshot_id,
                    Message.snapshot_after_id == snapshot_id,
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
