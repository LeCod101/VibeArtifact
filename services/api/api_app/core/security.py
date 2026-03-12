"""
安全工具模块

提供密码哈希和 JWT 令牌的工具函数，
供认证流程（注册、登录、令牌刷新）统一调用。
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from api_app.core.config import settings


def hash_password(plain: str) -> str:
    """
    对明文密码进行 bcrypt 哈希。

    参数:
        plain: 用户输入的明文密码
    返回:
        bcrypt 哈希后的密码字符串
    """
    return bcrypt.hashpw(
        plain.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    验证明文密码与哈希值是否匹配。

    参数:
        plain: 用户输入的明文密码
        hashed: 数据库中存储的哈希密码
    返回:
        匹配返回 True，否则返回 False
    """
    return bcrypt.checkpw(
        plain.encode("utf-8"), hashed.encode("utf-8")
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建访问令牌（access token）。

    参数:
        subject: 令牌主体，通常为用户 ID 的字符串形式
        expires_delta: 自定义过期时长；为 None 时使用配置默认值
    返回:
        编码后的 JWT 字符串
    """
    # 未指定过期时长时，从全局配置读取默认分钟数
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建刷新令牌（refresh token）。

    参数:
        subject: 令牌主体，通常为用户 ID 的字符串形式
        expires_delta: 自定义过期时长；为 None 时使用配置默认值
    返回:
        编码后的 JWT 字符串
    """
    # 未指定过期时长时，从全局配置读取默认天数
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """
    解码并验证 JWT 令牌。

    参数:
        token: 待解码的 JWT 字符串
    返回:
        解码后的 payload 字典，包含 sub、exp、type 等字段
    异常:
        jose.JWTError: 令牌无效、过期或签名不匹配时抛出
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
