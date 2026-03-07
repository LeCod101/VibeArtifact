from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    DATABASE_URL: str = "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact"
    REDIS_URL: str = "redis://localhost:6379/0"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"


settings = Settings()
