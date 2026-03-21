"""模板仓储 - 提供项目模板表的数据访问方法。"""

from uuid import UUID

from sqlalchemy import select

from platform_data.models.template import ProjectTemplate
from platform_data.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[ProjectTemplate]):
    """模板仓储，继承通用 CRUD 并提供查询公开模板等方法。"""

    model_class = ProjectTemplate

    async def list_public(
        self, category: str | None = None
    ) -> list[ProjectTemplate]:
        """查询公开模板列表，支持按类别过滤。

        参数:
            category: 模板类别字符串，可选。传入时仅返回该类别的模板。

        返回:
            公开模板列表
        """
        stmt = select(ProjectTemplate).where(
            ProjectTemplate.is_public.is_(True)
        )

        if category is not None:
            stmt = stmt.where(ProjectTemplate.category == category)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, template_id: UUID) -> ProjectTemplate | None:
        """根据模板 ID 查询模板详情。

        参数:
            template_id: 模板 UUID

        返回:
            模板实例，不存在则返回 None
        """
        stmt = select(ProjectTemplate).where(
            ProjectTemplate.id == template_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """统计模板总数。

        返回:
            模板总数
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(ProjectTemplate)
        result = await self.session.execute(stmt)
        return result.scalar_one()
