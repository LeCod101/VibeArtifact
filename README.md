<div align="center">

# VibeArtifact

**AI Product Engineering OS — 从模糊想法到可交付 MVP**

[![GitHub Stars](https://img.shields.io/github/stars/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/network)
[![GitHub Issues](https://img.shields.io/github/issues/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/pulls)
[![GitHub License](https://img.shields.io/github/license/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/LeCod101/VibeArtifact/ci.yml?branch=dev&style=flat-square&label=CI)](https://github.com/LeCod101/VibeArtifact/actions)

[English](./README-EN.md) | [中文文档](./README.md)

</div>

## 项目概述

**VibeArtifact** 是一个 AI 产品工程操作系统。用户输入一个模糊的产品想法，系统自动完成需求收敛、架构设计、代码生成，交付前后端源码、文档、图表与部署配置。

> "Vibe" 代表灵感与直觉，"Artifact" 代表可交付的工程产物。VibeArtifact 的目标是让每一个灵感都能快速落地为可运行的 MVP。

## 核心特性

- **想法到 MVP 全自动** — 自然语言描述想法，系统自动收敛为可执行的 MVP 方案，输出完整的前后端源码、数据库 Schema、API 文档和部署配置
- **10 Agent 流水线协作** — intent、contraction、planner、schema、backend、frontend、doc、diagram、qa、export，各司其职，通过 IR 黑板模式间接协作
- **IR 驱动架构** — LLM 输出高层业务结构（ScopeDraft、SchemaPlan 等），经 Translator 翻译为标准化 IROperation，确保输出质量可控、可审计
- **全栈代码生成** — 一次生成 Next.js 前端 + FastAPI 后端 + PostgreSQL 数据库 + Docker Compose 部署配置
- **快照版本控制** — 全量物理快照机制，子树级 Lease Lock 并发控制，确保多 Agent 同时操作时数据一致性
- **会话绑定分支** — Snapshot-Aware Tree Conversation，每个会话绑定独立的快照分支，支持多版本并行演进和回溯

## 生成流程

| 步骤 | 阶段 | 主要操作 | 参与 Agent |
|------|------|----------|-----------|
| 1 | 用户输入 | 自然语言描述产品想法 | — |
| 2 | 意图识别 | 解析用户意图，提取功能范围 | intent |
| 3 | 需求收缩 | 模糊想法 → MVP 范围 + 风险识别 | contraction |
| 4 | 任务规划 | 拆解为有序任务步骤 | planner |
| 5 | Schema 设计 | 数据模型 + API 端点设计 | schema |
| 6 | 代码生成 | 并行生成前端、后端代码 | backend, frontend |
| 7 | 文档 + 图表 | 生成文档和 Mermaid 图表 | doc, diagram |
| 8 | 质量检查 | 代码审查 + 修复建议 | qa |
| 9 | 产物导出 | 组装源码 + 文档 + Docker Compose | export |

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 平台前端 | Next.js 15 + React + TypeScript | 用户交互界面 |
| 平台 API | FastAPI + Python 3.12 | 核心业务逻辑 |
| 平台 Worker | Celery + Python 3.12 | 异步任务处理 |
| 数据库 | PostgreSQL + SQLAlchemy 2 + Alembic | 数据持久化与迁移 |
| 队列/锁/缓存 | Redis | 任务队列、分布式锁、缓存 |
| 认证 | JWT (access + refresh token) | 用户认证 |
| Monorepo | pnpm workspace + uv workspace | 前端 + Python 统一管理 |
| 生成项目栈 | Next.js + FastAPI + PostgreSQL + Docker Compose | 默认生成的项目技术栈 |

## 项目结构

```
vibeartifact/
├── apps/
│   └── web/                        # Next.js 15 前端应用
├── services/
│   ├── api/                        # FastAPI 主服务
│   │   ├── api_app/                # 应用代码（routes, models, services）
│   │   └── alembic/                # 数据库迁移
│   └── worker/                     # Celery Worker
│       └── worker_app/
├── packages/py/                    # Python 共享包（uv workspace）
│   ├── ir_core/                    # IR 核心：节点/边/操作类型、校验器、快照引擎
│   ├── agents/                     # Agent 基础设施：schema、prompt、config、translator、runner
│   ├── platform_data/              # ORM 模型、Repository、Session 工厂
│   └── runtime_tools/              # LLM Provider、Cost Tracker 等运行时工具
├── infra/                          # Docker Compose（PostgreSQL + Redis）
├── tests/                          # 根级集成测试
├── pyproject.toml                  # uv workspace 根配置
├── pnpm-workspace.yaml             # pnpm workspace 配置
├── Makefile                        # 常用命令快捷方式
└── .github/workflows/ci.yml       # GitHub Actions CI
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

# 5. 数据库迁移
cd services/api && uv run alembic upgrade head && cd ../..

# 6. 配置环境变量
cp .env.example .env   # 编辑 .env 填入数据库连接和 LLM API Key

# 7. 启动服务
# 终端 1：API
cd services/api && uv run uvicorn api_app.main:app --reload
# 终端 2：前端
pnpm --filter web dev
```

访问 `http://localhost:3000` 开始使用。

### 运行测试

```bash
# Python 全量测试
uv run pytest

# 前端 lint
pnpm --filter web lint

# Python lint
uv run ruff check .
```

## 开发进度

| Milestone | 状态 | 说明 |
|-----------|------|------|
| M0 仓库初始化 | ✅ | 项目骨架、Docker Compose、CI |
| M1 数据模型与基础设施 | ✅ | ORM、认证、CRUD、Lease Lock、前端页面 |
| M2 IR Core v1 | ✅ | 类型系统、校验器、快照引擎、Graph Query |
| M3 Agent 基础设施 | ✅ | 10 Agent Schema、LLM Provider、Prompt、Translator、Runner |
| M4 MVP 收缩 | 🔲 | contraction agent、容量点数 |
| M5 全权委托闭环 | 🔲 | DAG 编排、代码生成、ZIP 导出 |
| M6 Gate + QA 回路 | 🔲 | 编译门禁、qa agent、修复回路 |

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
