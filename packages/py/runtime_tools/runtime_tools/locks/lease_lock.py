"""基于 Redis 的子树级租约锁服务。

锁的判定逻辑走 Redis（SET NX + EX），同时可选地在 DB 的 lease_locks 表
写一条记录用于审计和故障排查。

Redis key 格式: "lease:{project_id}:{scope_key}"
Redis value: holder_id
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

import redis.asyncio as aioredis

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ── Lua 脚本：原子释放锁 ──
# 仅当 key 的值等于传入的 holder_id 时才删除，防止误释放他人的锁
_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# ── Lua 脚本：原子续期 ──
# 仅当 key 的值等于传入的 holder_id 时才重设过期时间
_EXTEND_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""


logger = logging.getLogger(__name__)


class LeaseLockService:
    """基于 Redis 的子树级租约锁服务。

    锁的判定逻辑走 Redis（SET NX + EX），同时在 DB 的 lease_locks 表
    写一条记录用于审计和故障排查（当提供 session 时）。

    参数:
        redis_client: aioredis.Redis 实例，用于实际的分布式锁操作
        session: 可选的 SQLAlchemy 异步会话，用于写 DB 审计记录
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
        session: AsyncSession | None = None,
    ) -> None:
        """初始化租约锁服务。

        参数:
            redis_client: aioredis.Redis 实例
            session: 可选的 AsyncSession，传入则启用 DB 审计记录
        """
        self._redis = redis_client
        self._session = session
        self._repo = None
        # 延迟导入 LeaseRepository，避免 runtime_tools 强依赖 platform_data
        if session is not None:
            from platform_data.repositories.lease_repo import LeaseRepository

            self._repo = LeaseRepository(session)

    @staticmethod
    def _make_key(project_id: UUID, scope_key: str) -> str:
        """构造 Redis 锁的 key。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识（如子树路径）

        返回:
            格式为 "lease:{project_id}:{scope_key}" 的字符串
        """
        return f"lease:{project_id}:{scope_key}"

    async def acquire(
        self,
        project_id: UUID,
        scope_key: str,
        holder_id: str,
        ttl_seconds: int = 30,
    ) -> bool:
        """尝试获取租约锁。

        使用 Redis SET NX EX 保证原子性。获取成功后可选写入 DB 审计记录。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识（如子树路径）
            holder_id: 持锁者标识（如 worker ID）
            ttl_seconds: 锁的有效期（秒），默认 30

        返回:
            成功获取返回 True，锁已被他人持有返回 False
        """
        key = self._make_key(project_id, scope_key)
        # SET key holder_id NX EX ttl_seconds
        # NX: 仅当 key 不存在时设置；EX: 设置过期时间（秒）
        acquired = await self._redis.set(key, holder_id, nx=True, ex=ttl_seconds)
        if not acquired:
            return False
        # 获取成功，写入 DB 审计记录（审计失败不影响核心锁逻辑）
        if self._repo is not None:
            try:
                await self._repo.acquire(project_id, scope_key, holder_id, ttl_seconds)
            except Exception:
                logger.warning(
                    "租约锁审计记录写入失败: project=%s scope=%s",
                    project_id,
                    scope_key,
                    exc_info=True,
                )
        return True

    async def release(
        self,
        project_id: UUID,
        scope_key: str,
        holder_id: str,
    ) -> bool:
        """释放租约锁。

        通过 Lua 脚本原子性地检查持锁者并删除，防止误释放他人的锁。
        释放成功后可选更新 DB 审计记录。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识
            holder_id: 持锁者标识，必须与获取时一致

        返回:
            成功释放返回 True，锁不存在或不属于该 holder 返回 False
        """
        key = self._make_key(project_id, scope_key)
        # 通过 Lua 脚本原子性地检查并删除
        result = await self._redis.eval(_RELEASE_SCRIPT, 1, key, holder_id)
        if result != 1:
            return False
        # 释放成功，更新 DB 审计记录（审计失败不影响核心锁逻辑）
        if self._repo is not None:
            try:
                await self._repo.release(project_id, scope_key, holder_id)
            except Exception:
                logger.warning(
                    "租约锁审计记录更新失败: project=%s scope=%s",
                    project_id,
                    scope_key,
                    exc_info=True,
                )
        return True

    async def is_held(
        self,
        project_id: UUID,
        scope_key: str,
    ) -> str | None:
        """检查指定作用域的锁是否被持有。

        直接查询 Redis，不涉及 DB。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识

        返回:
            如果锁被持有，返回 holder_id；否则返回 None
        """
        key = self._make_key(project_id, scope_key)
        holder = await self._redis.get(key)
        return holder

    async def extend(
        self,
        project_id: UUID,
        scope_key: str,
        holder_id: str,
        ttl_seconds: int = 30,
    ) -> bool:
        """续期租约锁。

        通过 Lua 脚本原子性地检查持锁者并重设过期时间。
        仅当锁仍由指定 holder 持有时才会续期。

        参数:
            project_id: 项目 UUID
            scope_key: 锁的作用域标识
            holder_id: 持锁者标识，必须与获取时一致
            ttl_seconds: 新的有效期（秒），默认 30

        返回:
            续期成功返回 True，锁不存在或不属于该 holder 返回 False
        """
        key = self._make_key(project_id, scope_key)
        # 通过 Lua 脚本原子性地检查持锁者并续期
        result = await self._redis.eval(
            _EXTEND_SCRIPT, 1, key, holder_id, ttl_seconds
        )
        return result == 1
