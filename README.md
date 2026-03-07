<div align="center">

# VibeArtifact

**AI Product Engineering OS — 从模糊想法到可交付 MVP**

[![GitHub Stars](https://img.shields.io/github/stars/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/network)
[![GitHub Issues](https://img.shields.io/github/issues/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/pulls)
[![GitHub License](https://img.shields.io/github/license/LeCod101/VibeArtifact?style=flat-square)](https://github.com/LeCod101/VibeArtifact/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-v0.1.0-green.svg?style=flat-square)](https://github.com/LeCod101/VibeArtifact)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)

[English](./README-EN.md) | [中文文档](./README.md)

</div>

## ⚡ 项目概述

**VibeArtifact** 是一个 AI 产品工程操作系统。用户输入一个模糊的产品想法，系统自动完成需求收敛、架构设计、代码生成，交付前后端源码、文档、图表与部署配置。

> "Vibe" 代表灵感与直觉，"Artifact" 代表可交付的工程产物。VibeArtifact 的目标是让每一个灵感都能快速落地为可运行的 MVP。

## 🚀 六大核心优势

1. **想法到 MVP 全自动**：用自然语言描述你的想法，系统自动收敛为可执行的 MVP 方案，输出完整的前后端源码、数据库 Schema、API 文档和部署配置。

2. **多 Agent 黑板协作**：多个 Agent 通过 IR（Intermediate Representation）黑板模式间接协作，各 Agent 拥有独立的 prompt 配置和工具集，避免单一模型的思维局限。

3. **全栈代码生成**：一次生成 Next.js 前端 + FastAPI 后端 + PostgreSQL 数据库 + Docker Compose 部署配置，开箱即用。

4. **快照版本控制**：全量物理快照机制，子树级 Lease Lock 并发控制，确保多 Agent 同时操作时数据一致性。

5. **会话绑定分支**：Snapshot-Aware Tree Conversation，每个会话绑定独立的快照分支，支持多版本并行演进和回溯。

6. **IR 驱动架构**：LLM 输出高层业务结构，经 Translator 翻译为标准化 IROperation，不直接生成底层代码，确保输出质量可控、可审计。

## 🏗️ 系统架构

### 整体架构

```
c
```

### 一次完整生成流程

| 步骤 | 阶段 | 主要操作 | 参与组件 |
|------|------|----------|----------|
| 1 | 用户输入 | 自然语言描述产品想法 | Web UI |
| 2 | 需求收敛 | 模糊想法 → 结构化 MVP 需求 | Idea Refiner Agent |
| 3 | 架构设计 | 确定技术栈、数据模型、API 设计 | Architect Agent |
| 4 | IR 构建 | 生成 IROperation 序列 | Translator |
| 5 | 快照创建 | 基于 IR 创建全量物理快照 | IR Engine + Snapshot |
| 6 | 代码生成 | 并行生成前端、后端、数据库代码 | Code Gen Agents |
| 7 | 产物组装 | 组装源码 + 文档 + Docker Compose | Artifact Builder |
| 8 | 交付 | 输出可运行的完整项目 | Delivery |

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 平台前端 | Next.js 15 + React + TypeScript | 用户交互界面 |
| 平台 API | FastAPI + Python 3.12 | 核心业务逻辑 |
| 平台 Worker | Celery + Python 3.12 | 异步任务处理 |
| 数据库 | PostgreSQL + SQLAlchemy 2 + Alembic | 数据持久化与迁移 |
| 队列/锁/缓存 | Redis | 任务队列、分布式锁、缓存 |
| 生成项目栈 | Next.js + FastAPI + PostgreSQL + Docker Compose | 默认生成的项目技术栈 |

## 📁 项目结构

```
vibeartifact/
├── apps/                          # 应用层
│   ├── web/                       # Next.js 前端应用
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   └── ...
├── services/                      # 服务层
│   ├── api/                       # FastAPI 主服务
│   │   ├── app/
│   │   ├── alembic/
│   │   └── requirements.txt
│   ├── worker/                    # Celery Worker
│   └── ...
├── packages/                      # 共享包
│   ├── ir-core/                   # IR 核心数据结构
│   ├── snapshot/                  # 快照引擎
│   └── ...
├── docker-compose.yml             # 本地开发环境编排
├── .gitignore
├── CLAUDE.md                      # AI 开发助手上下文
└── README.md
```

## 🚀 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose（可选）

### Docker 部署（推荐）

```bash
git clone https://github.com/LeCod101/VibeArtifact.git
cd VibeArtifact
cp .env.example .env    # 编辑 .env 配置数据库和 LLM API Key
docker compose up -d
```

### 源码部署

```bash
# 1. 克隆仓库
git clone https://github.com/LeCod101/VibeArtifact.git
cd VibeArtifact

# 2. 后端环境
cd services/api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 前端环境
cd ../../apps/web
npm install

# 4. 配置环境变量
cp .env.example .env             # 编辑 .env

# 5. 数据库迁移
cd ../../services/api
alembic upgrade head

# 6. 启动服务
# 终端 1：API 服务
uvicorn app.main:app --reload
# 终端 2：Celery Worker
celery -A app.worker worker -l info
# 终端 3：前端
cd ../../apps/web && npm run dev
```

访问 `http://localhost:3000` 开始使用。

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交改动（格式：`<type>: <中文描述>`）：
   - 可用 type：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `ci`
   - 示例：`git commit -m "feat: 添加用户登录功能"`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

## 📄 License

[MIT](./LICENSE)
