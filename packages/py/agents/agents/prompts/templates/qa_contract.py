"""
QA Agent 输出契约。

定义 QAReport 每个字段的类型、约束、取值范围，
以及 IssueSpec 的字段约束和严重度分级标准。
此契约会被注入 PromptBuilder 的 contract 层。
"""

QA_CONTRACT: str = """## QAReport 输出契约

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| reasoning | string | 是 | 检查推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 翻译器警告信息列表，默认空数组 |
| passed | boolean | 是 | true=无 critical 问题，false=存在 critical 问题 |
| issues | IssueSpec[] | 是 | 发现的问题列表，无问题时为空数组 |
| summary | string | 是 | 检查结果中文摘要，不超过 100 字 |

### IssueSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| severity | string | 是 | 取值: "critical" / "warning" / "info"，必须小写 |
| category | string | 是 | 取值: "missing_file" / "schema_mismatch" / "import_error" / "config_error" |
| description | string | 是 | 中文描述，不超过 80 字 |
| affected_file | string | 是 | 受影响的文件路径，使用正斜杠，相对于项目根目录 |

### severity 取值说明

| 取值 | 含义 | 判定标准 |
|------|------|----------|
| critical | 严重问题 | 必需文件缺失、必需服务配置缺失 |
| warning | 警告 | 文档缺失、Schema 可能不一致、可选文件缺失 |
| info | 信息 | 可优化的建议，非必须 |

### category 取值说明

| 取值 | 含义 | 检查内容 |
|------|------|----------|
| missing_file | 文件缺失 | 必需的代码文件、配置文件、文档文件不存在 |
| schema_mismatch | Schema 不一致 | SchemaPlan 中的实体/端点与代码文件不匹配 |
| import_error | 导入错误 | 文件间引用路径不正确 |
| config_error | 配置错误 | Docker Compose 或环境变量配置有误 |

### passed 判定规则

1. 如果 issues 中存在任何 severity="critical" 的问题，passed 必须为 false
2. 如果 issues 中只有 "warning" 和 "info" 级别的问题，passed 为 true
3. 如果 issues 为空数组，passed 必须为 true

### 合法性检查

输出前自检：
1. passed 布尔值与 issues 中的 critical 数量一致
2. 每个 issue 的 severity 是合法取值
3. 每个 issue 的 category 是合法取值
4. 每个 issue 的 description 不为空
5. 每个 issue 的 affected_file 不为空
6. summary 不为空
7. JSON 格式合法，无多余字段
8. confidence 取值范围 0.0 到 1.0

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- 所有描述性文本使用中文
"""
