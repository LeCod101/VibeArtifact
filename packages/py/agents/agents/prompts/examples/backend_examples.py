"""
Backend Agent Few-Shot 示例。

提供 Todo 应用后端完整示例，帮助 LLM 理解 BackendPlan 的输出格式。
每个文件包含 path、content、language，代码结构完整但精简。
"""

# noqa: E501 — few-shot 示例中的代码字符串行长度受限于真实代码格式

BACKEND_EXAMPLES = (  # noqa: E501
    """## 示例

### 示例（Todo 应用后端）

输入（SchemaPlan 摘要）：
实体：User（id, username, email, password_hash, is_active）、Todo（id, title, description, status, user_id）
端点：用户认证（注册/登录）+ Todo CRUD

输出：
{
  "files": [
    {
      "path": "backend/main.py",
      "language": "python",
      "content": "\\"\\"\\"\\n后端应用入口模块。\\n\\n创建 FastAPI 实例，注册路由和中间件。\\n\\"\\"\\"\\nfrom fastapi import FastAPI\\nfrom fastapi.middleware.cors import CORSMiddleware\\n\\nfrom routes.todos import router as todos_router\\n\\n# 创建 FastAPI 应用实例\\napp = FastAPI(title=\\"效率清单 API\\", description=\\"Todo 应用后端接口\\")\\n\\n# 添加 CORS 中间件\\napp.add_middleware(\\n    CORSMiddleware,\\n    allow_origins=[\\"*\\"],\\n    allow_credentials=True,\\n    allow_methods=[\\"*\\"],\\n    allow_headers=[\\"*\\"],\\n)\\n\\n# 注册路由\\napp.include_router(todos_router, prefix=\\"/api\\")\\n\\n\\n@app.get(\\"/health\\")\\nasync def health_check():\\n    \\"\\"\\"健康检查端点。\\"\\"\\"\\n    return {\\"status\\": \\"ok\\"}\\n"
    },
    {
      "path": "backend/config.py",
      "language": "python",
      "content": "\\"\\"\\"\\n配置管理模块。\\n\\n从环境变量读取应用配置。\\n\\"\\"\\"\\nfrom pydantic_settings import BaseSettings\\n\\n\\nclass Settings(BaseSettings):\\n    \\"\\"\\"应用配置，支持从环境变量和 .env 文件读取。\\"\\"\\"\\n\\n    DATABASE_URL: str = \\"postgresql+asyncpg://postgres:postgres@localhost:5432/tododb\\"\\n    SECRET_KEY: str = \\"dev-secret-key\\"\\n\\n    model_config = {\\"env_file\\": \\".env\\"}\\n\\n\\n# 全局配置单例\\nsettings = Settings()\\n"
    },
    {
      "path": "backend/database.py",
      "language": "python",
      "content": "\\"\\"\\"\\n数据库连接模块。\\n\\n管理 SQLAlchemy 异步引擎和会话。\\n\\"\\"\\"\\nfrom collections.abc import AsyncGenerator\\n\\nfrom sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine\\nfrom sqlalchemy.orm import DeclarativeBase\\n\\nfrom config import settings\\n\\n# 创建异步引擎\\nengine = create_async_engine(settings.DATABASE_URL, echo=False)\\n\\n# 创建异步会话工厂\\nasync_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)\\n\\n\\nclass Base(DeclarativeBase):\\n    \\"\\"\\"ORM 基类。\\"\\"\\"\\n    pass\\n\\n\\nasync def get_db() -> AsyncGenerator[AsyncSession, None]:\\n    \\"\\"\\"数据库会话依赖注入。\\"\\"\\"\\n    async with async_session() as session:\\n        yield session\\n"
    },
    {
      "path": "backend/models/__init__.py",
      "language": "python",
      "content": "\\"\\"\\"模型包，导出所有 ORM 模型。\\"\\"\\"\\nfrom .todo import Todo\\n\\n__all__ = [\\"Todo\\"]\\n"
    },
    {
      "path": "backend/models/todo.py",
      "language": "python",
      "content": "\\"\\"\\"\\nTodo ORM 模型。\\n\\n定义 Todo 数据实体的数据库映射。\\n\\"\\"\\"\\nimport uuid\\nfrom datetime import datetime\\n\\nfrom sqlalchemy import DateTime, String, Text, func\\nfrom sqlalchemy.dialects.postgresql import UUID\\nfrom sqlalchemy.orm import Mapped, mapped_column\\n\\nfrom database import Base\\n\\n\\nclass Todo(Base):\\n    \\"\\"\\"待办事项数据模型。\\"\\"\\"\\n\\n    __tablename__ = \\"todos\\"\\n\\n    # 主键\\n    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)\\n    # 标题\\n    title: Mapped[str] = mapped_column(String(200), nullable=False)\\n    # 描述\\n    description: Mapped[str | None] = mapped_column(Text, nullable=True)\\n    # 状态\\n    status: Mapped[str] = mapped_column(String(20), nullable=False, default=\\"pending\\")\\n    # 创建时间\\n    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())\\n    # 更新时间\\n    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())\\n"
    },
    {
      "path": "backend/schemas/__init__.py",
      "language": "python",
      "content": "\\"\\"\\"Schema 包，导出所有 Pydantic schema。\\"\\"\\"\\nfrom .todo import TodoCreate, TodoResponse, TodoUpdate\\n\\n__all__ = [\\"TodoCreate\\", \\"TodoUpdate\\", \\"TodoResponse\\"]\\n"
    },
    {
      "path": "backend/schemas/todo.py",
      "language": "python",
      "content": "\\"\\"\\"\\nTodo Pydantic Schema。\\n\\n定义 Todo 的请求体和响应体格式。\\n\\"\\"\\"\\nimport uuid\\nfrom datetime import datetime\\n\\nfrom pydantic import BaseModel, ConfigDict\\n\\n\\nclass TodoCreate(BaseModel):\\n    \\"\\"\\"创建 Todo 请求体。\\"\\"\\"\\n    title: str\\n    description: str | None = None\\n    status: str = \\"pending\\"\\n\\n\\nclass TodoUpdate(BaseModel):\\n    \\"\\"\\"更新 Todo 请求体。\\"\\"\\"\\n    title: str | None = None\\n    description: str | None = None\\n    status: str | None = None\\n\\n\\nclass TodoResponse(BaseModel):\\n    \\"\\"\\"Todo 响应体。\\"\\"\\"\\n    model_config = ConfigDict(from_attributes=True)\\n\\n    id: uuid.UUID\\n    title: str\\n    description: str | None\\n    status: str\\n    created_at: datetime\\n    updated_at: datetime\\n"
    },
    {
      "path": "backend/routes/__init__.py",
      "language": "python",
      "content": "\\"\\"\\"路由包，导出所有 API 路由。\\"\\"\\"\\n"
    },
    {
      "path": "backend/routes/todos.py",
      "language": "python",
      "content": "\\"\\"\\"\\nTodo 路由模块。\\n\\n定义 Todo 相关的 API 端点。\\n\\"\\"\\"\\nimport uuid\\n\\nfrom fastapi import APIRouter, Depends, HTTPException\\nfrom sqlalchemy.ext.asyncio import AsyncSession\\n\\nfrom database import get_db\\nfrom schemas.todo import TodoCreate, TodoResponse, TodoUpdate\\nfrom services.todo import TodoService\\n\\nrouter = APIRouter(tags=[\\"todos\\"])\\n\\n\\n@router.get(\\"/todos\\", response_model=list[TodoResponse])\\nasync def list_todos(db: AsyncSession = Depends(get_db)):\\n    \\"\\"\\"获取所有待办事项。\\"\\"\\"\\n    return await TodoService.get_all(db)\\n\\n\\n@router.post(\\"/todos\\", response_model=TodoResponse, status_code=201)\\nasync def create_todo(data: TodoCreate, db: AsyncSession = Depends(get_db)):\\n    \\"\\"\\"创建新的待办事项。\\"\\"\\"\\n    return await TodoService.create(db, data)\\n\\n\\n@router.get(\\"/todos/{todo_id}\\", response_model=TodoResponse)\\nasync def get_todo(todo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):\\n    \\"\\"\\"获取单个待办事项详情。\\"\\"\\"\\n    todo = await TodoService.get_by_id(db, todo_id)\\n    if not todo:\\n        raise HTTPException(status_code=404, detail=\\"待办事项不存在\\")\\n    return todo\\n\\n\\n@router.put(\\"/todos/{todo_id}\\", response_model=TodoResponse)\\nasync def update_todo(todo_id: uuid.UUID, data: TodoUpdate, db: AsyncSession = Depends(get_db)):\\n    \\"\\"\\"更新待办事项。\\"\\"\\"\\n    todo = await TodoService.update(db, todo_id, data)\\n    if not todo:\\n        raise HTTPException(status_code=404, detail=\\"待办事项不存在\\")\\n    return todo\\n\\n\\n@router.delete(\\"/todos/{todo_id}\\", status_code=204)\\nasync def delete_todo(todo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):\\n    \\"\\"\\"删除待办事项。\\"\\"\\"\\n    deleted = await TodoService.delete(db, todo_id)\\n    if not deleted:\\n        raise HTTPException(status_code=404, detail=\\"待办事项不存在\\")\\n"
    },
    {
      "path": "backend/services/__init__.py",
      "language": "python",
      "content": "\\"\\"\\"Service 包，导出所有业务逻辑服务。\\"\\"\\"\\n"
    },
    {
      "path": "backend/services/todo.py",
      "language": "python",
      "content": "\\"\\"\\"\\nTodo 业务逻辑服务。\\n\\n提供 Todo 实体的 CRUD 操作。\\n\\"\\"\\"\\nimport uuid\\n\\nfrom sqlalchemy import select\\nfrom sqlalchemy.ext.asyncio import AsyncSession\\n\\nfrom models.todo import Todo\\nfrom schemas.todo import TodoCreate, TodoUpdate\\n\\n\\nclass TodoService:\\n    \\"\\"\\"Todo CRUD 服务。\\"\\"\\"\\n\\n    @staticmethod\\n    async def get_all(db: AsyncSession) -> list[Todo]:\\n        \\"\\"\\"获取所有待办事项。\\"\\"\\"\\n        result = await db.execute(select(Todo))\\n        return list(result.scalars().all())\\n\\n    @staticmethod\\n    async def get_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:\\n        \\"\\"\\"根据 ID 获取待办事项。\\"\\"\\"\\n        return await db.get(Todo, todo_id)\\n\\n    @staticmethod\\n    async def create(db: AsyncSession, data: TodoCreate) -> Todo:\\n        \\"\\"\\"创建待办事项。\\"\\"\\"\\n        todo = Todo(**data.model_dump())\\n        db.add(todo)\\n        await db.commit()\\n        await db.refresh(todo)\\n        return todo\\n\\n    @staticmethod\\n    async def update(db: AsyncSession, todo_id: uuid.UUID, data: TodoUpdate) -> Todo | None:\\n        \\"\\"\\"更新待办事项。\\"\\"\\"\\n        todo = await db.get(Todo, todo_id)\\n        if not todo:\\n            return None\\n        for key, val in data.model_dump(exclude_unset=True).items():\\n            setattr(todo, key, val)\\n        await db.commit()\\n        await db.refresh(todo)\\n        return todo\\n\\n    @staticmethod\\n    async def delete(db: AsyncSession, todo_id: uuid.UUID) -> bool:\\n        \\"\\"\\"删除待办事项。\\"\\"\\"\\n        todo = await db.get(Todo, todo_id)\\n        if not todo:\\n            return False\\n        await db.delete(todo)\\n        await db.commit()\\n        return True\\n"
    },
    {
      "path": "backend/requirements.txt",
      "language": "txt",
      "content": "fastapi==0.115.0\\nuvicorn[standard]==0.30.0\\nsqlalchemy[asyncio]==2.0.35\\nasyncpg==0.30.0\\npydantic==2.9.0\\npydantic-settings==2.5.0\\nalembic==1.13.0\\n"
    },
    {
      "path": "backend/Dockerfile",
      "language": "dockerfile",
      "content": "FROM python:3.12-slim\\n\\nWORKDIR /app\\n\\nCOPY requirements.txt .\\nRUN pip install --no-cache-dir -r requirements.txt\\n\\nCOPY . .\\n\\nEXPOSE 8000\\n\\nCMD [\\"uvicorn\\", \\"main:app\\", \\"--host\\", \\"0.0.0.0\\", \\"--port\\", \\"8000\\"]\\n"
    }
  ]
}
"""
)
