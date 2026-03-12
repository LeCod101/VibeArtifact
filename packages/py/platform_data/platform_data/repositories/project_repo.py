"""项目仓储 - 提供项目表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.project import Project
from platform_data.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """项目仓储，继承通用 CRUD 并提供按用户查询项目列表等方法。"""

    model_class = Project

    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> list[Project]:
        """查询指定用户的项目列表（分页）。

        参数:
            user_id: 用户 UUID
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100

        返回:
            该用户拥有的项目列表
        """
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
