"""测试配置 - 提供内存 SQLite 测试数据库和 httpx 异步客户端。"""

import sys
from pathlib import Path

# 将 services/api 加入 sys.path，使 api_app 包可被直接导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- passlib 与新版 bcrypt (>=4.2) 的兼容性修补 ---
# bcrypt 4.2+ 移除了 __about__ 模块，5.0+ 严格拒绝 >72 字节的密码。
# passlib 在初始化时需要读取 bcrypt 版本号，并发送 255 字节密码做 wrap bug 检测。
# 必须在 passlib 被导入前完成修补。
import bcrypt as _bcrypt

# 补回 __about__ 模块，让 passlib 能读取版本号
if not hasattr(_bcrypt, "__about__"):

    class _About:
        """为 passlib 提供 bcrypt 版本信息的兼容垫片。"""

        __version__ = getattr(_bcrypt, "__version__", "4.0.0")

    _bcrypt.__about__ = _About  # type: ignore[attr-defined]

# 包装 hashpw，自动截断超过 72 字节的密码
# passlib 的 detect_wrap_bug 会发送 255 字节密码，新版 bcrypt 会直接拒绝
_original_hashpw = _bcrypt.hashpw


def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    """对 bcrypt.hashpw 的包装，自动截断超长密码至 72 字节。"""
    return _original_hashpw(password[:72], salt)


_bcrypt.hashpw = _safe_hashpw  # type: ignore[attr-defined]

# 同样包装 checkpw（如果存在）
if hasattr(_bcrypt, "checkpw"):
    _original_checkpw = _bcrypt.checkpw

    def _safe_checkpw(password: bytes, hashed_password: bytes) -> bool:
        """对 bcrypt.checkpw 的包装，自动截断超长密码至 72 字节。"""
        return _original_checkpw(password[:72], hashed_password)

    _bcrypt.checkpw = _safe_checkpw  # type: ignore[attr-defined]

import platform_data.models  # noqa: E402, F401
import pytest  # noqa: E402
from api_app.main import app  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from platform_data.models.base import Base  # noqa: E402
from sqlalchemy import JSON, event  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

# SQLite 内存异步引擎 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _patch_metadata_for_sqlite():
    """将 ORM metadata 中不兼容 SQLite 的类型替换为兼容类型。

    处理内容：
    1. 所有 native_enum 改为非原生模式（SQLite 无 CREATE TYPE）
    2. 所有 JSONB 列替换为通用 JSON 类型（SQLite 无 JSONB）
    """
    from sqlalchemy.dialects.postgresql import JSONB

    for table in Base.metadata.tables.values():
        for column in table.columns:
            # 将 native_enum 改为非原生模式
            if hasattr(column.type, "native_enum"):
                column.type.native_enum = False
            # 将 PostgreSQL JSONB 替换为通用 JSON
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture()
async def db_engine():
    """创建测试用内存数据库引擎，每次测试前建表，测试后销毁。

    通过 SQLite PRAGMA 启用外键约束，并在 create_all 之前修补
    所有不兼容 SQLite 的列类型。
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # SQLite 默认不启用外键约束，需要手动开启
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_fk(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 替换不兼容 SQLite 的类型（JSONB -> JSON, native_enum -> non-native）
    _patch_metadata_for_sqlite()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine):
    """提供测试用数据库会话，测试结束后自动关闭。"""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture()
async def client(db_session):
    """提供覆盖了 DB 依赖的 httpx 异步客户端。

    deps/db.py 中的 get_db 是 get_db_session 的别名引用，
    FastAPI 的依赖注入按函数对象匹配，因此需要 override 原始的
    get_db_session 函数。
    """
    from api_app.infra.db.session import get_db_session

    async def override_get_db():
        """覆盖数据库依赖，返回测试用会话。"""
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
