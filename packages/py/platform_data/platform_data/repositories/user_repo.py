"""用户仓储 - 提供用户表的数据访问方法。"""

from sqlalchemy import select

from platform_data.models.user import User
from platform_data.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓储，继承通用 CRUD 并提供按邮箱查询等用户专属方法。"""

    model_class = User

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱查询用户。

        参数:
            email: 用户邮箱地址

        返回:
            找到则返回 User 实例，否则返回 None
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
