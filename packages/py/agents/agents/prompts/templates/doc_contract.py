"""
Doc Agent 输出契约。

定义 DocPlan 每个字段的类型、约束、取值范围，
以及 README 必备章节列表和 API 文档格式要求。
此契约会被注入 PromptBuilder 的 contract 层。
"""

DOC_CONTRACT: str = """## DocPlan 输出契约

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| reasoning | string | 是 | 文档规划推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 警告信息列表，默认空数组 |
| files | FileSpec[] | 是 | 文档文件列表，不可为空，至少包含 2 个文件 |

### FileSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| path | string | 是 | 文件路径，使用正斜杠，相对于项目根目录 |
| content | string | 是 | 文件完整内容（Markdown 格式），不可为空 |
| language | string | 是 | 固定为 "markdown" |

### 必须包含的文件

| 序号 | path | 说明 |
|------|------|------|
| 1 | README.md | 项目入口文档 |
| 2 | docs/api.md | API 详细文档 |

### README.md 必备章节

README.md 的 content 必须包含以下 6 个一级/二级标题章节，缺一不可：

1. **项目概述** — 产品名称、一句话描述、核心功能要点
2. **技术栈** — 列出 FastAPI、SQLAlchemy 2、Next.js 15、PostgreSQL 16、Redis、Docker
3. **环境要求** — Python 3.12、Node 20、PostgreSQL 16、Redis
4. **快速启动** — docker-compose up 一键启动步骤（含 clone、环境变量配置、启动命令）
5. **API 概览** — 按功能模块分组，列出每个端点的方法、路径和简述
6. **项目结构** — 目录树说明（backend/、frontend/、docs/ 等）

### docs/api.md 格式要求

每个 API 端点必须包含以下信息：

```markdown
## METHOD /api/path

功能描述文字

**认证要求**：需要 / 不需要

**请求参数**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ... | ... | ... | ... |

**响应体**：
```json
{ ... }
```

**curl 示例**：
```bash
curl -X METHOD http://localhost:8000/api/path ...
```
```

### curl 示例规则

1. 所有端点必须有 curl 示例
2. POST/PUT/PATCH 请求必须包含 -H "Content-Type: application/json" 和 -d 请求体
3. 需要认证的端点必须包含 -H "Authorization: Bearer <token>"
4. 基础 URL 使用 http://localhost:8000

### 合法性检查

输出前自检：
1. files 列表不为空，且至少包含 README.md 和 docs/api.md
2. 每个 file 的 path 不为空、content 不为空
3. language 固定为 "markdown"
4. README.md 包含 6 个必备章节
5. docs/api.md 覆盖 SchemaPlan 中所有端点
6. 每个端点有 curl 示例
7. POST/PUT 端点的 curl 示例包含请求体
8. JSON 格式合法，无多余字段
9. confidence 取值范围 0.0 到 1.0

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- content 中的换行使用 \\n 转义
- 文档使用中文编写，代码和命令除外
"""
