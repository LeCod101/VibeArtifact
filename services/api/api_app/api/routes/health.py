from fastapi import APIRouter
from sqlalchemy import text

from api_app.infra.db.session import get_engine
from api_app.infra.redis.client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    checks: dict[str, str] = {}

    # Postgres
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    # Redis
    try:
        r = get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
