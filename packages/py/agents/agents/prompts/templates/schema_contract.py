"""
Schema Agent 输出契约。

定义 SchemaPlan 每个字段的类型、约束、取值范围，
以及数据类型标准列表和命名规范。
此契约会被注入 PromptBuilder 的 contract 层。
"""

SCHEMA_CONTRACT = """## SchemaPlan 输出契约

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| entities | array[EntitySpec] | 是 | 至少 1 个实体，不可为空 |
| endpoints | array[EndpointSpec] | 是 | 至少 1 个端点，不可为空 |

### EntitySpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| name | string | 是 | PascalCase 命名，如 "User"、"TodoItem" |
| fields | array[FieldSpec] | 是 | 至少 4 个字段（含必备的 id/created_at/updated_at + 至少 1 个业务字段） |
| relationships | array[string] | 否 | 关联关系描述，格式 "belongs_to X" 或 "has_many X"，默认空数组 |

### FieldSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| name | string | 是 | snake_case 命名，如 "user_id"、"is_active" |
| type | string | 是 | 标准类型名称：String / Text / Integer / Float / Boolean / DateTime / UUID / JSON |
| primary | boolean | 否 | 是否为主键，默认 false |
| nullable | boolean | 否 | 是否允许空值，默认 true |
| unique | boolean | 否 | 是否有唯一约束，默认 false |
| default | string 或 null | 否 | 默认值表达式，如 "uuid4"、"now"、"true"、"0"；无默认值填 null |

### EndpointSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| method | string | 是 | 取值: "GET" / "POST" / "PUT" / "DELETE" / "PATCH"，必须大写 |
| path | string | 是 | 以 "/api/" 开头，资源名用复数小写，路径参数用 {param} 格式 |
| description | string | 是 | 中文描述，不超过 30 字 |
| request_schema | string 或 null | 否 | 请求体 schema 名称（PascalCase），GET/DELETE 填 null |
| response_schema | string 或 null | 否 | 响应体 schema 名称（PascalCase） |
| auth_required | boolean | 否 | 是否需要认证，默认 true |

### 标准数据类型（对应 SQLAlchemy 2 类型）

| 类型名 | 用途 | 示例字段 |
|--------|------|----------|
| UUID | 主键、外键 | id, user_id |
| String | 短文本（用户名、标题等） | username, title |
| Text | 长文本（正文、描述等） | content, description |
| Integer | 整数计数 | age, view_count |
| Float | 浮点数 | price, score |
| Boolean | 布尔标记 | is_active, is_published |
| DateTime | 时间戳 | created_at, updated_at |
| JSON | JSON 对象 | metadata, settings |

### 必备字段检查

每个实体必须包含以下 3 个字段，缺一不可：

```json
{"name": "id", "type": "UUID", "primary": true, "nullable": false, "unique": true, "default": "uuid4"}
{"name": "created_at", "type": "DateTime", "primary": false, "nullable": false, "unique": false, "default": "now"}
{"name": "updated_at", "type": "DateTime", "primary": false, "nullable": false, "unique": false, "default": "now"}
```

### 命名规范检查

1. 实体名必须是 PascalCase：首字母大写，多词连写（User, BlogPost, TodoItem）
2. 字段名必须是 snake_case：全小写，下划线分隔（user_id, is_active, created_at）
3. API 路径必须以 "/api/" 开头，资源名用复数小写形式
4. request_schema / response_schema 名称使用 PascalCase（UserCreate, UserResponse）

### 合法性自检

输出前自检：
1. entities 列表不为空
2. endpoints 列表不为空
3. 每个实体都包含 id、created_at、updated_at 字段
4. 每个实体至少有 1 个业务字段（除必备字段外）
5. 每个字段的 type 属于标准类型列表
6. 每个端点的 method 属于 GET/POST/PUT/DELETE/PATCH
7. 每个端点的 path 以 "/api/" 开头
8. 外键字段的 type 为 UUID
9. JSON 格式合法，无多余字段
"""
