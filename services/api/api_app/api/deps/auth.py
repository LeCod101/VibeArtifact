"""认证依赖注入 - 从请求中提取并验证 JWT，返回当前用户。"""

import uuid

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from platform_data.models.user import User, UserStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.db import get_db
from api_app.core.security import decode_token

# OAuth2 密码模式的 token 获取端点
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT token 中解析当前用户。

    流程：
    1. 解码 token，验证签名和过期时间
    2. 确认 token 类型为 access（拒绝 refresh token）
    3. 根据 payload 中的 sub 字段查询用户
    4. 验证用户存在且状态为 active

    参数：
        token: 从 Authorization 头提取的 Bearer token
        db: 异步数据库会话

    返回：
        User ORM 对象（当前已认证用户）

    异常：
        HTTPException 401: token 无效、过期、类型错误、用户不存在或被禁用
    """
    # 统一的 401 异常，附带 WWW-Authenticate 头
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码并验证 JWT token
        payload = decode_token(token)

        # 仅允许 access 类型的 token
        if payload.get("type") != "access":
            raise credentials_exception

        # 从 payload 中提取用户 ID
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # 将字符串形式的 UUID 转换为 uuid 对象
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        # JWTError: token 解码失败
        # ValueError: UUID 格式错误
        raise credentials_exception

    # 查询数据库获取用户记录
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 用户不存在
    if user is None:
        raise credentials_exception

    # 用户状态不是 active（已被禁用）
    if user.status != UserStatus.active:
        raise credentials_exception

    return user


async def _resolve_token_to_user(
    token: str,
    db: AsyncSession,
) -> User:
    """根据 JWT token 字符串解析出用户对象。

    内部复用函数，供 get_current_user 和 get_current_user_sse 共享逻辑。

    参数：
        token: JWT token 字符串
        db: 异步数据库会话

    返回：
        User ORM 对象

    异常：
        HTTPException 401: token 无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise credentials_exception

        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if user.status != UserStatus.active:
        raise credentials_exception

    return user


async def get_current_user_sse(
    request: Request,
    token: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """SSE 端点专用认证依赖。

    浏览器原生 EventSource 不支持自定义 Header，
    因此 SSE 端点需要同时支持两种认证方式：
    1. 优先从 Authorization Header 读取 Bearer token
    2. 回退到 URL 查询参数 ?token=xxx

    参数：
        request: FastAPI 请求对象
        token: URL 查询参数中的 token（可选）
        db: 异步数据库会话

    返回：
        User ORM 对象（当前已认证用户）

    异常：
        HTTPException 401: 无法获取有效 token 或认证失败
    """
    resolved_token: str | None = None

    # 优先从 Authorization Header 提取 token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        resolved_token = auth_header[len("Bearer "):]

    # Header 中无 token 时回退到查询参数
    if not resolved_token and token:
        resolved_token = token

    if not resolved_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _resolve_token_to_user(resolved_token, db)
