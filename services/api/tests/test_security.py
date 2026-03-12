"""安全工具模块测试 - 验证密码哈希和 JWT 令牌功能。"""

from datetime import timedelta

from api_app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from jose import JWTError


def test_hash_password():
    """哈希后的密码应与原文不同。"""
    plain = "my-secret-password"
    hashed = hash_password(plain)
    assert hashed != plain
    # bcrypt 哈希以 $2b$ 开头
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    """正确密码验证应返回 True。"""
    plain = "correct-password"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    """错误密码验证应返回 False。"""
    hashed = hash_password("real-password")
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token():
    """创建 access token 后解码，sub 和 type 字段应正确。"""
    subject = "test-user-id-123"
    token = create_access_token(subject=subject)
    payload = decode_token(token)

    assert payload["sub"] == subject
    assert payload["type"] == "access"
    # payload 应包含过期时间
    assert "exp" in payload


def test_create_and_decode_refresh_token():
    """创建 refresh token 后解码，sub 和 type 字段应正确。"""
    subject = "test-user-id-456"
    token = create_refresh_token(subject=subject)
    payload = decode_token(token)

    assert payload["sub"] == subject
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_expired_token():
    """过期 token 解码应抛出 JWTError。"""
    # 使用负数时间差创建已过期的 token
    token = create_access_token(
        subject="expired-user",
        expires_delta=timedelta(seconds=-1),
    )
    try:
        decode_token(token)
        # 不应执行到此处
        assert False, "应抛出 JWTError"
    except JWTError:
        pass


def test_decode_invalid_token():
    """无效字符串解码应抛出 JWTError。"""
    try:
        decode_token("this-is-not-a-valid-jwt")
        assert False, "应抛出 JWTError"
    except JWTError:
        pass
