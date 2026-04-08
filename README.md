<div align="center">

# VibeArtifact

**AI-Powered Vibe Coding Assistant — 对话式 AI 编程助手**

[![GitHub Stars](https://img.shields.io/github/stars/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/network)
[![GitHub Issues](https://img.shields.io/github/issues/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/pulls)
[![GitHub License](https://img.shields.io/github/license/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/LeCod101/VibeArtifact/ci.yml?branch=dev&style=flat-square&label=CI)](https://github.com/LeCod101/VibeArtifact/actions)

[English](./README-EN.md) | [中文文档](./README.md)

</div>

## 项目概述

**VibeArtifact** 是一个对话式 AI 编程助手，通过自然语言对话逐步迭代你的项目。一个 Agent + 丰富的工具集，代替复杂的多 Agent 流水线，实现代码生成、文档编写、架构设计等全栈开发任务。

> "Vibe" 代表灵感与直觉，"Artifact" 代表可交付的工程产物。
> 
> 参考 [Anything.com](https://www.anything.com/) 的架构理念 — 不需要多 Agent 流水线，一个足够聪明的 Agent + 好的工具就够了。

## 核心特性

- **对话式迭代开发** — 像和同事聊天一样描述需求，Agent 逐步生成代码、文档和图表，实时预览产物
- **单 Agent + 工具集** — 一个 VibeArtifactAgent 配备 13 种专业工具（代码生成、文档编写、项目管理等），通过 System Prompt 注入全平台知识
- **三种交互模式** — Auto（自动模式，所有工具可用）、Discussion（讨论模式，仅对话不生成）、Thinking（深度思考，低温度推理）
- **SSE 实时流式响应** — Agent 的思考过程、工具调用、内容生成全程实时流式输出，所见即所得
- **产物版本管理** — 每次修改自动创建新版本，支持版本历史浏览和回溯
- **一键导出 ZIP** — 项目产物打包为 ZIP 文件，随时下载

## 交互流程

```
用户输入需求（自然语言）
     ↓
Agent 分析 → 选择工具 → 调用工具
     ↓
实时流式输出（思考 / 工具调用 / 内容生成）
     ↓
产物创建（代码 / 文档 / 图表 / SQL）
     ↓
用户预览 → 继续迭代 or 导出
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js 16 + React 19 + TypeScript | 三栏工作区 UI |
| UI 组件 | Tailwind CSS v4 + Shadcn UI | 现代化组件库 |
| 后端 API | FastAPI + Python 3.12 | SSE 流式响应 + RESTful API |
| Agent 引擎 | 单 Agent + 工具注册 + LiteLLM | 多模型统一抽象（DeepSeek/GLM/Qwen/Claude/GPT） |
| 异步任务 | Celery + Redis | 导出打包、批量生成 |
| 数据库 | PostgreSQL + SQLAlchemy 2 + Alembic | 异步 ORM + 版本迁移 |
| 缓存/队列 | Redis | 任务队列、Celery broker |
| 认证 | JWT (access + refresh token) | 无状态认证 |
| Monorepo | pnpm workspace + uv workspace | 前后端统一管理 |

## 项目结构

```
VibeArtifact/
├── apps/
│   └── web/                          # Next.js 前端应用
│       └── src/
│           ├── app/                   # 页面路由（dashboard, project, templates）
│           ├── features/              # 业务模块（chat, artifact, project, templates）
│           ├── components/            # 共享组件（ui, layout）
│           ├── lib/                   # API 客户端、工具函数
│           └── i18n/                  # 国际化（中/英文）
├── services/
│   ├── api/                          # FastAPI 主服务
│   │   ├── api_app/
│   │   │   ├── api/routes/           # 路由（chat, artifacts, exports, auth...）
│   │   │   ├── api/schemas/          # Pydantic 请求/响应模型
│   │   │   ├── api/deps/             # 依赖注入（auth, db）
│   │   │   ├── application/services/ # 业务服务（agent_service, project_service）
│   │   │   └── infra/db/migrations/  # Alembic 数据库迁移
│   │   └── alembic.ini
│   └── worker/                       # Celery Worker
│       └── worker_app/
│           ├── celery_app.py
│           └── tasks/                # export_project, batch_generate
├── packages/py/                      # Python 共享包（uv workspace）
│   ├── agents/                       # Agent 核心
│   │   └── agents/
│   │       ├── agent.py              # VibeArtifactAgent 主类
│   │       ├── modes.py              # 模式定义（auto/discussion/thinking）
│   │       ├── system_prompt.py      # System Prompt 构建器
│   │       ├── tool_executor.py      # 工具调用执行器
│   │       └── tools/                # 工具集（code, doc, project, util）
│   ├── platform_data/                # ORM 模型（User, Project, Artifact, Message...）
│   └── runtime_tools/                # 运行时工具（LLM Provider, ZIP Packer, Cost Tracker）
├── scripts/
│   └── init_database.sql             # 数据库初始化脚本
├── infra/                            # Docker Compose（PostgreSQL + Redis）
├── pyproject.toml                    # uv workspace 根配置
└── pnpm-workspace.yaml               # pnpm workspace 配置
```

## 快速开始

### 前置要求

- [uv](https://docs.astral.sh/uv/) (Python 包管理)
- [pnpm](https://pnpm.io/) v10+ (前端包管理)
- Node.js 20+
- Docker & Docker Compose

### 启动

```bash
# 1. 克隆仓库
git clone https://github.com/LeCod101/VibeArtifact.git
cd VibeArtifact

# 2. 启动基础设施（PostgreSQL + Redis）
docker compose up -d

# 3. 安装 Python 依赖
uv sync --all-packages

# 4. 安装前端依赖
pnpm install

# 5. 数据库迁移（二选一）
# 方式 A：通过 Alembic
cd services/api && uv run alembic upgrade head && cd ../..
# 方式 B：通过 SQL 脚本
psql -U vibe -d vibeartifact -f scripts/init_database.sql

# 6. 配置环境变量
cp .env.example .env   # 编辑 .env 填入 LLM API Key 和数据库连接

# 7. 启动服务
# 终端 1：API 服务
cd services/api && uv run uvicorn api_app.main:app --reload
# 终端 2：前端
pnpm --filter web dev
# 终端 3：Worker（可选，用于导出打包）
cd services/worker && celery -A worker_app.celery_app worker --loglevel=info
```

访问 `http://localhost:3000` 开始使用。

### 运行测试

```bash
# Python 全量测试
uv run pytest

# 前端 TypeScript 编译检查
pnpm --filter web tsc --noEmit

# Python lint
uv run ruff check .
```

## 数据库模型

共 14 张业务表，覆盖核心业务、执行审计、用户配置和内容模板：

```
users                     # 用户账户
├── projects              # 项目
│   ├── conversations     # 对话
│   │   └── messages      # 消息（含 tool_calls JSONB）
│   ├── artifacts         # 产物（代码/文档/图表，parent_id 版本链）
│   ├── artifact_exports  # 导出记录
│   ├── job_runs          # Celery 任务运行
│   │   └── agent_runs    # Agent 调用记录
│   │       └── cost_ledger  # 成本账本
│   └── audit_events      # 审计事件
├── user_api_keys         # LLM API 密钥（加密）
├── user_model_preferences  # 模型偏好
├── usage_records         # 用量记录
└── project_templates     # 项目模板
```

完整建表脚本：[`scripts/init_database.sql`](./scripts/init_database.sql)

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/projects` | GET/POST | 项目列表 / 创建 |
| `/api/v1/projects/{id}` | GET/PUT | 项目详情 / 更新 |
| `/api/v1/projects/{id}/conversations` | GET/POST | 对话列表 / 创建 |
| `/api/v1/projects/{id}/chat` | POST | SSE 流式对话（Agent 核心端点） |
| `/api/v1/projects/{id}/artifacts` | GET | 产物列表 |
| `/api/v1/artifacts/{id}` | GET/PUT | 产物详情 / 编辑（创建新版本） |
| `/api/v1/artifacts/{id}/versions` | GET | 版本历史 |
| `/api/v1/projects/{id}/export` | POST | 触发导出 |
| `/api/v1/exports/{id}/download` | GET | 下载导出文件 |
| `/api/v1/templates` | GET | 模板列表 |
| `/api/v1/settings` | GET/PUT | 用户设置 |

## 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交改动（格式：`<type>: <中文描述>`）：
   - 可用 type：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `ci`
   - 示例：`git commit -m "feat: 添加用户登录功能"`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

## License

[MIT](./LICENSE)
