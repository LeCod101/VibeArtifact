"""
Planner Agent 的 Output Contract。

定义 TaskPlan 每个字段的类型、约束和取值范围，
以及合法 agent_id 列表和 step_id 格式要求。
此契约会被注入 PromptBuilder 的 contract 层。
"""

PLANNER_CONTRACT: str = """## TaskPlan 输出契约

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reasoning | string | 是 | 规划推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 警告信息列表，默认空数组 |
| steps | TaskStep[] | 是 | 任务步骤列表，不可为空 |
| estimated_complexity | string | 是 | 预估复杂度，取值 "small" / "medium" / "large" |

### TaskStep 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| step_id | string | 是 | 格式 "step_<序号>"，从 step_1 开始递增 |
| agent_id | string | 是 | 必须是合法 agent_id（见下方列表） |
| description | string | 是 | 不超过 200 字，结合具体功能模块内容描述 |
| depends_on | string[] | 是 | 依赖的 step_id 列表，可为空数组 |

### 合法 agent_id 列表

| agent_id | 对应 Agent | DAG 层级 |
|----------|-----------|----------|
| schema | 数据建模专家 | 第 1 层 |
| backend | 后端开发专家 | 第 2 层 |
| frontend | 前端开发专家 | 第 2 层 |
| doc | 文档生成专家 | 第 2 层 |
| diagram | 图表生成专家 | 第 2 层 |
| qa | 质量保障专家 | 第 3 层 |
| export | 导出打包专家 | 第 4 层 |

注意：intent、contraction、planner 不是合法的 agent_id，不可出现在 steps 中。

### 标准 DAG 结构

步骤必须严格遵循以下 DAG 结构：

```
step_1 (schema)  →  depends_on: []
step_2 (backend) →  depends_on: ["step_1"]
step_3 (frontend) → depends_on: ["step_1"]
step_4 (doc)     →  depends_on: ["step_1"]
step_5 (diagram) →  depends_on: ["step_1"]
step_6 (qa)      →  depends_on: ["step_2", "step_3", "step_4", "step_5"]
step_7 (export)  →  depends_on: ["step_6"]
```

### 复杂度判断规则

| estimated_complexity | 条件 |
|---------------------|------|
| small | 功能模块 ≤ 3 个，且不含 auth/payment/realtime 标签 |
| medium | 功能模块 4-6 个，或包含 auth 标签 |
| large | 功能模块 > 6 个，或包含 payment/realtime 标签 |

### 合法性检查

输出前自检：
1. steps 列表不为空，且恰好包含 7 个步骤
2. step_id 从 step_1 到 step_7 连续递增
3. 每个 step 的 agent_id 是合法值
4. depends_on 中引用的 step_id 必须存在且编号小于当前步骤
5. 无循环依赖
6. schema 步骤无依赖，qa 依赖所有第 2 层步骤，export 依赖 qa
7. estimated_complexity 取值合法
8. JSON 格式合法，无多余字段
9. confidence 取值范围 0.0 到 1.0

### 示例输出

```json
{
  "reasoning": "项目包含 3 个功能模块（待办管理、分类标签、用户认证），含 auth 标签，判定为 medium 复杂度。按标准 DAG 生成 7 步任务计划。",
  "confidence": 0.9,
  "warnings": [],
  "steps": [
    {
      "step_id": "step_1",
      "agent_id": "schema",
      "description": "设计 User、Todo、Tag 数据实体和 CRUD API 端点",
      "depends_on": []
    },
    {
      "step_id": "step_2",
      "agent_id": "backend",
      "description": "生成 FastAPI 后端代码，实现认证和 CRUD 接口",
      "depends_on": ["step_1"]
    },
    {
      "step_id": "step_3",
      "agent_id": "frontend",
      "description": "生成 Next.js 前端页面和组件",
      "depends_on": ["step_1"]
    },
    {
      "step_id": "step_4",
      "agent_id": "doc",
      "description": "生成 API 文档和快速启动指南",
      "depends_on": ["step_1"]
    },
    {
      "step_id": "step_5",
      "agent_id": "diagram",
      "description": "生成 ER 图和架构流程图",
      "depends_on": ["step_1"]
    },
    {
      "step_id": "step_6",
      "agent_id": "qa",
      "description": "审查所有生成产物的质量",
      "depends_on": ["step_2", "step_3", "step_4", "step_5"]
    },
    {
      "step_id": "step_7",
      "agent_id": "export",
      "description": "打包导出可部署项目",
      "depends_on": ["step_6"]
    }
  ],
  "estimated_complexity": "medium"
}
```

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- steps 必须恰好包含 7 个步骤
- agent_id 顺序固定：schema, backend, frontend, doc, diagram, qa, export
- description 必须结合输入的 ScopeDraft 内容，不可使用泛化模板
"""
