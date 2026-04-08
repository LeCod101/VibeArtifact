"""应用入口 - 创建 FastAPI 实例并挂载路由和中间件。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_app.api.routes.artifacts import router as artifacts_router
from api_app.api.routes.auth import router as auth_router
from api_app.api.routes.chat import router as chat_router
from api_app.api.routes.conversations import router as conversations_router
from api_app.api.routes.exports import router as exports_router
from api_app.api.routes.health import router as health_router
from api_app.api.routes.projects import router as projects_router
from api_app.api.routes.settings import router as settings_router
from api_app.api.routes.templates import router as templates_router

app = FastAPI(title="VibeArtifact API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(artifacts_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
