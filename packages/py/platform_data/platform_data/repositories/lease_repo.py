"""租约锁仓储 - 提供租约锁表的数据访问方法。

配合 Redis 实现子树级并发控制，DB 记录用于审计和状态查询。
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from platform_data.models.execution import LeaseLock
from platform_data.repositories.base import BaseRepository


class LeaseRepository(BaseRepository[LeaseLock]):
    """租约锁仓储，继承通用 CRUD 并提供获取锁、释放锁、检查锁状态等方法。"""

    model_class = LeaseLock

    async def acquire(
        self,
        project_id: UUID,
        scope_key: str,
        holder_id: str,
        ttl_seconds: int = 30,
    ) -> LeaseLock:
        """获取一个租约锁，写入一条 DB 记录。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识（如子树路径）
            holder_id: 持锁者标识（如 worker ID）
            ttl_seconds: 锁的有效期（秒），默认 30

        返回:
            新创建的租约锁实例
        """
        now = datetime.now(timezone.utc)
        lock = LeaseLock(
            project_id=project_id,
            scope_key=scope_key,
            holder_id=holder_id,
            acquired_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        return await self.create(lock)

    async def release(
        self, project_id: UUID, scope_key: str, holder_id: str
    ) -> bool:
        """释放指定的租约锁，设置 released_at 时间戳。

        只释放属于指定 holder 且尚未释放的锁。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识
            holder_id: 持锁者标识

        返回:
            成功释放返回 True，未找到匹配的锁返回 False
        """
        stmt = select(LeaseLock).where(
            LeaseLock.project_id == project_id,
            LeaseLock.scope_key == scope_key,
            LeaseLock.holder_id == holder_id,
            LeaseLock.released_at.is_(None),
        )
        result = await self.session.execute(stmt)
        lock = result.scalar_one_or_none()
        if lock is None:
            return False
        lock.released_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def is_held(
        self, project_id: UUID, scope_key: str
    ) -> str | None:
        """检查指定作用域的锁是否被持有。

        查找未释放且未过期的有效锁。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识

        返回:
            如果锁被持有，返回 holder_id；否则返回 None
        """
        now = datetime.now(timezone.utc)
        stmt = select(LeaseLock).where(
            LeaseLock.project_id == project_id,
            LeaseLock.scope_key == scope_key,
            LeaseLock.released_at.is_(None),
            LeaseLock.expires_at > now,
        )
        result = await self.session.execute(stmt)
        lock = result.scalar_one_or_none()
        if lock is None:
            return None
        return lock.holder_id
