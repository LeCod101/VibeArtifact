"""
Backend Agent 输出契约。

定义 BackendPlan 中每个 FileSpec 的字段约束、
必须包含的文件列表、以及命名和路径规范。
此契约会被注入 PromptBuilder 的 contract 层。
"""

BACKEND_CONTRACT = """## BackendPlan 输出契约

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| files | array[FileSpec] | 是 | 至少 8 个文件，不可为空 |

### FileSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| path | string | 是 | 以 "backend/" 开头，使用正斜杠分隔，不含 ".." |
| content | string | 是 | 非空字符串，包含完整的文件源码 |
| language | string | 是 | 取值: "python" / "dockerfile" / "txt" / "toml" |

### 必须包含的文件

以下文件缺一不可：

1. `backend/main.py` — FastAPI 应用入口
2. `backend/config.py` — 配置管理
3. `backend/database.py` — 数据库连接
4. `backend/requirements.txt` — Python 依赖列表
5. `backend/Dockerfile` — 容器化配置

### 每个实体必须生成的文件

对于 SchemaPlan 中的每个 EntitySpec（名为 X），必须生成：

| 文件路径模式 | 说明 |
|-------------|------|
| `backend/models/{x}.py` | SQLAlchemy ORM 模型（x 为实体名的 snake_case） |
| `backend/schemas/{x}.py` | Pydantic 请求/响应 schema |
| `backend/routes/{xs}.py` | FastAPI 路由（xs 为资源名的 snake_case 复数形式） |
| `backend/services/{x}.py` | CRUD 业务逻辑 service |

### __init__.py 文件

以下目录必须包含 `__init__.py`：
- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- `backend/routes/__init__.py`
- `backend/services/__init__.py`

### path 规范

1. 路径以 "backend/" 开头
2. 使用正斜杠 "/" 分隔
3. 文件名使用 snake_case + 对应扩展名
4. 不允许包含 ".." 或绝对路径

### content 规范

1. Python 文件必须以模块 docstring 开头
2. 所有注释使用中文
3. 禁止尾行注释
4. 代码必须语法正确，可直接运行

### language 取值

| language 值 | 适用文件 |
|-------------|---------|
| python | .py 文件 |
| dockerfile | Dockerfile |
| txt | requirements.txt |
| toml | pyproject.toml（如果使用） |

### 合法性自检

输出前自检：
1. files 列表不为空
2. 每个文件都有 path、content、language 三个字段
3. 所有 path 以 "backend/" 开头
4. 必须包含 main.py、config.py、database.py、requirements.txt、Dockerfile
5. 每个实体都有对应的 model、schema、route、service 文件
6. 每个目录都有 __init__.py
7. content 不为空字符串
8. language 值属于合法集合
9. 无重复 path
"""
