# VibeArtifact MVP 实施计划

> **目标：跑通「生成 → 预览 → 迭代 → 导出」闭环，对标 Anything.com 核心体验**
>
> 文档版本：v1.1 | 日期：2026-04-15 | 预估总周期：4.5 周
>
> **进度追踪**：Phase 1.1 ✅ → Phase 1.2 ✅ → Phase 1.3 ⏳ → Phase 1.4 ⏳ → Phase 2 ⏳ → Phase 3 ⏳

---

## 1. 现状评估

### 1.1 已实现模块

基于对 VibeArtifact 代码仓库的全面审计，当前实现状态如下：

| 模块 | 完成度 | 关键文件 | 说明 |
|------|--------|---------|------|
| 用户认证 | 95% | `services/api/.../routes/auth.py` | JWT 注册/登录/刷新 |
| 项目管理 | 95% | `services/api/.../routes/projects.py` | CRUD + 状态管理 |
| 对话系统 | 90% | `services/api/.../routes/chat.py` | SSE 流式、多轮对话、历史记录 |
| AI Agent | 85% | `packages/py/agents/agents/agent.py` | 单 Agent + Tool Loop + 多模式 |
| Agent 工具集 | 85% | `packages/py/agents/agents/tools/` | 13+ 工具（代码/文档/图表/项目/SQL） |
| Artifact 版本管理 | 90% | `platform_data/models/artifact.py` | 版本链、parent_id 追溯 |
| 项目导出 | 80% | `services/worker/.../export_project.py` | Celery 异步 ZIP 导出 |
| LLM 多模型 | 100% | `runtime_tools/llm/provider.py` | LiteLLM 8+ 模型（DeepSeek/GLM/Claude/GPT） |
| 成本追踪 | 90% | `runtime_tools/cost/tracker.py` | 按调用记录费用 |
| 并发控制 | 100% | `runtime_tools/locks/lease_lock.py` | Redis Lease Lock |
| 数据库 | 100% | `platform_data/models/` | 9 个 ORM 模型，Alembic 迁移 |
| 前端 UI | 80% | `apps/web/src/` | Dashboard、工作区、对话、Artifact 面板 |
| 模板系统 | 80% | `services/api/.../routes/templates.py` | 项目模板种子数据 |
| 用户设置 | 85% | `services/api/.../routes/settings.py` | 模型偏好、API Key 加密存储 |

### 1.2 对标 Anything.com 的关键缺口

参考 `restructure.md` 中对 Anything.com 的架构分析，以及 2026 年 Anything.com 的最新产品能力：

| Anything.com 能力 | VibeArtifact 状态 | 差距等级 |
|-------------------|------------------|---------|
| 自然语言生成全栈应用 | 有 Agent + 工具，但未端到端验证 | 中 |
| **实时预览生成的应用** | **完全缺失** | **致命** |
| 对话式迭代修改 | 已实现（chat + edit_file） | 小 |
| Anything Max（自主 QA） | 完全缺失 | 大（MVP 后） |
| **一键部署到自定义域名** | **完全缺失** | **大** |
| 原生移动端输出 | 完全缺失 | 大（MVP 后） |
| 100+ 第三方集成 | 完全缺失 | 大（MVP 后） |
| 内置 Auth/支付/存储 | 可生成代码但无运行时 | 中 |
| 多模型智能路由 | 有基础，路由策略简单 | 小 |
| 团队协作 | 完全缺失 | 大（MVP 后） |
| 积分计费系统 | 有 CostTracker，无面向用户计费 | 中（MVP 后） |

### 1.3 核心判断

当前系统的**后端 API、数据库、Agent 框架、导出管线**都已就绪。

最大的断裂点：

```
用户输入想法 → AI 生成代码 → ???（看不到效果）→ 导出 ZIP
                              ↑
                         这里是致命缺口
```

用户无法在平台内看到生成结果的运行效果，这使得整个产品停留在「代码片段生成器」层面，而非「产品工程 OS」。

---

## 2. MVP 定义

### 2.1 MVP 用户故事

> 作为一个计算机专业的大学生，我希望：
> 1. 用一句话描述我要做的课程作业（如「用 React 做一个 Todo 应用」）
> 2. AI 帮我生成完整的前端代码
> 3. **在浏览器里直接看到应用运行效果**
> 4. 通过对话继续修改（「把按钮颜色改成蓝色」「加一个删除功能」）
> 5. **每次修改后立刻看到更新效果**
> 6. 满意后导出完整项目 ZIP，解压就能跑

### 2.2 MVP 范围界定

**MVP 包含（Must Have）：**
- 前端应用实时预览（iframe 沙箱 + WebContainer）
- 端到端生成流程打通（一句话 → 可运行项目）
- 导出增强（ZIP 解压即跑）

**MVP 不包含（Phase 4+）：**
- 云端一键部署（Vercel/Railway）
- 自主 QA Agent（Anything Max）
- 原生移动端输出
- 第三方集成市场
- 团队协作
- 积分/订阅计费
- 后端代码在线运行

### 2.3 技术栈约束

遵循 `restructure.md` 的原则，**基础设施和技术选型保持不变**：

| 层级 | 技术 | 不变 |
|------|------|------|
| 平台前端 | Next.js 15 + React + TypeScript | ✅ |
| 平台 API | FastAPI + Python 3.12 | ✅ |
| 平台 Worker | Celery + Python 3.12 | ✅ |
| 数据库 | PostgreSQL + SQLAlchemy 2 + Alembic | ✅ |
| 缓存/队列 | Redis | ✅ |
| 新增：预览运行时 | WebContainer API（浏览器端） | 🆕 |

---

## 3. 分阶段实施计划

### Phase 1：实时预览（最高优先级）

**目标**：用户在对话中让 AI 生成代码后，右侧面板能实时看到运行效果。

**预估周期**：2 周

#### 1.1 基础 iframe 沙箱（第 1 周前半）✅ 已完成

**目标**：纯 HTML/CSS/JS 的 Artifact 可直接在 iframe 中渲染。

**完成日期**：2026-04-15

**交付物**：

| 文件 | 状态 | 说明 |
|------|------|------|
| 新建 `apps/web/src/features/artifact/components/preview-iframe.tsx` | ✅ | 373 行，支持 HTML/CSS/JS/JSX/TSX 预览，sandbox 安全隔离 |
| 修改 `apps/web/src/features/artifact/components/artifact-panel.tsx` | ✅ | 新增「代码/预览」Tab 切换，仅 code 类型显示 |

**实现细节**：
- `buildPreviewHtml()` 按语言类型构建可渲染 HTML
- HTML：直接 `srcdoc` 渲染
- CSS：带示例元素展示样式效果
- JS/TS：含 console 输出捕获显示
- JSX/TSX：React 18 UMD + Babel standalone 浏览器编译
- `sandbox="allow-scripts allow-modals"` 安全隔离
- TypeScript 编译零错误验证通过

#### 1.2 WebContainer 集成（第 1 周后半 ~ 第 2 周前半）✅ 已完成

**目标**：支持 React/Next.js 项目的在线预览。

**完成日期**：2026-04-15

**交付物**：

| 文件 | 状态 | 说明 |
|------|------|------|
| 新建 `apps/web/src/features/preview/use-webcontainer.ts` | ✅ | 单例 WebContainer hook，动态 import SSR 安全 |
| 新建 `apps/web/src/features/preview/file-system-bridge.ts` | ✅ | Artifact → FileSystemTree 转换，自动补全 package.json/index.html/vite.config/main.tsx |
| 新建 `apps/web/src/features/preview/preview-panel.tsx` | ✅ | 完整预览面板（状态指示+iframe+可折叠终端），支持增量文件更新+Vite HMR |
| 修改 `services/api/.../routes/artifacts.py` | ✅ | 新增 `GET /projects/{id}/artifacts/code-files` 端点 |
| 修改 `apps/web/src/features/artifact/api.ts` | ✅ | 新增 `useCodeArtifactsQuery` hook |
| 修改 `apps/web/src/features/artifact/components/artifact-panel.tsx` | ✅ | 多文件时切换到 PreviewPanel |
| 修改 `apps/web/src/app/(dashboard)/project/[id]/page.tsx` | ✅ | 传入 codeArtifacts 数据 |
| 修改 `apps/web/next.config.ts` | ✅ | 项目页面 COOP/COEP headers（WebContainer 必需） |
| 新增依赖 `@webcontainer/api` | ✅ | pnpm add |

**实现细节**：
- 单例 WebContainer 全局只 boot 一次（模块级缓存）
- `buildFileSystemTree()` 按 file_path 递归构建目录，智能补全脚手架
- `extractImportedPackages()` 扫描 import 语句自动填充依赖
- 增量更新：artifacts 指纹变化时 mount 新文件树，Vite HMR 自动刷新
- 6 级状态指示：idle/booting/installing/starting/running/error
- 终端面板限制 500 行日志，自动滚到底

#### 1.3 多文件项目组装（第 2 周前半）

**目标**：Agent 生成的多个 Artifact 能自动组装为可运行项目。

**后端改动**：

| 文件 | 改动内容 |
|------|---------|
| 新建 `packages/py/agents/agents/tools/scaffold_tools.py` | 新增 `create_scaffold` 工具，生成项目骨架（package.json / tsconfig / vite.config 等） |
| `packages/py/agents/agents/system_prompt.py` | System Prompt 增加脚手架生成规范（确保文件路径正确、依赖声明完整） |

**工具设计**：
```python
@tool
async def create_scaffold(
    project_type: str,  # "react" | "nextjs" | "html" | "vue"
    project_name: str,
    dependencies: list[str],  # ["react", "react-dom", "tailwindcss"]
) -> dict:
    """生成项目骨架配置文件（package.json, tsconfig, etc）。
    
    Agent 在生成业务代码前先调用此工具，确保项目结构完整。
    """
```

#### 1.4 预览热更新（第 2 周后半）

**目标**：用户通过对话修改代码后，预览自动刷新。

**实现方案**：
```
用户发消息「把按钮改成蓝色」
       │
       ▼
Agent 调用 edit_file 工具 → 创建新版本 Artifact
       │
       ▼
SSE 事件 tool_result 包含 artifact_id
       │
       ▼
前端监听到 Artifact 更新
       │
       ▼
file-system-bridge 计算 diff → WebContainer 增量更新文件
       │
       ▼
Vite HMR 自动生效 → iframe 预览刷新
```

#### Phase 1 交付验收标准

- [x] 纯 HTML/CSS/JS Artifact 点击「预览」可在右侧 iframe 运行 ✅ (1.1)
- [x] JSX/TSX 单文件可通过 Babel standalone 编译预览 ✅ (1.1)
- [x] React 项目（3+ 文件）可通过 WebContainer 启动并预览 ✅ (1.2)
- [ ] 用户通过对话修改代码后，预览在 3 秒内自动刷新 (1.4)
- [x] 预览面板有明确的状态指示（6 级：idle/booting/installing/starting/running/error）✅ (1.2)
- [x] 构建错误在终端面板中可见 ✅ (1.2)

---

### Phase 2：端到端生成流程打磨

**目标**：一句话生成完整可运行项目，而不是逐个文件。

**预估周期**：1.5 周

#### 2.1 批量生成任务联调（第 3 周前半）

**现状**：`services/worker/worker_app/tasks/batch_generate.py` 已有 5 步流程框架，但未经端到端验证。

| 文件 | 改动内容 |
|------|---------|
| `services/worker/worker_app/tasks/batch_generate.py` | 联调验证 5 步流程（需求分析→架构→数据库→代码→文档），确保 Agent 正确调用工具 |
| `services/api/.../routes/projects.py` | 新增 `POST /projects/{id}/generate` 端点，触发批量生成 |
| `apps/web/src/features/project/components/create-project-form.tsx` | 创建项目后自动触发生成流程 |

**5 步流程验证清单**：

```
Step 1: 需求分析
  └── Agent 输出需求文档 Artifact（create_document）
  
Step 2: 架构设计
  └── Agent 输出架构图 Artifact（create_diagram）
  
Step 3: 数据库设计
  └── Agent 输出 SQL Artifact（create_sql）
  
Step 4: 代码生成
  ├── Agent 先调用 create_scaffold（项目骨架）
  └── Agent 逐个调用 create_file（业务代码）
  
Step 5: API 文档
  └── Agent 输出 API 文档 Artifact（create_document）
```

#### 2.2 项目脚手架增强（第 3 周后半）

**目标**：AI 生成的文件具有正确的目录结构，形成可运行工程。

| 文件 | 改动内容 |
|------|---------|
| `packages/py/agents/agents/system_prompt.py` | 增加脚手架规范：文件路径必须完整（如 `src/App.tsx` 而非 `App.tsx`）、配置文件必须齐全 |
| `packages/py/agents/agents/tools/scaffold_tools.py` | 完善模板：React（Vite）、Next.js、纯 HTML 三种项目类型 |

**脚手架模板（React + Vite 示例）**：
```
project-name/
├── package.json          ← create_scaffold 自动生成
├── vite.config.ts        ← create_scaffold 自动生成
├── tsconfig.json         ← create_scaffold 自动生成
├── index.html            ← create_scaffold 自动生成
├── src/
│   ├── main.tsx          ← create_scaffold 自动生成
│   ├── App.tsx           ← Agent create_file
│   ├── App.css           ← Agent create_file
│   └── components/
│       └── TodoList.tsx  ← Agent create_file
└── public/               ← create_scaffold 自动生成
```

#### 2.3 智能模型路由（第 4 周前半）

**目标**：推理任务用强模型，生成任务用快模型，平衡质量与速度。

| 文件 | 改动内容 |
|------|---------|
| `packages/py/agents/agents/modes.py` | 扩展 ModeConfig，batch_generate 各步骤配置不同模型偏好 |

**路由策略**：
```
Step 1 需求分析 → reasoning_model（需要理解力）
Step 2 架构设计 → reasoning_model（需要推理力）
Step 3 数据库   → generation_model（模式化生成）
Step 4 代码生成 → generation_model（批量生成）
Step 5 API 文档 → generation_model（模式化生成）
```

#### 2.4 错误恢复机制（第 4 周前半）

**目标**：单步失败不导致整体失败。

| 文件 | 改动内容 |
|------|---------|
| `services/worker/worker_app/tasks/batch_generate.py` | 增加单步 retry（最多 2 次）、失败跳过（标记 skip）、进度上报 |
| `packages/py/agents/agents/agent.py` | `_MAX_TOOL_ROUNDS` 超限时返回已有结果而非空 |

#### Phase 2 交付验收标准

- [ ] 创建项目后一键触发生成，5 步流程完整执行
- [ ] 生成的 React 项目文件结构正确，package.json 依赖完整
- [ ] 生成完成后自动触发 Phase 1 的预览流程
- [ ] 单步失败可自动重试，不中断整体流程
- [ ] 前端展示生成进度（Step 1/5、Step 2/5...）

---

### Phase 3：导出增强

**目标**：导出的 ZIP 是开箱即用的，解压后一条命令就能跑。

**预估周期**：1 周

#### 3.1 导出模板优化（第 4 周后半）

| 文件 | 改动内容 |
|------|---------|
| `packages/py/runtime_tools/runtime_tools/exporters/compose_gen.py` | 按项目类型生成不同的 Dockerfile 和启动配置 |
| `packages/py/runtime_tools/runtime_tools/exporters/collector.py` | 确保收集器按 file_path 正确组织文件 |
| `packages/py/runtime_tools/runtime_tools/exporters/zip_packer.py` | 增加 README.md 和启动脚本到 ZIP 包 |

**导出 ZIP 结构**：
```
my-project.zip
├── README.md               ← 自动生成，包含项目说明和启动步骤
├── start.sh                ← 一键启动脚本
├── start.bat               ← Windows 启动脚本
├── package.json
├── src/
│   └── ...                 ← 所有代码 Artifact
├── docs/
│   ├── 需求文档.md          ← 文档 Artifact
│   ├── 架构图.mmd           ← 图表 Artifact
│   └── 数据库设计.sql       ← SQL Artifact
└── docker-compose.yml      ← 如需数据库则包含
```

#### 3.2 一键启动脚本（第 5 周前半）

**start.sh 逻辑**：
```bash
#!/bin/bash
# 检测 Node.js 是否安装
# npm install
# npm run dev
# 输出访问地址
```

#### 3.3 导出进度反馈（第 5 周前半）

| 文件 | 改动内容 |
|------|---------|
| `services/api/.../routes/exports.py` | 增加 `GET /exports/{id}/status` 轮询端点 |
| `apps/web/src/app/(dashboard)/project/[id]/export/page.tsx` | 展示导出进度和下载按钮 |

#### Phase 3 交付验收标准

- [ ] 导出 ZIP 包含 README + 启动脚本 + 所有代码/文档/SQL
- [ ] React 项目解压后 `npm install && npm run dev` 可直接运行
- [ ] 含数据库的项目解压后 `docker compose up` 可运行
- [ ] 导出过程有进度反馈
- [ ] ZIP 文件大小合理（< 5MB）

---

## 4. 总体时间线

```
Week 1              Week 2              Week 3              Week 4              Week 5(前半)
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬──────────┐
│ Phase 1         │ Phase 1         │ Phase 2         │ Phase 2 + 3     │ Phase 3  │
│                 │                 │                 │                 │          │
│ 1.1 iframe沙箱  │ 1.3 多文件组装   │ 2.1 批量生成联调│ 2.3 模型路由     │ 3.3 进度 │
│ 1.2 WebContainer│ 1.4 热更新       │ 2.2 脚手架增强  │ 2.4 错误恢复     │ 反馈     │
│                 │                 │                 │ 3.1 导出模板     │          │
│                 │                 │                 │ 3.2 启动脚本     │          │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴──────────┘

里程碑:
  M1 (Week 2 末): HTML/React 项目可在浏览器内预览
  M2 (Week 3 末): 一句话生成完整可运行项目
  M3 (Week 5 前半): 导出 ZIP 解压即跑
```

---

## 5. 技术风险与应对

| 风险 | 影响 | 概率 | 应对方案 |
|------|------|------|---------|
| WebContainer 兼容性问题 | Phase 1 延期 | 中 | 降级方案：用 CodeSandbox SDK 替代；最差情况保留纯 HTML 预览 |
| Agent 生成代码质量不稳定 | Phase 2 延期 | 高 | System Prompt 增加代码规范约束 + 脚手架模板兜底基本结构 |
| 大项目预览性能问题 | 用户体验下降 | 中 | 限制 MVP 项目规模（< 20 文件）；按需加载文件 |
| LLM API 调用延迟/失败 | 全流程 | 中 | 已有 LiteLLM 多模型兜底；batch_generate 增加单步重试 |
| WebContainer npm install 慢 | 预览体验差 | 高 | 预置常用依赖缓存；使用 pnpm 加速；显示进度条缓解等待焦虑 |

---

## 6. MVP 后路线图（Phase 4+）

以下功能不在本次 MVP 范围内，但列出作为后续规划参考：

| Phase | 功能 | 优先级 | 说明 |
|-------|------|--------|------|
| 4 | 云端一键部署 | P1 | 集成 Vercel/Railway API，一键上线到真实域名 |
| 5 | 自主 QA Agent（Max 模式） | P1 | 给 Agent 增加「浏览器自动化」和「运行测试」工具 |
| 6 | 后端沙箱运行时 | P2 | Docker 沙箱运行 Python/Java 后端代码 |
| 7 | 第三方集成框架 | P2 | 先做 Stripe + Auth 模板，逐步扩展 |
| 8 | 团队协作 | P3 | 多人实时编辑、权限管理 |
| 9 | 移动端代码生成 | P3 | React Native / Flutter 输出 |
| 10 | 积分/订阅计费 | P3 | 面向用户的计费系统 |

---

## 7. 派遣计划

基于团队分工（Max 协调、Ella 设计、Jarvis 开发、Kyle 验收）：

| Phase | 成员 | 职责 |
|-------|------|------|
| Phase 1 | **Jarvis** | 前端 iframe/WebContainer 组件开发、后端 file-tree API |
| Phase 1 | **Ella** | 预览面板 UI/UX 设计（布局、状态指示、错误展示） |
| Phase 2 | **Jarvis** | 后端批量生成联调、脚手架工具、模型路由 |
| Phase 3 | **Jarvis** | 导出模板优化、启动脚本生成 |
| 全程 | **Kyle** | 每个 Phase 结束做功能验收 + 代码审查 |
| 全程 | **Max** | 进度跟踪、风险预警、产物审查 |
