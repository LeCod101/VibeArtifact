# M4 MVP 收缩与容量点数 — 使用指南

## M4 做了什么

M4 实现了 VibeArtifact 的**需求收缩流程**：用户输入一个模糊的产品想法，系统自动分析功能范围、评估复杂度、必要时收缩为 MVP，最终锁定 scope。

**完整流程**：
```
用户输入想法 → 分析（ScopeDraft + 容量评估）→ 收缩（如需）→ 确认 Scope
```

## M4 能做什么 / 不能做什么

| 能做 | 不能做（M5+） |
|------|-------------|
| 接收产品想法，输出结构化功能范围 | 生成实际代码 |
| 计算容量点数，判定 small/medium/large | DAG 编排多 Agent 协作 |
| 超预算时自动收缩功能 | SSE 实时进度推送 |
| 用户确认或微调收缩方案 | ZIP 打包导出 |
| 前端完整交互流程 | 真实 LLM 调用（当前用 mock） |

> **简单说**：M4 解决的是"做什么"的问题（scope 定义），M5 才解决"怎么做"的问题（代码生成）。

## 启动服务

### 1. 基础设施

```bash
# 启动 PostgreSQL + Redis
make dev-infra

# 数据库迁移
cd services/api
uv run alembic upgrade head
```

### 2. 后端 API

```bash
cd services/api
uv run uvicorn api_app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：打开 http://localhost:8000/docs 查看 Swagger 文档，应能看到 `generation` 标签下的 4 个端点。

### 3. 前端

```bash
cd apps/web
pnpm dev
```

打开 http://localhost:3000

## 使用流程

### 前端方式（推荐）

1. 登录后进入 Dashboard
2. 创建一个项目（或选择已有项目）
3. 进入项目后，访问 `/projects/{id}/ideation` 页面
4. 在文本框中输入产品想法，例如：
   - `做一个任务管理工具，支持团队协作和文件上传`
   - `我想做一个博客平台，要有评论功能和标签分类`
   - `做一个简单的电商网站`
5. 点击"分析想法"
6. 查看分析结果：功能模块列表 + 容量仪表盘
7. 如果需要收缩（medium/large），点击"开始收缩"
8. 查看收缩方案，可微调后确认 Scope

### API 方式（curl）

```bash
# 0. 先登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 假设你已有一个项目 ID
PROJECT_ID="你的项目UUID"

# 1. 分析想法
curl -X POST "http://localhost:8000/api/v1/projects/${PROJECT_ID}/generation/analyze" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"user_idea": "做一个任务管理工具，支持团队协作和文件上传"}'
```

**返回示例**：
```json
{
  "scope_draft": {
    "product_name": "任务管理工具",
    "product_description": "一个支持团队协作和文件上传的任务管理系统",
    "scopes": [
      {"name": "用户管理", "description": "用户注册、登录和个人信息管理", "priority": "high", "tags": ["auth"]},
      {"name": "任务管理", "description": "任务的创建、编辑、删除和状态管理", "priority": "high", "tags": ["todo"]},
      {"name": "团队协作", "description": "团队成员的邀请、权限和协作功能", "priority": "medium", "tags": []},
      {"name": "文件上传", "description": "支持文件的上传和管理", "priority": "medium", "tags": ["upload"]},
      {"name": "首页仪表盘", "description": "项目总览和数据统计", "priority": "medium", "tags": []}
    ]
  },
  "capacity_report": {
    "dimensions": [
      {"dimension": "pages", "count": 5, "points": 15},
      {"dimension": "api_endpoints", "count": 10, "points": 20},
      {"dimension": "db_tables", "count": 5, "points": 20},
      {"dimension": "auth_flows", "count": 1, "points": 5},
      {"dimension": "file_upload", "count": 1, "points": 6}
    ],
    "total_points": 66,
    "tier": "large",
    "budget": 60,
    "over_budget": true,
    "needs_contraction": true,
    "must_contract": true
  }
}
```

```bash
# 2. 收缩（如果 tier 是 medium 或 large）
curl -X POST "http://localhost:8000/api/v1/projects/${PROJECT_ID}/generation/contract" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "scope_draft": { ... },
    "capacity_report": { ... }
  }'

# 3. 确认 Scope
curl -X POST "http://localhost:8000/api/v1/projects/${PROJECT_ID}/generation/confirm-scope" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"restore_features": [], "defer_features": []}'
```

## 容量点数体系

### 维度与点数

| 维度 | 单位 | 每单位点数 | Phase 1 上限 |
|------|------|-----------|-------------|
| 页面数 | 每页 | 3 pts | 8 页 (24 pts) |
| API 端点 | 每端点 | 2 pts | 15 端点 (30 pts) |
| 数据表 | 每表 | 4 pts | 6 表 (24 pts) |
| 认证流程 | 每种 | 5 pts | 2 种 (10 pts) |
| 第三方集成 | 每个 | 8 pts | 2 个 (16 pts) |
| 文件上传 | 有/无 | 6 pts | 1 (6 pts) |
| 实时功能 | 有/无 | 10 pts | 1 (10 pts) |
| 支付功能 | — | — | Phase 1 不支持 |

### 分档规则

| 档位 | 点数 | 行为 |
|------|------|------|
| **Small** | 0-30 | 直接通过，无需收缩 |
| **Medium** | 31-60 | 建议收缩，用户可跳过 |
| **Large** | 61+ | 必须收缩才能继续 |

### 试试这些输入

| 输入想法 | 预期档位 | 是否需要收缩 |
|---------|---------|-------------|
| `做一个 Todo 清单` | Small (~22 pts) | 不需要 |
| `做一个博客平台，支持评论和标签` | Medium (~40 pts) | 建议收缩 |
| `做一个电商网站，支持支付、实时聊天和文件上传` | Large (~80 pts) | 必须收缩 |

## 当前限制（Mock 模式）

M4 的分析和收缩使用**关键词匹配 + 规则模拟**，不是真实 LLM：

- 分析：根据输入中的关键词（todo/博客/电商/聊天 等）匹配预设模块模板
- 收缩：按优先级排序，低优先级先裁剪，直到点数在预算内
- 输出是确定性的（相同输入 → 相同输出）

M5 将替换为真实 LLM 调用，届时：
- 分析结果更智能，能理解复杂需求
- 收缩决策考虑业务依赖关系
- 输出具有多样性

## API 端点速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/projects/{id}/generation/analyze` | 分析想法 → ScopeDraft + 容量报告 |
| POST | `/api/v1/projects/{id}/generation/contract` | 收缩功能范围 |
| POST | `/api/v1/projects/{id}/generation/confirm-scope` | 确认并锁定 Scope |
| GET | `/api/v1/projects/{id}/generation/capacity` | 查询容量报告（占位） |
