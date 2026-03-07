# CLAUDE.md - VibeArtifact 项目上下文

> **这个文件是给 Claude 的快速上下文引导。每次新对话开始时 Claude 会自动读取此文件。**

## 项目概要

VibeArtifact 是一个 AI Product Engineering OS。用户输入模糊想法，系统自动收缩为 MVP，交付前后端源码、文档、图表、部署配置。

## 仓库策略（策略 A：双仓库）

```
vibeartifact/          # 代码仓库（可开源）— 就是当前仓库
  ├── apps/
  ├── services/
  ├── packages/
  └── ...              # 不含任何产品文档

vibeartifact-docs/     # 文档仓库（私有）— 对应本地 doc_internal/
  ├── PRD.md
  ├── 技术架构.md
  ├── 仓库目录设计.md
  ├── 开发计划_最终版.md
  ├── devlog/
  └── brainstorm/
```

**本地文档全部在 `doc_internal/`，已被 .gitignore 排除。**

### 同伴如何获取文档

```bash
# 1. 克隆代码仓库
git clone <code-repo-url> vibeartifact
cd vibeartifact

# 2. 在代码仓库内克隆文档仓库
git clone https://github.com/LeCod101/vibeartifact-docs.git doc_internal
```

`doc_internal/` 已在 `.gitignore` 中，两个仓库互不干扰。

## 关键架构决策

1. 平台后端用 Python（FastAPI + Celery + SQLAlchemy），不是 Node.js
2. Agent 是同一 LLM 的不同 prompt 配置，不是多模型集群
3. IR（Intermediate Representation）是核心数据结构，所有 Agent 通过 IR 间接协作（黑板模式）
4. LLM 输出高层业务结构，经 Translator 翻译为 IROperation，不直接输出底层操作
5. 快照采用全量物理快照，并发控制用子树级 Lease Lock
6. 会话绑定快照分支（Snapshot-Aware Tree Conversation）

## 技术栈

- 平台前端：Next.js 15 + React + TypeScript
- 平台 API：FastAPI + Python 3.12
- 平台 Worker：Celery + Python 3.12
- 数据库：PostgreSQL + SQLAlchemy 2 + Alembic
- 队列/锁/缓存：Redis
- 生成项目栈：Next.js + FastAPI + SQLAlchemy + PostgreSQL + Mermaid + Docker Compose

## 开发进度

**→ 每次接手前先读 `doc_internal/devlog/PROGRESS.md` 了解当前进度 ←**

## 文档导航

- 产品需求 → `doc_internal/PRD.md`
- 技术方案 → `doc_internal/技术架构.md`
- 代码组织 → `doc_internal/仓库目录设计.md`
- 开发顺序 → `doc_internal/开发计划_最终版.md`
- 进度总表 → `doc_internal/devlog/PROGRESS.md`
- Milestone 日志 → `doc_internal/devlog/M*.md`

## 开发规则

1. 先跑通闭环，再优化
2. 先固定栈，再扩栈
3. 不抢做 Phase 2 的功能
4. 每完成一个 Milestone，更新 `doc_internal/devlog/PROGRESS.md`
5. 每个功能块完成后，在对应的 `M*.md` 里打勾并记录遇到的问题

## Git 提交规则

1. **测试和代码审计通过后再提交**：完成一组相关改动后，先跑测试、做代码审计，确认没问题再 `git add` + `git commit`
2. **提交署名只用仓库主人**：commit 中不得出现 `Co-Authored-By`、`Claude`等字样，所有提交归属 git config 中配置的用户（LeCod101）
3. **Commit message 用简洁中文或英文**，说明改了什么、为什么改
4. **不要修改 git config**：直接使用现有的 user.name / user.email 配置
