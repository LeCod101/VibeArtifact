"""认证相关的请求和响应模型 - 定义注册、登录、令牌等数据结构。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """注册请求。

    字段：
        email: 用户邮箱（经过 EmailStr 校验格式）
        password: 明文密码
        display_name: 可选的显示名称
    """

    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    """登录请求。

    字段：
        email: 用户邮箱
        password: 明文密码
    """

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """刷新令牌请求。

    字段：
        refresh_token: 用于获取新 access_token 的 refresh token
    """

    refresh_token: str


class TokenResponse(BaseModel):
    """令牌响应 - 登录/刷新成功后返回的令牌对。

    字段：
        access_token: 短期访问令牌
        refresh_token: 长期刷新令牌
        token_type: 令牌类型，固定为 "bearer"
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户信息响应 - 用于返回用户基本信息（不含敏感字段）。

    字段：
        id: 用户唯一标识
        email: 用户邮箱
        display_name: 显示名称
        status: 用户状态（active / disabled）
        created_at: 创建时间
    """

    id: UUID
    email: str
    display_name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
