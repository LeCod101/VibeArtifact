from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from api_app.core.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    return _engine
