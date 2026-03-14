"""
Diagram Agent 输出契约。

定义 DiagramPlan 每个字段的类型、约束和取值范围，
以及合法的图表类型列表和 Mermaid 语法要求。
此契约会被注入 PromptBuilder 的 contract 层。
"""

DIAGRAM_CONTRACT: str = """## DiagramPlan 输出契约

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| reasoning | string | 是 | 图表规划推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 警告信息列表，默认空数组 |
| diagrams | DiagramSpec[] | 是 | 图表定义列表，至少 2 个 |

### DiagramSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| title | string | 是 | 图表标题（中文），不超过 30 字 |
| diagram_type | string | 是 | 图表类型，取值见下方"合法图表类型" |
| mermaid_code | string | 是 | Mermaid 语法代码，不可为空 |

### 合法图表类型

| diagram_type | 说明 | Mermaid 语法起始 |
|--------------|------|-----------------|
| er | ER 关系图 | erDiagram |
| flowchart | 流程图/架构图 | graph 或 flowchart |
| sequence | 序列图/时序图 | sequenceDiagram |
| classDiagram | 类图 | classDiagram |

### 必须包含的图表

| 序号 | diagram_type | 说明 |
|------|-------------|------|
| 1 | er | 数据模型 ER 图，覆盖所有实体和关联关系 |
| 2 | flowchart | 系统架构图，展示前端/后端/数据库/缓存的架构 |

第 3 个图表（序列图）为可选，如果 scopes 包含 auth 标签则建议生成。

### ER 图内容要求

1. 每个实体列出 id（PK）和核心业务字段（3-6 个）
2. 不需要列出 created_at、updated_at 等通用字段
3. 外键字段标记为 FK
4. 实体间关系使用正确的 Mermaid ER 语法：
   - ||--o{ : 一对多
   - ||--|| : 一对一
   - }o--o{ : 多对多

### 架构图内容要求

1. 必须包含以下组件：Next.js 前端、FastAPI 后端、PostgreSQL 数据库
2. 如果 scopes 中有需要缓存的场景，包含 Redis
3. 箭头标签说明数据流类型（HTTP 请求、ORM 查询、缓存读写等）
4. 使用 graph LR（从左到右）方向

### 序列图内容要求（如果生成）

1. 参与者至少包含：用户、前端、API、数据库
2. 使用 ->>（实线箭头）表示请求，-->>（虚线箭头）表示响应
3. 展示完整的请求-响应流程

### Mermaid 语法合法性检查

1. ER 图必须以 "erDiagram" 开头
2. 架构图必须以 "graph" 或 "flowchart" 开头
3. 序列图必须以 "sequenceDiagram" 开头
4. 不要在 Mermaid 代码中使用 ```mermaid``` 代码块标记
5. 标识符使用英文字母、数字、下划线，避免特殊字符

### 合法性检查

输出前自检：
1. diagrams 列表至少包含 2 个图表
2. 必须包含 er 类型和 flowchart 类型
3. 每个图表的 title 不为空
4. 每个图表的 diagram_type 是合法值
5. 每个图表的 mermaid_code 不为空，且语法起始正确
6. ER 图覆盖 SchemaPlan 中所有实体
7. JSON 格式合法，无多余字段
8. confidence 取值范围 0.0 到 1.0

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- mermaid_code 中的换行使用 \\n 转义
- 图表标签和描述使用中文，实体名和字段名使用英文
"""
