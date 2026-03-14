"""
Intent Agent 输出契约。

定义 ScopeDraft 每个字段的类型、约束、取值范围，
以及 tags 标准标签列表和优先级分配指南。
此契约会被注入 PromptBuilder 的 contract 层。
"""

INTENT_CONTRACT = """## ScopeDraft 输出契约

### 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| product_name | string | 是 | 2-6 个中文字符，不含特殊符号 |
| product_description | string | 是 | 不超过 50 字，一句话概括 |
| scopes | array[ScopeItem] | 是 | 3-8 个元素，不可为空 |
| deferred_items | array[string] | 否 | 每项不超过 20 字 |
| risks | array[string] | 否 | 每项不超过 30 字 |

### ScopeItem 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| name | string | 是 | 2-8 个中文字符，模块级命名 |
| description | string | 是 | 不超过 50 字，说明该模块做什么 |
| priority | enum | 是 | 取值: "high" / "medium" / "low" |
| tags | array[string] | 是 | 至少 1 个标签，从标准标签中选取 |

### 标准技术标签（用于容量计算）

| 标签 | 含义 | 容量影响 |
|------|------|----------|
| auth | 认证/授权/用户系统 | 涉及密码加密、JWT、权限控制 |
| crud | 标准增删改查 | 基础数据操作，容量消耗最低 |
| upload | 文件/图片上传 | 涉及存储服务、文件处理 |
| payment | 支付/交易 | 涉及支付网关、订单状态机 |
| realtime | 实时通信 | 涉及 WebSocket/SSE，架构复杂度高 |
| integration | 第三方服务集成 | 涉及外部 API 调用、错误重试 |
| search | 搜索/过滤/排序 | 可能涉及全文索引 |
| notification | 通知/消息推送 | 涉及异步任务队列 |
| analytics | 数据统计/报表 | 涉及聚合查询、可视化 |
| export | 数据导出/下载 | 涉及批量处理、文件生成 |

### 优先级分配指南

- **high（核心）**：
  - 产品的主要价值承载模块
  - 缺了这个功能用户无法完成核心流程
  - 一般占 scopes 总数的 30%-50%

- **medium（重要）**：
  - 提升用户体验的辅助功能
  - 没有也能用，但有了明显更好
  - 一般占 scopes 总数的 30%-40%

- **low（次要）**：
  - 锦上添花的功能
  - 可以在后续版本迭代
  - 一般占 scopes 总数的 10%-30%

### 合法性检查

输出前自检：
1. product_name 不为空
2. scopes 列表不为空且元素在 3-8 个之间
3. 每个 ScopeItem 的 tags 至少包含一个标准标签
4. 至少有一个 priority 为 "high" 的模块
5. JSON 格式合法，无多余字段
"""
