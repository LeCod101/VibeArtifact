"""通用仓储基类 - 提供 CRUD 和分页查询等通用数据访问方法。

所有业务 Repository 继承此基类，通过 model_class 类属性指定操作的 ORM 模型。
使用 SQLAlchemy 2 异步风格（select, AsyncSession）。
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from platform_data.models.base import Base

# 泛型类型变量，约束为 SQLAlchemy Base 子类
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """通用仓储基类，封装常见的数据库 CRUD 操作。

    子类需设置 model_class 类属性来指定操作的 ORM 模型。

    参数:
        session: SQLAlchemy 异步数据库会话
    """

    # 子类必须覆写此属性，指定对应的 ORM 模型类
    model_class: type[T]

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓储实例。

        参数:
            session: SQLAlchemy 异步数据库会话
        """
        self.session = session

    async def get_by_id(self, id: UUID) -> T | None:
        """根据主键 ID 查询单条记录。

        参数:
            id: 记录的 UUID 主键

        返回:
            找到则返回模型实例，否则返回 None
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj: T) -> T:
        """创建一条新记录。

        将对象加入会话，flush 写入数据库并刷新获取服务端生成的字段值。

        参数:
            obj: 待创建的模型实例

        返回:
            刷新后的模型实例（包含数据库生成的默认值）
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        """更新一条已有记录。

        假定 obj 已在当前会话中被修改，flush 写入数据库并刷新。

        参数:
            obj: 已修改的模型实例

        返回:
            刷新后的模型实例
        """
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> None:
        """根据主键 ID 删除一条记录。

        参数:
            id: 要删除的记录的 UUID 主键

        异常:
            如果记录不存在则静默跳过
        """
        obj = await self.get_by_id(id)
        if obj is not None:
            await self.session.delete(obj)
            await self.session.flush()

    async def list(self, offset: int = 0, limit: int = 100) -> list[T]:
        """分页查询记录列表。

        参数:
            offset: 跳过的记录数，默认 0
            limit: 返回的最大记录数，默认 100

        返回:
            模型实例列表
        """
        stmt = select(self.model_class).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
