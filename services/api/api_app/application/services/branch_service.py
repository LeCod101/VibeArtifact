"""分支服务 - 封装分支创建、切换、fork、回滚、树形查询等业务逻辑。

提供会话分支的完整管理能力，包括：
- 创建子分支
- 列出会话所有分支
- 切换活跃分支
- 从快照点 fork 新分支
- 回滚到指定快照（自动 fork 或切换）
- 构建分支树形结构
"""

import logging
from uuid import UUID

from platform_data.models.conversation import Conversation, ConversationBranch
from platform_data.repositories.branch_repo import BranchRepository
from platform_data.repositories.conversation_repo import ConversationRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BranchService:
    """分支业务服务层，协调 BranchRepository 完成分支相关操作。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化分支服务。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.session = session
        self.branch_repo = BranchRepository(session)
        self.conversation_repo = ConversationRepository(session)

    async def create_branch(
        self,
        conversation_id: UUID,
        parent_branch_id: UUID,
        branch_name: str | None = None,
        base_snapshot_id: UUID | None = None,
    ) -> ConversationBranch:
        """创建子分支。

        如果未指定 branch_name，则自动生成 branch-{n} 格式的名称，
        其中 n 为当前会话已有分支数量。

        参数:
            conversation_id: 所属会话 UUID
            parent_branch_id: 父分支 UUID
            branch_name: 分支名称，可选（不传则自动生成）
            base_snapshot_id: 分支起点快照 UUID，可选

        返回:
            新创建的 ConversationBranch 实例
        """
        # 如果未指定分支名称，自动生成
        if branch_name is None:
            existing = await self.branch_repo.get_by_conversation(conversation_id)
            branch_name = f"branch-{len(existing)}"

        branch = ConversationBranch(
            conversation_id=conversation_id,
            parent_branch_id=parent_branch_id,
            branch_name=branch_name,
            base_snapshot_id=base_snapshot_id,
        )
        branch = await self.branch_repo.create(branch)
        return branch

    async def list_branches(
        self, conversation_id: UUID
    ) -> list[ConversationBranch]:
        """获取会话下所有分支。

        参数:
            conversation_id: 会话 UUID

        返回:
            该会话下的所有分支列表
        """
        return await self.branch_repo.get_by_conversation(conversation_id)

    async def get_branch(
        self, branch_id: UUID
    ) -> ConversationBranch | None:
        """获取单个分支。

        参数:
            branch_id: 分支 UUID

        返回:
            分支实例，不存在则返回 None
        """
        return await self.branch_repo.get_by_id(branch_id)

    async def switch_branch(
        self, conversation_id: UUID, branch_id: UUID
    ) -> Conversation:
        """切换会话的活跃分支。

        验证目标分支确实属于该会话后，更新 conversation.active_branch_id。

        参数:
            conversation_id: 会话 UUID
            branch_id: 目标分支 UUID

        返回:
            更新后的 Conversation 实例

        异常:
            ValueError: 会话不存在或分支不属于该会话
        """
        # 获取会话
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("会话不存在")

        # 验证分支属于该会话
        branch = await self.branch_repo.get_by_id(branch_id)
        if branch is None or branch.conversation_id != conversation_id:
            raise ValueError("分支不存在或不属于该会话")

        # 更新活跃分支
        conversation.active_branch_id = branch_id
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def fork_branch(
        self,
        conversation_id: UUID,
        source_branch_id: UUID,
        fork_point_snapshot_id: UUID,
        branch_name: str | None = None,
    ) -> ConversationBranch:
        """从某个快照点 fork 新分支。

        以 fork_point_snapshot_id 作为新分支的 base_snapshot_id 和 head_snapshot_id，
        源分支作为父分支。

        参数:
            conversation_id: 所属会话 UUID
            source_branch_id: 源分支 UUID（将作为新分支的父分支）
            fork_point_snapshot_id: fork 点的快照 UUID
            branch_name: 新分支名称，可选

        返回:
            新创建的 ConversationBranch 实例

        异常:
            ValueError: 源分支不存在或不属于该会话
        """
        # 验证源分支存在且属于该会话
        source_branch = await self.branch_repo.get_by_id(source_branch_id)
        if source_branch is None or source_branch.conversation_id != conversation_id:
            raise ValueError("源分支不存在或不属于该会话")

        # 创建新分支，base_snapshot_id 和 head_snapshot_id 都指向 fork 点
        new_branch = await self.create_branch(
            conversation_id=conversation_id,
            parent_branch_id=source_branch_id,
            branch_name=branch_name,
            base_snapshot_id=fork_point_snapshot_id,
        )

        # 设置 head_snapshot_id 为 fork 点
        new_branch.head_snapshot_id = fork_point_snapshot_id
        await self.session.flush()
        await self.session.refresh(new_branch)

        return new_branch

    async def rollback_to_snapshot(
        self, conversation_id: UUID, snapshot_id: UUID
    ) -> dict:
        """回滚到指定快照。

        三种路径：
        1. no_change: snapshot 就是当前 head
        2. forked: snapshot 在当前分支历史中，fork 新分支
        3. switched: snapshot 不在当前分支，找到包含它的分支并切换

        参数:
            conversation_id: 会话 ID
            snapshot_id: 目标快照 ID

        返回:
            {
                "action": "no_change" | "forked" | "switched",
                "switched_branch_id": UUID,
                "new_branch_id": UUID | None,
                "snapshot_id": UUID,
            }

        异常:
            ValueError: 会话不存在
            LookupError: 快照在所有分支中均未找到
        """
        # 获取会话
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError("会话不存在")

        active_branch_id = conversation.active_branch_id
        if active_branch_id is None:
            raise ValueError("会话没有活跃分支")

        # 获取当前活跃分支
        current_branch = await self.branch_repo.get_by_id(active_branch_id)
        if current_branch is None:
            raise ValueError("活跃分支不存在")

        # ── 路径 1: snapshot 就是当前 head → no_change ──
        if current_branch.head_snapshot_id == snapshot_id:
            logger.info(
                "回滚目标即当前 head，无需操作: conversation=%s, snapshot=%s",
                conversation_id,
                snapshot_id,
            )
            return {
                "action": "no_change",
                "switched_branch_id": active_branch_id,
                "new_branch_id": None,
                "snapshot_id": snapshot_id,
            }

        # ── 检查 snapshot 是否在当前分支历史中 ──
        in_current = await self.branch_repo.snapshot_in_branch_history(
            active_branch_id, snapshot_id
        )
        # 也检查 base_snapshot_id
        if not in_current and current_branch.base_snapshot_id == snapshot_id:
            in_current = True

        if in_current:
            # ── 路径 2: snapshot 在当前分支历史 → fork 新分支 ──
            new_branch = await self.fork_branch(
                conversation_id=conversation_id,
                source_branch_id=active_branch_id,
                fork_point_snapshot_id=snapshot_id,
            )

            # 自动切换活跃分支到新 fork 的分支
            await self.switch_branch(conversation_id, new_branch.id)

            logger.info(
                "从当前分支 fork 新分支: conversation=%s, old_branch=%s, "
                "new_branch=%s, snapshot=%s",
                conversation_id,
                active_branch_id,
                new_branch.id,
                snapshot_id,
            )
            return {
                "action": "forked",
                "switched_branch_id": new_branch.id,
                "new_branch_id": new_branch.id,
                "snapshot_id": snapshot_id,
            }

        # ── 路径 3: snapshot 不在当前分支 → 查找其他分支 ──
        other_branch = await self.branch_repo.find_branch_by_snapshot(
            conversation_id, snapshot_id
        )
        if other_branch is None:
            raise LookupError(
                f"快照 {snapshot_id} 在会话 {conversation_id} 的所有分支中均未找到"
            )

        # 切换到包含该快照的分支
        await self.switch_branch(conversation_id, other_branch.id)

        logger.info(
            "切换到包含目标快照的分支: conversation=%s, branch=%s, snapshot=%s",
            conversation_id,
            other_branch.id,
            snapshot_id,
        )
        return {
            "action": "switched",
            "switched_branch_id": other_branch.id,
            "new_branch_id": None,
            "snapshot_id": snapshot_id,
        }

    async def get_branch_tree(
        self, conversation_id: UUID
    ) -> list[dict]:
        """构建会话的分支树形结构。

        递归构建树，根节点是 parent_branch_id 为 None 的分支。
        每个节点包含分支信息和子分支列表。

        参数:
            conversation_id: 会话 UUID

        返回:
            树形结构列表，每个元素包含 branch 和 children 字段
        """
        branches = await self.branch_repo.get_by_conversation(conversation_id)

        # 为每个分支统计消息数
        branch_message_counts: dict[UUID, int] = {}
        for b in branches:
            count = await self.branch_repo.count_messages(b.id)
            branch_message_counts[b.id] = count

        # 按 parent_branch_id 建立索引
        children_map: dict[UUID | None, list[ConversationBranch]] = {}
        for b in branches:
            parent_id = b.parent_branch_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(b)

        def build_tree(parent_id: UUID | None) -> list[dict]:
            """递归构建分支树。

            参数:
                parent_id: 父分支 UUID，None 表示根级别

            返回:
                子树列表
            """
            nodes = []
            for b in children_map.get(parent_id, []):
                node = {
                    "branch": b,
                    "message_count": branch_message_counts.get(b.id, 0),
                    "children": build_tree(b.id),
                }
                nodes.append(node)
            return nodes

        return build_tree(None)
