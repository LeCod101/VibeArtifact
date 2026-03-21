"""模板服务 - 封装模板查询和从模板创建项目的业务逻辑。

从模板创建项目时，自动初始化 IR 快照、节点、边、对话和分支。
"""

from uuid import UUID

from platform_data.models.conversation import (
    Conversation,
    ConversationBranch,
    ConversationMode,
)
from platform_data.models.ir import IREdge, IRNode, IRSnapshot, SnapshotStatus
from platform_data.models.project import Project
from platform_data.models.template import ProjectTemplate, TemplateCategory
from platform_data.repositories.branch_repo import BranchRepository
from platform_data.repositories.conversation_repo import ConversationRepository
from platform_data.repositories.project_repo import ProjectRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository
from platform_data.repositories.template_repo import TemplateRepository
from platform_data.seed.templates import PRESET_TEMPLATES
from sqlalchemy.ext.asyncio import AsyncSession


class TemplateService:
    """模板业务服务层，提供模板查询和从模板创建项目的功能。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化模板服务，创建所需的 Repository 实例。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.session = session
        self.template_repo = TemplateRepository(session)
        self.project_repo = ProjectRepository(session)
        self.snapshot_repo = SnapshotRepository(session)
        self.conversation_repo = ConversationRepository(session)
        self.branch_repo = BranchRepository(session)

    async def ensure_preset_templates(self) -> None:
        """确保预置模板已加载到数据库。

        如果模板表为空，则从 seed 数据中加载预置模板。
        使用幂等策略：仅在表为空时插入。
        """
        count = await self.template_repo.count()
        if count > 0:
            return

        for tpl_data in PRESET_TEMPLATES:
            template = ProjectTemplate(
                name=tpl_data["name"],
                description=tpl_data["description"],
                category=TemplateCategory(tpl_data["category"]),
                snapshot_data=tpl_data["snapshot_data"],
                icon=tpl_data.get("icon"),
                is_public=True,
            )
            await self.template_repo.create(template)

    async def list_templates(
        self, category: str | None = None
    ) -> list[ProjectTemplate]:
        """查询公开模板列表。

        首次调用时自动加载预置模板（如果表为空）。

        参数:
            category: 模板类别，可选

        返回:
            公开模板列表
        """
        await self.ensure_preset_templates()
        return await self.template_repo.list_public(category=category)

    async def get_template(self, template_id: UUID) -> ProjectTemplate | None:
        """获取模板详情。

        参数:
            template_id: 模板 UUID

        返回:
            模板实例，不存在则返回 None
        """
        await self.ensure_preset_templates()
        return await self.template_repo.get_by_id(template_id)

    async def create_project_from_template(
        self,
        user_id: UUID,
        project_name: str,
        template_id: UUID,
    ) -> tuple[Project, IRSnapshot]:
        """从模板创建项目。

        流程：
        1. 获取模板
        2. 创建项目
        3. 创建 IRSnapshot
        4. 从 template.snapshot_data 创建 IRNode 和 IREdge
        5. 创建默认会话和分支
        6. 返回 (project, snapshot)

        参数:
            user_id: 创建者用户 UUID
            project_name: 新项目名称
            template_id: 模板 UUID

        返回:
            元组 (新创建的项目, 初始快照)

        异常:
            ValueError: 模板不存在
        """
        # 获取模板
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise ValueError("模板不存在")

        # 创建项目
        project = Project(
            user_id=user_id,
            name=project_name,
            description=template.description,
        )
        project = await self.project_repo.create(project)

        # 创建初始快照
        snapshot = IRSnapshot(
            project_id=project.id,
            version=1,
            status=SnapshotStatus.active,
        )
        snapshot = await self.snapshot_repo.create(snapshot)

        # 从模板数据创建 IR 节点
        snapshot_data = template.snapshot_data
        nodes_data = snapshot_data.get("nodes", [])
        edges_data = snapshot_data.get("edges", [])

        # 记录 label -> node_id 映射，用于创建边
        label_to_node_id: dict[str, object] = {}

        for node_data in nodes_data:
            node = IRNode(
                snapshot_id=snapshot.id,
                node_type=node_data["node_type"],
                label=node_data["label"],
                props=node_data.get("props"),
            )
            self.session.add(node)
            await self.session.flush()
            await self.session.refresh(node)
            label_to_node_id[node_data["label"]] = node.id

        # 从模板数据创建 IR 边
        for edge_data in edges_data:
            source_id = label_to_node_id.get(edge_data["source"])
            target_id = label_to_node_id.get(edge_data["target"])

            # 仅在两端节点都存在时创建边
            if source_id and target_id:
                edge = IREdge(
                    snapshot_id=snapshot.id,
                    source_node_id=source_id,
                    target_node_id=target_id,
                    edge_type=edge_data["edge_type"],
                )
                self.session.add(edge)

        await self.session.flush()

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

        return project, snapshot
