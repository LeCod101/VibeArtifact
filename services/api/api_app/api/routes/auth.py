"""认证路由模块 - 实现注册、登录、令牌刷新和获取当前用户信息的端点。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from platform_data.models.user import User, UserStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_app.api.deps.auth import get_current_user
from api_app.api.deps.db import get_db
from api_app.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from api_app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """用户注册。

    流程：
    1. 检查邮箱是否已被注册
    2. 对密码进行哈希处理
    3. 创建用户记录并写入数据库

    参数：
        body: 注册请求体（包含 email、password、display_name）
        db: 异步数据库会话

    返回：
        新创建的用户信息（UserResponse）

    异常：
        409: 邮箱已被注册
    """
    # 查询邮箱是否已存在
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    # 对明文密码进行哈希
    hashed = hash_password(body.password)

    # 创建用户 ORM 对象
    user = User(
        email=body.email,
        password_hash=hashed,
        display_name=body.display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """用户登录。

    流程：
    1. 根据邮箱查找用户
    2. 验证密码是否匹配
    3. 检查用户状态是否为 active
    4. 签发 access_token 和 refresh_token

    参数：
        body: 登录请求体（包含 email、password）
        db: 异步数据库会话

    返回：
        TokenResponse（包含 access_token 和 refresh_token）

    异常：
        401: 邮箱或密码错误
        403: 账户已禁用
    """
    # 根据邮箱查找用户
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # 用户不存在
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 验证密码
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 检查用户状态是否为 active
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已禁用",
        )

    # 签发令牌对
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """刷新访问令牌。

    流程：
    1. 解码 refresh_token，验证签名和过期时间
    2. 确认 token 类型为 refresh
    3. 查询数据库确认用户存在且状态为 active
    4. 签发新的 access_token（refresh_token 不变）

    参数：
        body: 刷新请求体（包含 refresh_token）
        db: 异步数据库会话

    返回：
        TokenResponse（新的 access_token + 原 refresh_token）

    异常：
        401: refresh_token 无效、过期、类型错误、用户不存在或被禁用
    """
    # 统一的 401 异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的刷新令牌",
    )

    try:
        # 解码 refresh_token
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise credentials_exception

    # 确认 token 类型为 refresh
    if payload.get("type") != "refresh":
        raise credentials_exception

    # 从 payload 中提取用户 ID
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # 将用户 ID 字符串转换为 UUID 对象
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 用户不存在
    if user is None:
        raise credentials_exception

    # 用户状态不是 active
    if user.status != UserStatus.active:
        raise credentials_exception

    # 签发新的 access_token
    new_access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=body.refresh_token,
    )


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前登录用户的信息。

    参数：
        current_user: 通过 JWT 认证后注入的当前用户 ORM 对象

    返回：
        UserResponse（当前用户的基本信息）
    """
    return current_user
