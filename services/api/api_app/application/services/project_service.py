"""项目服务 - 封装项目创建、查询等核心业务逻辑。"""

from uuid import UUID

from platform_data.models.project import Project, ProjectStatus
from platform_data.repositories.project_repo import ProjectRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectService:
    """项目业务服务层。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_repo = ProjectRepository(session)

    async def create_project(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
        project_type: str = "homework",
        course_name: str | None = None,
        tech_requirements: str | None = None,
    ) -> Project:
        """创建项目。

        参数:
            user_id: 创建者的用户 UUID
            name: 项目名称
            description: 项目描述，可选
            project_type: 项目类型，默认 homework
            course_name: 课程名称，可选
            tech_requirements: 技术要求，可选

        返回:
            新创建的 Project 实例
        """
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            project_type=project_type,
            course_name=course_name,
            tech_requirements=tech_requirements,
        )
        return await self.project_repo.create(project)

    async def list_projects(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 100,
        project_type: str | None = None,
    ) -> list[Project]:
        """查询指定用户的项目列表，支持按项目类型过滤。

        参数:
            user_id: 用户 UUID
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100
            project_type: 项目类型过滤，None 表示不过滤

        返回:
            该用户拥有的项目列表
        """
        if project_type is None:
            return await self.project_repo.list_by_user(
                user_id=user_id, offset=offset, limit=limit,
            )

        stmt = (
            select(Project)
            .where(
                Project.user_id == user_id,
                Project.project_type == project_type,
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
