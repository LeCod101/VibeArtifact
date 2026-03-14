"""
Docker Compose 配置生成器模块。

根据项目信息生成 docker-compose.yml 和 .env.example 文件内容。
Phase 1 使用固定模板：backend + frontend + postgres + redis 四个服务。
"""

from __future__ import annotations


def generate_compose(project_name: str) -> str:
    """
    生成 docker-compose.yml 内容。

    Phase 1 固定模板包含四个服务：
    - backend: FastAPI 服务，端口 8000
    - frontend: Next.js 服务，端口 3000
    - postgres: PostgreSQL 16 数据库，带持久化卷
    - redis: Redis 7 缓存服务

    - project_name: 项目名称，用于容器命名和卷命名
    - 返回: docker-compose.yml 的完整内容字符串
    """
    # 安全处理项目名称，用于 Docker 资源命名
    safe_name = _docker_safe_name(project_name)

    return f"""version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {safe_name}-backend
    ports:
      - "${{BACKEND_PORT:-8000}}:8000"
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
      - REDIS_URL=${{REDIS_URL}}
      - SECRET_KEY=${{SECRET_KEY}}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: {safe_name}-frontend
    ports:
      - "${{FRONTEND_PORT:-3000}}:3000"
    environment:
      - NEXT_PUBLIC_API_URL=${{NEXT_PUBLIC_API_URL:-http://localhost:8000}}
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: {safe_name}-postgres
    ports:
      - "${{POSTGRES_PORT:-5432}}:5432"
    environment:
      - POSTGRES_USER=${{POSTGRES_USER:-postgres}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
      - POSTGRES_DB=${{POSTGRES_DB:-{safe_name}}}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-postgres}}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: {safe_name}-redis
    ports:
      - "${{REDIS_PORT:-6379}}:6379"
    volumes:
      - redisdata:/data
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
"""


def generate_env_example(project_name: str) -> str:
    """
    生成 .env.example 模板内容。

    包含所有服务所需的环境变量，带说明注释和示例值。

    - project_name: 项目名称
    - 返回: .env.example 的完整内容字符串
    """
    safe_name = _docker_safe_name(project_name)

    return f"""# ============================================================
# {project_name} - 环境变量配置
# 复制此文件为 .env 并填入实际值
# ============================================================

# ---- 数据库 ----
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB={safe_name}
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:changeme@postgres:5432/{safe_name}

# ---- Redis ----
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

# ---- 后端 ----
SECRET_KEY=change-this-to-a-random-secret-key
BACKEND_PORT=8000

# ---- 前端 ----
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
"""


def _docker_safe_name(name: str) -> str:
    """
    将项目名称转换为 Docker 安全的资源名称。

    Docker 容器名和卷名只允许 [a-zA-Z0-9_.-]，
    其他字符统一替换为下划线，并转为小写。

    - name: 原始项目名称
    - 返回: Docker 安全的名称字符串
    """
    safe = name.lower().replace(" ", "_").replace("-", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    return safe or "project"
