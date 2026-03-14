"""
Export Agent 输出契约。

定义 ExportManifest 每个字段的类型、约束、取值范围，
以及 FileEntry 字段约束和 docker_compose_config 必需服务列表。
此契约会被注入 PromptBuilder 的 contract 层。
"""

EXPORT_CONTRACT: str = """## ExportManifest 输出契约

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| reasoning | string | 是 | 打包规划推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 警告信息列表，默认空数组 |
| project_name | string | 是 | kebab-case 格式项目名，只含小写字母、数字和短横线 |
| files | FileEntry[] | 是 | 导出文件列表，不可为空 |
| docker_compose_config | object | 是 | Docker Compose 配置字典，不可为空 |
| env_template | object | 是 | .env.example 键值对字典，不可为空 |

### FileEntry 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| source_type | string | 是 | 取值: "code" / "doc" / "diagram"，必须小写 |
| source_path | string | 是 | 源文件路径，使用正斜杠，不可为空 |
| export_path | string | 是 | 导出目标路径，使用正斜杠，不可为空，不可重复 |

### source_type 取值说明

| 取值 | 含义 | 对应文件类型 |
|------|------|-------------|
| code | 源码文件 | .py / .ts / .tsx / .json / .toml / .txt / Dockerfile / requirements.txt |
| doc | 文档文件 | .md（README.md, docs/*.md） |
| diagram | 图表文件 | .mmd（Mermaid 图表） |

### docker_compose_config 必需服务

Docker Compose 配置中必须包含以下四个服务，缺一不可：

| 服务名 | 基础镜像/构建 | 必需端口 | 依赖 |
|--------|-------------|---------|------|
| backend | build: ./backend | 8000:8000 | postgres, redis |
| frontend | build: ./frontend | 3000:3000 | backend |
| postgres | postgres:16 | 5432:5432 | 无 |
| redis | redis:7-alpine | 6379:6379 | 无 |

### env_template 必需键

| 键名 | 示例值 | 说明 |
|------|--------|------|
| DATABASE_URL | postgresql://user:password@postgres:5432/dbname | PostgreSQL 连接字符串 |
| REDIS_URL | redis://redis:6379/0 | Redis 连接地址 |
| SECRET_KEY | change-me-in-production | 应用密钥 |
| DEBUG | true | 调试模式 |
| POSTGRES_USER | user | 数据库用户 |
| POSTGRES_PASSWORD | change-me | 数据库密码 |
| POSTGRES_DB | dbname | 数据库名称 |

### 合法性检查

输出前自检：
1. project_name 符合 kebab-case 格式
2. files 列表不为空
3. 每个 FileEntry 的 source_type 是合法取值
4. 每个 FileEntry 的 source_path 和 export_path 不为空
5. export_path 没有重复
6. docker_compose_config 包含 backend / frontend / postgres / redis 四个服务
7. env_template 包含所有必需键
8. JSON 格式合法，无多余字段
9. confidence 取值范围 0.0 到 1.0

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- 所有描述性文本使用中文
"""
