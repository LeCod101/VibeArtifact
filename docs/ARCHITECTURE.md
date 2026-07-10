# ARCHITECTURE.md

> 架构总览。项目实例上下文/模块索引见 `docs/PROJECT_CONTEXT.md`；模块级细节见各 `<module>/CLAUDE.md`。

## 架构概览

VibeArtifact 是一个三层 Monorepo（pnpm workspace + uv workspace 统一管理）：**apps/web**（Next.js 前端，用户交互）→ **services/api**（FastAPI，同步业务 API + SSE 推流）→ **services/worker**（Celery，异步 DAG 编排，逐层调度 Agent 完成需求收敛到代码生成的全流程）。三者共享 **packages/py/** 下 3 个 Python 库：`agents`（Agent 配置/Prompt/Runner + LangGraph author↔reviewer 协作循环）、`platform_data`（SQLAlchemy ORM + Repository，含 workspace_files/conversation_turns）、`runtime_tools`（LangChain 国产模型接入、Gate、Cost Tracker、导出打包）。PostgreSQL 承载持久化数据与工作区文件（workspace_files 表，Agent 产物的唯一存储），Redis 承载 Celery 队列与 SSE Pub/Sub。

生成引擎的分层原则：**LangGraph 管"一次对话怎么循环"**（backend/frontend/doc/diagram 四个 author 各配对一个 reviewer，在单个 Celery task 内多轮"写→评→改"直到 approve 或达轮次上限）；**Celery 管"这些循环怎么分布式跑"**（DAG 分层调度、30 分钟软超时、失败标记）。LLM 全部走国产模型（DeepSeek / 通义千问 DashScope / Moonshot Kimi / MiniMax），通过 LangChain 原生集成接入，代码中不写死任何厂商默认值（由 REASONING_PROVIDER/REASONING_MODEL、GENERATION_PROVIDER/GENERATION_MODEL 环境变量决定）。

仓库同时内嵌 **aiGroup 开发协作框架**（`.claude/`、`docs/rules/`、`manifests/`、`scripts/orchestration`、`scripts/hooks`）：这是用于辅助人类+AI 协作开发 VibeArtifact 本身的工具层，与运行时架构（上一段）相互独立，仅在"跨切关注点"一节简要提及。

## 组件 / 模块边界

```
apps/web (Next.js)
   │  HTTP + SSE (NEXT_PUBLIC_API_URL, 默认 :8000)
   ▼
services/api (FastAPI, api_app)
   │  ├─ application/services/*  编排用例（chat_orchestrator、project_service、conversation_service…）
   │  ├─ api/routes/*            REST + SSE 端点（auth/projects/conversations/generation/delegated/snapshots(废弃stub+工作区文件)/artifacts）
   │  ├─ infra/db, infra/redis   SQLAlchemy AsyncSession / Redis 客户端
   │  └─ core/security           JWT (access + refresh)
   │  依赖 → platform_data（声明于 pyproject）；运行时还 import agents / runtime_tools（见"已知技术债"）
   ▼ (Celery .delay() 触发；DB 记录 JobRun/AgentRun 供状态查询)
services/worker (Celery, worker_app)
   │  ├─ orchestrator/dag.py        基于 AgentRegistry 依赖关系构建分层执行计划（reviewer 不进 DAG）
   │  ├─ orchestrator/run_manager.py  run 状态机（pending→running→completed/failed/needs_attention）
   │  ├─ tasks/orchestrate.py       顶层编排任务 run_delegated_dag（30 分钟软超时；Gate 通过后打包工作区为 ZIP）
   │  └─ tasks/agent_task.py        单个 Agent 执行步骤：单轮 agent 走 AgentRunner，
   │                                 配对 agent（backend/frontend/doc/diagram）走 ConversationGraph 多轮循环
   ▼ 调用
packages/py/agents
   │  Runner: Registry → ContextAssembler → PromptBuilder → LangChainProvider → 解析输出 → file_extractor → 工作区文件
   │  ConversationGraph (LangGraph): author 写 → reviewer 评 → author 改，approve 或达轮次上限（默认 3）结束
   ▼
packages/py/runtime_tools
   （LangChain 国产模型接入 chat_model_factory、CostTracker + pricing、Gates + RepairLoop、Exporters/ZipPacker）
   ▼
packages/py/platform_data
   （User/Project/Conversation/WorkspaceFile/ReviewTurn/JobRun/AgentRun/CostLedger/AuditEvent/Artifact 等 ORM 模型）
```

依赖方向：`runtime_tools` 是最底层（外部依赖 redis/langchain-*）；`platform_data` 独立（仅 sqlalchemy/alembic）；`agents` 依赖 `runtime_tools` + `langgraph`；`services/api` 依赖 `platform_data`（+ 运行时依赖 `agents`/`runtime_tools`）；`services/worker` 依赖以上全部（+ 反向 import `services/api` 的 SSE publisher，见下）。

## 数据流（关键路径：全权委托运行）

1. **用户输入想法**：`apps/web` → `POST /api/v1/projects/{id}/generation/analyze`（`services/api/api_app/api/routes/generation.py`）。当前用关键词规则 mock `intent_agent` 输出 `ScopeDraft`，并用 `CapacityCalculator`（`packages/py/agents`）计算容量点数与分档（small/medium/…）。
2. **收缩**（可选）：超预算时 `POST .../generation/contract`，mock `contraction_agent` 按优先级裁剪功能，输出 `ContractionDecision` + 收缩后 `ScopeDraft`。
3. **确认范围**：`POST .../generation/confirm-scope` 锁定 scope。
4. **创建全权委托运行**：`POST /projects/{id}/delegated-runs`（`routes/delegated.py`）→ 校验无并发运行中的 run → 写入 `JobRun`（`platform_data.models.execution`）→ `worker_app.tasks.orchestrate.run_delegated_dag.delay(...)` 触发 Celery 任务。
5. **DAG 编排**（`services/worker`）：`register_all_agents()` 注册 13 个 Agent（9 流水线：intent→contraction→planner→schema→{backend,frontend,doc,diagram}→export + 4 个 reviewer，依赖关系见 `agents/configs/definitions.py`）→ `build_execution_plan()` 按拓扑排序分层（reviewer 不进 DAG）→ 逐层调用 `agent_task._execute_agent_step_async`（同层多 Agent 用 `asyncio.gather` 并行）。单轮 agent 直接跑 `AgentRunner`；backend/frontend/doc/diagram 走 `ConversationGraph`（LangGraph）author↔reviewer 多轮循环，产物文件写入 `workspace_files` 表、轮次记录写入 `conversation_turns` 表，评审事件（`review_round_start`/`review_verdict`）经 Redis 发布到 SSE。
6. **Gate + 修复回路**：全部层完成后，`runtime_tools.gates.repair_loop.RepairLoop` 从 `workspace_files` 加载本 run 的文件跑三道 Gate（后端/前端/Mermaid），失败则重跑相关 Agent（经 agent_task 分发，配对 agent 仍带评审循环）；仍失败则标记 run 为 `needs_attention` 并通过 `api_app.api.sse.publisher.publish_needs_attention` 发 Redis 消息。
7. **实时进度**：`apps/web` 通过 `GET /delegated-runs/{run_id}/events`（SSE，`routes/delegated.py`）订阅 `sse:{run_id}` Redis 频道；评审轮次历史可经 `GET /delegated-runs/{run_id}/turns` 查询。
8. **产物导出与下载**：Gate 通过后 orchestrate 将工作区文件经 `ArtifactCollector` → `ZipPacker` 打包落盘（`data/exports/{run_id}.zip`），`GET /delegated-runs/{run_id}/download` 按 run 状态校验后返回 ZIP（`runtime_tools.exporters.storage.get_zip_path`）。

**次要数据流（聊天式生成）**：`apps/web` 的会话页通过 `POST/GET .../conversations` 与 `chat_orchestrator.ChatOrchestrator` 交互（`api_app/application/services/chat_orchestrator.py`），调用 `agents.analysis`（`cold_start`、`impact_analyzer`、`agent_selector`）执行冷启动或增量 Agent 链，Agent 高层输出经 `upstream_outputs` 逐级传递、产物文件在内存态工作区视图累积，通过 `api/sse/chat_publisher.py` 推送流式变更摘要（SSE），供 `apps/web/src/features/chat/*` 消费。

## 跨切关注点

- **认证**：JWT access + refresh token（`api_app/core/security.py`，`python-jose` + `bcrypt`），`get_current_user` / `get_current_user_sse`（SSE 场景兼容 URL query token，因浏览器 `EventSource` 不支持自定义 Header）。前端 `apps/web/src/lib/api-client` 统一封装 401 自动刷新逻辑。
- **实时推送（SSE）**：所有长流程（DAG 进度、评审轮次、聊天增量）通过 Redis Pub/Sub 频道解耦生产者（worker/API 业务逻辑）与消费者（API 的 SSE 端点），避免 worker 直接持有 HTTP 连接。
- **成本追踪**：`runtime_tools.cost.tracker.CostTracker` 记录每次 LLM 调用成本（`cost/pricing.py` 国产模型静态价格表估算），落库到 `platform_data.models.execution.CostLedger`。
- **质量门禁（双层）**：语义层由配对 reviewer 在生成时即时评审（`conversation_graph` 多轮循环，轮次落库 `conversation_turns`）；客观层由 `runtime_tools.gates`（`backend_gate` / `frontend_gate` / `mermaid_gate` / `classifier` / `repair_loop`）在全部生成完成后做结构/编译级校验，失败自动进入修复回路，仍失败则人工介入（`needs_attention` 状态 + SSE 通知）。
- **AI 协作开发（元层）**：本仓库自身的开发过程由 aiGroup 框架管理（Agent Team 派遣、`.orchestration/` 协作产物、`scripts/hooks` 的 Claude Code hooks 校验、`docs/rules/` 强制规则）。该层不参与 VibeArtifact 运行时，但决定代码如何被 AI 协同产出，详见 `scripts/CLAUDE.md` 与根 `CLAUDE.md`。

## 技术栈选型

| 层级 | 技术 | 选型理由（来自 README / 代码事实） |
|------|------|-----------------------------------|
| 前端 | Next.js 15 (App Router) + React 19 + TypeScript + Tailwind v4 + shadcn/base-ui + Zustand + TanStack Query | SSR/CSR 混合、组件生态成熟；Zustand 管理 auth 状态，TanStack Query 管理服务端状态缓存 |
| API | FastAPI + Python 3.12 + Pydantic v2 | 异步原生、自动 OpenAPI、与 SQLAlchemy 2 异步引擎契合 |
| Worker | Celery 5 + Redis broker/backend | 成熟的分布式任务队列，适合长耗时 DAG 编排（30 分钟软超时） |
| 数据库 | PostgreSQL + SQLAlchemy 2（asyncpg）+ Alembic | 异步 ORM + 版本化迁移；Agent 产物存 workspace_files 表（run 级文件工作区），评审轮次存 conversation_turns |
| 队列/缓存/Pub-Sub | Redis | 一套基础设施同时承担 Celery 队列与 SSE 推送 |
| LLM 接入 | LangChain 原生集成（langchain-deepseek / langchain-moonshot / langchain-openai 兼容模式）| 只接国产模型：DeepSeek、通义千问（DashScope）、Moonshot（Kimi）、MiniMax；`runtime_tools.llm.chat_model_factory` 按 provider 构造 ChatModel，成本经 `cost/pricing.py` 静态价格表估算 |
| 多轮协作引擎 | LangGraph（StateGraph） | author↔reviewer 有界评审循环（`agents.executors.conversation_graph`），在单个 Celery task 内同步跑完，不用 checkpointer——分布式调度仍归 Celery |
| Monorepo 管理 | pnpm workspace（前端）+ uv workspace（Python） | 前后端各自生态原生工具，`pyproject.toml` 根配置统一 `uv sync --all-packages` |
| 生成项目栈（产品输出物） | Next.js + FastAPI + PostgreSQL + Docker Compose | VibeArtifact 默认生成的下游 MVP 技术栈，与平台自身技术栈一致，降低认知负担 |

## 演进路线

| Milestone | 状态 | 说明 |
|-----------|------|------|
| M0 仓库初始化 | 完成 | 项目骨架、Docker Compose、CI |
| M1 数据模型与基础设施 | 完成 | ORM、认证、CRUD、前端页面 |
| M2-M6（历史） | 已重构 | 原 IR Core / Translator / 独立 qa agent 体系已于 2026-07 整体下线，被工作区文件 + LangGraph 评审循环取代 |
| R1 工作区替代 IR | 完成 | workspace_files 表、WorkspaceRepository、Gate/导出改读工作区、ir_core 整包删除 |
| R2 国产模型接入 | 完成 | LangChain 原生集成（DeepSeek/通义/Kimi/MiniMax）、chat_model_factory、静态价格表 |
| R3 多轮评审循环 | 完成 | ConversationGraph（LangGraph）、4 个 reviewer、conversation_turns 落库、评审 SSE 事件 |
| R4 前端跟进 | 待办 | dag-progress.tsx 仍硬编码含 qa 的 8 段流水线，需改造为消费 turns/评审事件；snapshots 统计改为工作区文件统计 |
| R5 真实 LLM 接入 generation 路由 | 待办 | `generation.py` 的 `_mock_analyze` / `_mock_contract` 仍为关键词规则模拟 |

已知技术债 / 待关注点（供后续开发与代码审查参考）：

1. `services/worker/pyproject.toml` 与 `services/api/pyproject.toml` 未显式声明对 `agents` / `runtime_tools`（worker 还 import 了 `api_app`）的依赖，实际运行依赖 uv workspace 共享 `.venv` 中的可编辑安装。跨服务反向 import（worker → `api_app.api.sse.publisher`）耦合了本应独立部署的两个服务。
2. `generation.py` 路由内 `_mock_analyze` / `_mock_contract` 为关键词规则模拟，非真实 LLM 调用。
3. `apps/web` 未见独立的前端单元/组件测试配置，测试策略目前依赖 `next build` + ESLint 作为质量门禁。
4. `routes/snapshots.py` 的 `GET /projects/{id}/snapshots` 为兼容前端保留的废弃 stub（恒返回空列表），前端改造后应删除。
5. `worker_app/orchestrator/run_manager.py` 本地维护一套与 `platform_data` 平行的 ORM 声明（同表两份定义），改动 run 状态机时需两处同步。
