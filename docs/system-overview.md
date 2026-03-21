# VibeArtifact 系统功能总览

> **版本**: M0–M9 全部完成（PA-1 / PA-2 / PA-3 三阶段交付）
> **更新日期**: 2026-03-21

---

## 系统简介

VibeArtifact 是一个 **AI Product Engineering OS**。用户输入模糊的产品想法，系统自动收缩为可验证 MVP，交付前后端源码、文档、图表和部署配置。

支持三种工作模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **一问一答** | 用户逐条发消息，AI 逐步构建 IR | 精细控制、迭代调整 |
| **全权委托** | 一键启动 DAG 编排，AI 自动完成全部 Agent | 快速出活、MVP 生成 |
| **审慎委托** | 全权委托 + 关键节点暂停审批 | 高风险项目、需要人工把关 |

---

## 功能模块

### 1. 用户认证

| 功能 | 说明 |
|------|------|
| 注册 | 邮箱 + 密码注册 |
| 登录 | JWT 双 Token（access + refresh） |
| Token 刷新 | access_token 过期后自动刷新 |
| 用户信息 | 获取当前登录用户信息 |

### 2. 项目管理

| 功能 | 说明 |
|------|------|
| 创建项目 | 输入名称 + 描述，自动初始化 IR 快照 |
| 项目列表 | 分页查询当前用户的所有项目 |
| 项目详情 | 查看项目元数据 |
| 更新/删除 | 修改项目名称或软删除 |
| 从模板创建 | 选择预置模板，自动初始化 IR 节点和边 |

### 3. 需求收缩（Ideation）

| 功能 | 说明 |
|------|------|
| 需求分析 | 用户输入想法 → 生成 ScopeDraft + 容量评估 |
| 容量点数 | 8 维度评估（前端、后端、数据库、认证等），分为 S/M/L 三档 |
| 功能收缩 | 超出容量时自动裁剪，保留核心功能 |
| Scope 确认 | 用户确认最终范围，锁定 IR |

### 4. 一问一答模式（Chat）

| 功能 | 说明 |
|------|------|
| 发送消息 | 用户发消息 → ChatOrchestrator 编排 → Agent 执行 → IR 更新 |
| 影响分析 | ImpactAnalyzer 自动判断消息影响范围 |
| 冷启动 | 首条消息自动初始化 IR（intent → contraction → planner → schema） |
| 增量修改 | 后续消息只重跑受影响的 Agent 子集 |
| SSE 实时进度 | analysis_start/done → agent_start/done → apply_done → complete |
| 变更摘要 | 每次响应附带影响范围和操作统计 |
| 快照绑定 | 每条消息记录 snapshot_before / snapshot_after |

### 5. 分支会话（Tree Conversation）

| 功能 | 说明 |
|------|------|
| 创建分支 | 在任意快照点创建子分支，探索不同方案 |
| 切换分支 | 在分支间自由切换，消息互不干扰 |
| Fork 分支 | 从指定快照点 fork 新分支 |
| 回滚 | 回滚到旧快照，自动 fork 保护历史（no_change / forked / switched） |
| 分支树 | 查看树形分支结构 |
| 对话压缩 | 超过 10 轮自动生成 summary，降低 context 消耗 |
| 决策抽取 | 从对话中识别关键决策（技术选型、功能取舍等），写回 IR decision 节点 |
| 上下文组装 | summary + decisions + 最近 3 轮消息，精简 prompt context |

### 6. 全权委托（Full Delegation）

| 功能 | 说明 |
|------|------|
| 一键委托 | 创建 Celery DAG 任务，自动执行全部 Agent |
| DAG 编排 | 10 个 Agent 按依赖拓扑分层执行（同层并行） |
| SSE 进度 | 实时推送每个 Agent 的开始/完成事件 |
| 编译门禁 | Frontend Gate（tsc）+ Backend Gate（ruff + pytest）+ Mermaid Gate |
| 修复回路 | Gate 失败 → IssueClassifier → 重跑对应 Agent → 二轮验证 |
| needs_attention | 修复失败时标记，通知用户介入 |
| ZIP 下载 | 完成后打包源码、文档、图表下载 |

### 7. 审慎委托（Cautious Delegation）

| 功能 | 说明 |
|------|------|
| 审批暂停 | 检测到 HIGH 级风险或 PENDING 决策时自动暂停 |
| 风险面板 | 展示高风险节点列表（严重等级、描述、缓解措施） |
| 决策面板 | 展示待决策节点列表（标题、备选方案） |
| 批准继续 | 用户审批后，自动将 risk/decision 标记为 accepted |
| 拒绝终止 | 用户拒绝后，运行标记为 failed |
| 调整反馈 | 用户发送调整意见，运行标记为 needs_attention |
| 审批历史 | 记录每次审批操作（审批人、动作、理由、时间） |

### 8. 模板系统

| 功能 | 说明 |
|------|------|
| 模板列表 | 浏览公开模板（按类别筛选） |
| 模板详情 | 查看模板包含的 IR 节点和边定义 |
| 从模板创建 | 选择模板 → 输入项目名 → 自动初始化 IR + 会话 + 分支 |
| 预置模板 | Todo SaaS、Blog Platform、REST API Service |

### 9. IR（中间表示）系统

| 功能 | 说明 |
|------|------|
| 7 种节点类型 | scope / task / entity / endpoint / ui_page / ui_component / artifact |
| 2 种元节点 | risk（风险）/ decision（决策） |
| 7 种边类型 | 节点间关系（has_many / belongs_to / depends_on 等） |
| 快照版本链 | 每次变更创建新快照，parent_snapshot_id 链式追踪 |
| 操作审计 | 每个 IROperation 记录操作类型、目标节点、payload |
| 快照加载 | 加载指定快照的完整节点/边图 |

### 10. Agent 基础设施

| Agent | 职责 |
|-------|------|
| intent_agent | 解析用户意图 |
| contraction_agent | 收缩功能范围 |
| planner_agent | 任务规划 |
| schema_agent | 数据模型设计 |
| backend_agent | 后端代码生成 |
| frontend_agent | 前端代码生成 |
| doc_agent | 文档生成 |
| diagram_agent | 图表生成 |
| deploy_agent | 部署配置生成 |
| qa_agent | 质量检查 |

每个 Agent 有独立的 prompt 配置、输入/输出 schema、Translator（将高层输出翻译为 IROperation）。

---

## API 端点一览

### 认证（/api/v1/auth）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/auth/register` | 用户注册 | 无 |
| POST | `/auth/login` | 用户登录 | 无 |
| POST | `/auth/refresh` | 刷新 Token | Token |
| GET | `/users/me` | 获取当前用户 | Token |

### 项目（/api/v1/projects）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/projects` | 创建项目 | Token |
| GET | `/projects` | 项目列表 | Token |
| GET | `/projects/{id}` | 项目详情 | Token |
| PUT | `/projects/{id}` | 更新项目 | Token |
| DELETE | `/projects/{id}` | 删除项目 | Token |
| POST | `/projects/from-template` | 从模板创建 | Token |

### 会话与消息（/api/v1/conversations）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/projects/{id}/conversations` | 创建会话 | Token |
| GET | `/projects/{id}/conversations` | 会话列表 | Token |
| POST | `/conversations/{id}/messages` | 发送消息（触发 Agent） | Token |
| GET | `/conversations/{id}/messages` | 消息列表 | Token |
| GET | `/conversations/{id}/events` | SSE 事件流 | Token |

### 分支（/api/v1/conversations）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/conversations/{id}/branches` | 创建分支 | Token |
| GET | `/conversations/{id}/branches` | 分支列表 | Token |
| GET | `/conversations/{id}/branches/tree` | 分支树 | Token |
| POST | `/conversations/{id}/branches/{bid}/switch` | 切换分支 | Token |
| POST | `/conversations/{id}/branches/{bid}/fork` | Fork 分支 | Token |
| POST | `/conversations/{id}/rollback` | 回滚到快照 | Token |

### 需求分析（/api/v1/projects/{id}/generation）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/generation/analyze` | 分析用户想法 | Token |
| POST | `/generation/contract` | 收缩功能范围 | Token |
| POST | `/generation/confirm-scope` | 确认 Scope | Token |
| GET | `/generation/capacity` | 获取容量报告 | Token |

### 全权委托（/api/v1/projects/{id}/delegated-runs）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/delegated-runs` | 创建委托运行 | Token |
| GET | `/delegated-runs` | 运行列表 | Token |
| GET | `/delegated-runs/{rid}` | 运行状态 | Token |
| GET | `/delegated-runs/{rid}/events` | SSE 进度流 | Token |
| GET | `/delegated-runs/{rid}/download` | 下载 ZIP | Token |

### 审批（/api/v1/projects/{id}/delegated-runs/{rid}）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/approvals` | 获取待审批项 | Token |
| POST | `/approve` | 批准 | Token |
| POST | `/reject` | 拒绝 | Token |
| POST | `/adjust` | 调整 | Token |

### 快照（/api/v1/projects/{id}/snapshots）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/snapshots` | 快照列表 | Token |
| GET | `/snapshots/{sid}` | 快照详情 | Token |

### 模板（/api/v1/templates）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/templates` | 公开模板列表 | 无 |
| GET | `/templates/{id}` | 模板详情 | 无 |

### 健康检查（/api/v1/health）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 存活检查 | 无 |
| GET | `/health/ready` | 就绪检查 | 无 |

---

## 前端页面

| 路由 | 说明 |
|------|------|
| `/` | 落地页 |
| `/login` | 登录 |
| `/register` | 注册 |
| `/dashboard` | 仪表盘 |
| `/projects` | 项目列表 |
| `/projects/[id]` | 项目详情 — 对话 + 消息 + 分支选择器 |
| `/projects/[id]/overview` | 项目概览 |
| `/projects/[id]/ideation` | 需求分析 — 容量仪表盘 + 收缩方案 |
| `/projects/[id]/delegation` | 全权委托 — 创建运行 |
| `/projects/[id]/runs` | 运行历史 |
| `/projects/[id]/result` | 运行结果 — 审批面板 + 下载 |
| `/projects/[id]/artifacts` | 产物（Phase 2） |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 15 + React + TypeScript + TanStack Query + Zustand + shadcn/ui |
| API | FastAPI + Python 3.12 + SQLAlchemy 2 (async) |
| Worker | Celery + Python 3.12 |
| 数据库 | PostgreSQL + Alembic |
| 缓存/队列 | Redis |
| 认证 | JWT（access + refresh） |
| 实时通信 | SSE（Redis Pub/Sub） |
| AI | LiteLLM（多模型路由） |

---

## 数据模型层次

```
User
 └── Project
      ├── IRSnapshot (版本链: parent_snapshot_id)
      │    ├── IRNode (scope/task/entity/endpoint/ui_page/ui_component/artifact/risk/decision)
      │    ├── IREdge (节点间关系)
      │    └── IROperation (操作审计日志)
      ├── Conversation
      │    ├── ConversationBranch (树形: parent_branch_id)
      │    │    └── Message (snapshot_before/after 绑定)
      │    └── summary (对话压缩摘要)
      ├── JobRun (委托运行)
      │    └── ApprovalRecord (审批记录)
      └── ProjectTemplate (预置模板)
```

---

## 开发进度

| Milestone | 说明 | 状态 |
|-----------|------|------|
| M0 | 仓库初始化 | ✅ |
| M1 | 数据模型与基础设施 | ✅ |
| M2 | IR Core v1 | ✅ |
| M3 | Agent 基础设施 | ✅ |
| M4 | MVP 收缩 | ✅ |
| M5 | 全权委托闭环 | ✅ |
| M6 | Gate + QA 回路 | ✅ |
| M7 | 一问一答模式 | ✅ |
| M8 | 树状会话 | ✅ |
| M9 | 审慎委托 + 模板 | ✅ |
