"""
API Key 对称加密工具。

使用 Fernet 对称加密算法加密/解密用户的第三方 API Key。
密钥从环境变量 ENCRYPTION_KEY 读取。
"""

from __future__ import annotations

import functools

from cryptography.fernet import Fernet

from api_app.core.config import settings

# 已知的不安全默认值，禁止在运行时使用
_INSECURE_DEFAULTS = frozenset({
    "",
    "change-me-generate-with-fernet-generate-key",
})


@functools.lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """
    获取缓存的 Fernet 实例。

    首次调用时校验 ENCRYPTION_KEY 是否已正确配置，
    若为空或已知测试值则直接抛出异常，阻止启动。

    返回:
        Fernet 实例

    异常:
        RuntimeError: ENCRYPTION_KEY 未配置或为不安全值
    """
    key = settings.ENCRYPTION_KEY
    if key in _INSECURE_DEFAULTS:
        raise RuntimeError(
            "ENCRYPTION_KEY 未配置或为不安全的默认值，"
            "请通过环境变量设置有效的 Fernet 密钥。"
            "生成方法: python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_api_key(plain_key: str) -> str:
    """
    加密 API 密钥。

    参数:
        plain_key: 明文 API 密钥

    返回:
        加密后的密文字符串（base64 编码）
    """
    f = _get_fernet()
    return f.encrypt(plain_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    解密 API 密钥。

    参数:
        encrypted_key: 加密后的密文字符串

    返回:
        解密后的明文 API 密钥
    """
    f = _get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()


def mask_api_key(plain_key: str) -> str:
    """
    将 API 密钥掩码处理，仅保留前缀标识和末尾 4 位。

    例如: sk-ant-api03-xxxxxxxx-abcd → sk-***...abcd

    参数:
        plain_key: 明文 API 密钥

    返回:
        掩码后的字符串
    """
    if len(plain_key) <= 8:
        return "***"
    return f"{plain_key[:3]}***...{plain_key[-4:]}"
