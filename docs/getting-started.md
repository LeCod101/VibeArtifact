# VibeArtifact 本地开发启动指南

## 前置依赖

| 工具 | 版本要求 | 安装方式 |
|------|---------|---------|
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 10+ | `npm install -g pnpm` |
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | 最新版 | `pip install uv` 或 [官方安装](https://docs.astral.sh/uv/getting-started/installation/) |
| Docker | 最新版 | [docker.com](https://www.docker.com/) |
| Docker Compose | v2+ | Docker Desktop 自带 |

## 快速启动（推荐）

```bash
# 1. 克隆项目
git clone <repo-url> vibeartifact
cd vibeartifact

# 2. 复制环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key 等配置

# 3. 一键安装所有依赖
make install

# 4. 启动基础设施（PostgreSQL + Redis）
make dev-infra

# 5. 数据库迁移
cd services/api
alembic upgrade head
cd ../..

# 6. 分别启动各服务（需要 3 个终端窗口）
make dev-api      # 终端 1：后端 API
make dev-worker   # 终端 2：Celery Worker
make dev-web      # 终端 3：前端
```

启动后访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 分步详解

### 1. 环境变量配置

```bash
cp .env.example .env
```

编辑 `.env`，关键配置项：

```env
# 数据库（Docker Compose 默认值，无需修改）
DATABASE_URL=postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact
DATABASE_URL_SYNC=postgresql://vibe:vibe@localhost:5432/vibeartifact

# Redis（Docker Compose 默认值，无需修改）
REDIS_URL=redis://localhost:6379/0

# LLM API Key（按需填写）
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 应用密钥（开发环境可用默认值，生产环境必须修改）
SECRET_KEY=change-me-in-production
```

### 2. 安装依赖

```bash
# 一键安装（Python + Node.js）
make install
```

等价于手动执行：

```bash
# Python 依赖（uv workspace，包含 api/worker/packages）
uv sync

# 前端依赖
pnpm install
```

### 3. 启动基础设施

```bash
# 启动 PostgreSQL 16 + Redis 7
make dev-infra
```

等价于：

```bash
docker compose -f infra/compose/docker-compose.dev.yml up -d
```

服务详情：

| 服务 | 端口 | 用户/密码 | 备注 |
|------|------|----------|------|
| PostgreSQL 16 | 5432 | vibe / vibe | 数据库名：vibeartifact |
| Redis 7 | 6379 | 无密码 | DB0=缓存, DB1=Broker, DB2=Result |

验证基础设施：

```bash
# 检查容器状态
docker compose -f infra/compose/docker-compose.dev.yml ps

# 测试 PostgreSQL 连接
docker exec -it $(docker ps -qf "ancestor=postgres:16") pg_isready

# 测试 Redis 连接
docker exec -it $(docker ps -qf "ancestor=redis:7") redis-cli ping
```

### 4. 数据库迁移

```bash
cd services/api
alembic upgrade head
cd ../..
```

常用迁移命令：

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回退一个版本
alembic downgrade -1
```

### 5. 启动后端 API

```bash
make dev-api
```

等价于：

```bash
cd services/api
uv run uvicorn api_app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：

```bash
curl http://localhost:8000/api/v1/health
# 返回 {"status": "ok"} 即正常
```

API 路由一览：

| 路径 | 说明 |
|------|------|
| `GET /api/v1/health` | 健康检查 |
| `POST /api/v1/auth/signup` | 注册 |
| `POST /api/v1/auth/login` | 登录 |
| `POST /api/v1/auth/logout` | 登出 |
| `POST /api/v1/auth/refresh` | 刷新 Token |
| `/api/v1/projects` | 项目管理 |
| `/api/v1/conversations` | 会话管理 |
| `GET /docs` | Swagger 文档 |

### 6. 启动 Celery Worker

```bash
make dev-worker
```

等价于：

```bash
cd services/worker
uv run celery -A worker_app.celery_app worker --loglevel=info
```

### 7. 启动前端

```bash
make dev-web
```

等价于：

```bash
cd apps/web
pnpm dev
```

前端默认运行在 http://localhost:3000，API 请求代理到 http://localhost:8000。

---

## Makefile 命令速查

| 命令 | 说明 |
|------|------|
| `make install` | 安装所有依赖（uv sync + pnpm install） |
| `make dev-infra` | 启动 Docker 基础设施 |
| `make dev-api` | 启动 FastAPI 开发服务器 |
| `make dev-worker` | 启动 Celery Worker |
| `make dev-web` | 启动 Next.js 开发服务器 |
| `make dev` | 启动基础设施并打印启动说明 |
| `make lint` | 代码检查（Ruff + ESLint） |
| `make test` | 运行测试（pytest + web build） |
| `make gate` | 全量检查（lint + test） |
| `make stop` | 停止 Docker 基础设施 |

## 停止服务

```bash
# 停止基础设施
make stop

# 或手动
docker compose -f infra/compose/docker-compose.dev.yml down
```

## 常见问题

### 端口被占用

```bash
# 查看占用端口的进程
# Windows
netstat -ano | findstr :8000
# Linux/Mac
lsof -i :8000
```

### 数据库连接失败

1. 确认 Docker 容器正在运行：`docker ps`
2. 确认 `.env` 中 `DATABASE_URL` 与 Docker Compose 配置一致
3. 确认已执行 `alembic upgrade head`

### Redis 连接失败

1. 确认 Redis 容器运行中：`docker ps`
2. 确认 `.env` 中 `REDIS_URL` 端口正确（默认 6379）

### pnpm install 失败

```bash
# 清理缓存重试
pnpm store prune
rm -rf node_modules
pnpm install
```

### uv sync 失败

```bash
# 确认 Python 版本
python --version  # 需要 3.12+

# 重新安装
uv sync --reinstall
```
