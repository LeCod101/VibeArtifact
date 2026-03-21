from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    DATABASE_URL: str = "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact"
    REDIS_URL: str = "redis://localhost:6379/0"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # 访问令牌过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 刷新令牌过期时间（天）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # JWT 签名算法
    JWT_ALGORITHM: str = "HS256"

    # API Key 加密密钥（Fernet 对称加密，必须通过环境变量设置）
    ENCRYPTION_KEY: str = ""


settings = Settings()
