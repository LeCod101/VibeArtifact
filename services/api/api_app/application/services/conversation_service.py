"""对话服务 - 封装对话创建、查询等业务逻辑。

创建对话时自动创建默认分支并设置为活跃分支。
"""

from uuid import UUID

from ir_core.schema.data import IREdgeData, IRNodeData
from platform_data.models.conversation import (
    Conversation,
    ConversationBranch,
    ConversationMode,
)
from platform_data.repositories.branch_repo import BranchRepository
from platform_data.repositories.conversation_repo import ConversationRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ConversationService:
    """对话业务服务层，协调 ConversationRepository 完成对话相关操作。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化对话服务。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.branch_repo = BranchRepository(session)
        self.snapshot_repo = SnapshotRepository(session)

    async def create_conversation(
        self,
        project_id: UUID,
        title: str | None = None,
        base_snapshot_id: UUID | None = None,
    ) -> Conversation:
        """创建对话并自动初始化默认分支。

        流程：
        1. 创建 Conversation 记录（chat 模式）
        2. 创建默认 ConversationBranch（branch_name="main"）
        3. 设置 conversation.active_branch_id = branch.id

        参数:
            project_id: 所属项目的 UUID
            title: 对话标题，可选
            base_snapshot_id: 分支绑定的基线快照 ID，可选

        返回:
            新创建的 Conversation 实例（已关联活跃分支）
        """
        # 创建对话记录
        conversation = Conversation(
            project_id=project_id,
            title=title,
            mode=ConversationMode.chat,
        )
        conversation = await self.conversation_repo.create(conversation)

        # 创建默认分支
        branch = ConversationBranch(
            conversation_id=conversation.id,
            branch_name="main",
            base_snapshot_id=base_snapshot_id,
        )
        branch = await self.branch_repo.create(branch)

        # 设置对话的活跃分支
        conversation.active_branch_id = branch.id
        await self.session.flush()
        await self.session.refresh(conversation)

        return conversation

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
        return await self.conversation_repo.list_by_project(project_id=project_id, offset=offset, limit=limit)

    async def get_branch_with_snapshot(
        self, branch_id: UUID
    ) -> ConversationBranch:
        """获取分支信息（含 head_snapshot_id）。

        参数:
            branch_id: 分支 UUID

        返回:
            ConversationBranch 实例

        异常:
            如果分支不存在，返回 None（由调用方处理）
        """
        return await self.branch_repo.get_by_id(branch_id)

    async def update_branch_head(
        self, branch_id: UUID, new_snapshot_id: UUID
    ) -> None:
        """更新分支的 head_snapshot_id。

        参数:
            branch_id: 分支 UUID
            new_snapshot_id: 新的快照 UUID
        """
        branch = await self.branch_repo.get_by_id(branch_id)
        if branch is not None:
            branch.head_snapshot_id = new_snapshot_id
            await self.session.flush()

    async def get_current_snapshot(
        self, branch_id: UUID
    ) -> tuple[UUID | None, list[IRNodeData], list[IREdgeData]]:
        """获取分支当前快照 ID 及其 IR 节点/边。

        流程：
        1. 获取 branch.head_snapshot_id
        2. 如果有，用 SnapshotRepository.load_snapshot_graph() 加载节点和边
        3. 将 ORM 对象转为 ir_core 的 IRNodeData/IREdgeData 格式

        参数:
            branch_id: 分支 UUID

        返回:
            (snapshot_id, ir_nodes_data, ir_edges_data)
            如果分支没有 head_snapshot_id，返回 (None, [], [])
        """
        branch = await self.branch_repo.get_by_id(branch_id)
        if branch is None or branch.head_snapshot_id is None:
            return None, [], []

        snapshot_id = branch.head_snapshot_id

        # 从数据库加载快照图的 ORM 对象
        orm_nodes, orm_edges = await self.snapshot_repo.load_snapshot_graph(
            snapshot_id
        )

        # 将 ORM 对象转换为 DTO
        ir_nodes = [
            IRNodeData(
                id=node.id,
                node_type=node.node_type,
                label=node.label,
                props=node.props or {},
                position_x=node.position_x,
                position_y=node.position_y,
            )
            for node in orm_nodes
        ]

        ir_edges = [
            IREdgeData(
                id=edge.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                edge_type=edge.edge_type,
                props=edge.props,
            )
            for edge in orm_edges
        ]

        return snapshot_id, ir_nodes, ir_edges
