"""项目服务 - 封装项目创建、查询等核心业务逻辑。

创建项目时自动初始化关联资源：空 IR 快照、默认对话和默认分支。
"""

from uuid import UUID

from platform_data.models.conversation import (
    Conversation,
    ConversationBranch,
    ConversationMode,
)
from platform_data.models.project import Project, ProjectStatus
from platform_data.repositories.branch_repo import BranchRepository
from platform_data.repositories.conversation_repo import ConversationRepository
from platform_data.repositories.project_repo import ProjectRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectService:
    """项目业务服务层，协调多个 Repository 完成项目相关操作。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化项目服务，创建所需的 Repository 实例。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.snapshot_repo = SnapshotRepository(session)
        self.conversation_repo = ConversationRepository(session)
        self.branch_repo = BranchRepository(session)

    async def create_project(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Project:
        """创建项目并自动初始化关联资源。

        流程：
        1. 创建 Project 记录
        2. 创建初始空 IRSnapshot（version=1）
        3. 创建默认 Conversation（chat 模式）
        4. 创建默认 ConversationBranch（branch_name="main"）
        5. 设置 conversation.active_branch_id

        参数:
            user_id: 创建者的用户 UUID
            name: 项目名称
            description: 项目描述，可选

        返回:
            新创建的 Project 实例
        """
        # 创建项目记录
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
        )
        project = await self.project_repo.create(project)

        # 创建初始空快照
        snapshot = await self.snapshot_repo.create_empty(
            project_id=project.id,
        )

        # 创建默认对话
        conversation = Conversation(
            project_id=project.id,
            title="默认对话",
            mode=ConversationMode.chat,
        )
        conversation = await self.conversation_repo.create(conversation)

        # 创建默认分支，绑定到初始快照
        branch = ConversationBranch(
            conversation_id=conversation.id,
            branch_name="main",
            base_snapshot_id=snapshot.id,
        )
        branch = await self.branch_repo.create(branch)

        # 设置对话的活跃分支
        conversation.active_branch_id = branch.id
        await self.session.flush()

        return project

    async def list_projects(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """查询指定用户的项目列表。

        参数:
            user_id: 用户 UUID
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100

        返回:
            该用户拥有的项目列表
        """
        return await self.project_repo.list_by_user(user_id=user_id, offset=offset, limit=limit)

    async def get_project(self, project_id: UUID) -> Project | None:
        """根据项目 ID 查询项目详情。

        参数:
            project_id: 项目 UUID

        返回:
            项目实例，不存在则返回 None
        """
        return await self.project_repo.get_by_id(project_id)

    async def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Project | None:
        """更新项目名称和描述。

        仅更新传入的非 None 字段。验证项目属于指定用户。

        参数:
            project_id: 项目 UUID
            user_id: 当前用户 UUID，用于权限校验
            name: 新的项目名称，None 表示不更新
            description: 新的项目描述，None 表示不更新

        返回:
            更新后的 Project 实例，项目不存在或不属于该用户则返回 None
        """
        project = await self.project_repo.get_by_id(project_id)
        if project is None or project.user_id != user_id:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        return await self.project_repo.update(project)

    async def delete_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> bool:
        """软删除项目（将状态设为 deleted）。

        参数:
            project_id: 项目 UUID
            user_id: 当前用户 UUID，用于权限校验

        返回:
            删除成功返回 True，项目不存在或不属于该用户返回 False
        """
        project = await self.project_repo.get_by_id(project_id)
        if project is None or project.user_id != user_id:
            return False

        project.status = ProjectStatus.deleted
        await self.project_repo.update(project)
        return True
