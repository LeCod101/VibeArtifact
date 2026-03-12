"""租约锁服务测试 - 验证基于 Redis 的分布式锁核心操作。

测试使用 mock Redis，不需要真实 Redis 实例。
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from runtime_tools.locks.lease_lock import LeaseLockService


@pytest.fixture()
def mock_redis() -> AsyncMock:
    """创建模拟的 aioredis.Redis 实例。

    返回：
        AsyncMock 对象，预设 set / eval / get 方法
    """
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.eval = AsyncMock()
    redis.get = AsyncMock()
    return redis


@pytest.fixture()
def project_id() -> uuid.UUID:
    """生成测试用的项目 UUID。"""
    return uuid.uuid4()


@pytest.fixture()
def service(mock_redis: AsyncMock) -> LeaseLockService:
    """创建不带 DB session 的 LeaseLockService 实例。

    参数：
        mock_redis: 模拟的 Redis 客户端

    返回：
        LeaseLockService 实例
    """
    return LeaseLockService(redis_client=mock_redis, session=None)


# ──────────────────────────────
# acquire 测试
# ──────────────────────────────


async def test_acquire_success(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """SET NX 返回 True 时，acquire 应返回 True。"""
    mock_redis.set.return_value = True

    result = await service.acquire(project_id, "tree:/root", "worker-1", ttl_seconds=60)

    assert result is True
    # 验证 Redis 调用参数
    expected_key = f"lease:{project_id}:tree:/root"
    mock_redis.set.assert_awaited_once_with(expected_key, "worker-1", nx=True, ex=60)


async def test_acquire_already_held(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """SET NX 返回 None（锁已被持有）时，acquire 应返回 False。"""
    mock_redis.set.return_value = None

    result = await service.acquire(project_id, "tree:/root", "worker-2")

    assert result is False


# ──────────────────────────────
# release 测试
# ──────────────────────────────


async def test_release_success(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """Lua 脚本返回 1 时，release 应返回 True。"""
    mock_redis.eval.return_value = 1

    result = await service.release(project_id, "tree:/root", "worker-1")

    assert result is True
    # 验证 eval 被调用，且传入了正确的 key 和 holder_id
    mock_redis.eval.assert_awaited_once()
    call_args = mock_redis.eval.call_args
    expected_key = f"lease:{project_id}:tree:/root"
    # eval(script, num_keys, key, holder_id)
    assert call_args[0][1] == 1
    assert call_args[0][2] == expected_key
    assert call_args[0][3] == "worker-1"


async def test_release_not_held(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """Lua 脚本返回 0（锁不属于该 holder）时，release 应返回 False。"""
    mock_redis.eval.return_value = 0

    result = await service.release(project_id, "tree:/root", "worker-wrong")

    assert result is False


# ──────────────────────────────
# is_held 测试
# ──────────────────────────────


async def test_is_held_returns_holder(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """锁被持有时，is_held 应返回 holder_id。"""
    mock_redis.get.return_value = "worker-1"

    result = await service.is_held(project_id, "tree:/root")

    assert result == "worker-1"
    expected_key = f"lease:{project_id}:tree:/root"
    mock_redis.get.assert_awaited_once_with(expected_key)


async def test_is_held_not_held(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """锁未被持有时，is_held 应返回 None。"""
    mock_redis.get.return_value = None

    result = await service.is_held(project_id, "tree:/root")

    assert result is None


# ──────────────────────────────
# extend 测试
# ──────────────────────────────


async def test_extend_success(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """Lua 脚本返回 1 时，extend 应返回 True。"""
    mock_redis.eval.return_value = 1

    result = await service.extend(project_id, "tree:/root", "worker-1", ttl_seconds=120)

    assert result is True
    # 验证 eval 被调用，且传入了正确的 holder_id 和 ttl
    mock_redis.eval.assert_awaited_once()
    call_args = mock_redis.eval.call_args
    expected_key = f"lease:{project_id}:tree:/root"
    assert call_args[0][1] == 1
    assert call_args[0][2] == expected_key
    assert call_args[0][3] == "worker-1"
    assert call_args[0][4] == 120


async def test_extend_not_held(
    service: LeaseLockService,
    mock_redis: AsyncMock,
    project_id: uuid.UUID,
):
    """Lua 脚本返回 0（锁不属于该 holder）时，extend 应返回 False。"""
    mock_redis.eval.return_value = 0

    result = await service.extend(project_id, "tree:/root", "worker-wrong")

    assert result is False


# ──────────────────────────────
# _make_key 格式测试
# ──────────────────────────────


def test_make_key_format():
    """_make_key 应生成 'lease:{project_id}:{scope_key}' 格式的 key。"""
    pid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    key = LeaseLockService._make_key(pid, "tree:/components/header")

    assert key == "lease:12345678-1234-5678-1234-567812345678:tree:/components/header"
