"""
Contraction Agent 的 Output Contract。

定义 LLM 输出的 JSON 结构约束，用于拼接到 system prompt 中，
确保 LLM 输出的格式能被 ContractionOutput schema 正确解析。
"""

CONTRACTION_CONTRACT: str = """## Output Contract

你的输出必须是一个合法的 JSON 对象，严格遵守以下结构。不要输出任何 JSON 以外的内容。

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reasoning | string | 是 | 收缩推理过程摘要 |
| confidence | number | 是 | 0-1 之间的置信度 |
| warnings | string[] | 否 | 警告信息列表，默认空数组 |
| scope_draft | object | 是 | 收缩后的功能范围草案 |
| decision | object | 是 | 收缩决策详情 |

### scope_draft 结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_name | string | 是 | 产品名称 |
| product_description | string | 是 | 产品描述 |
| scopes | ScopeItem[] | 是 | 保留的功能范围列表 |
| deferred_items | string[] | 否 | 延后功能列表，默认空数组 |
| risks | string[] | 否 | 风险列表，默认空数组 |

### ScopeItem 结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 功能名称 |
| description | string | 是 | 功能描述 |
| priority | string | 是 | 优先级，取值 "high" / "medium" / "low" |
| tags | string[] | 是 | 功能标签列表，至少 1 个标准标签（与 intent_contract 一致） |

### decision 结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| retained_features | string[] | 是 | 保留的功能名称列表 |
| deferred_features | DeferredFeature[] | 是 | 延后的功能列表（含理由） |
| risks | string[] | 是 | 收缩带来的风险描述列表 |
| rationale | string | 是 | 整体收缩理由 |

### DeferredFeature 结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 被延后的功能名称 |
| reason | string | 是 | 延后理由 |

### 示例输出

```json
{
  "reasoning": "输入的 ScopeDraft 总容量 85 点，超出 medium 预算...",
  "confidence": 0.85,
  "warnings": [],
  "scope_draft": {
    "product_name": "示例产品",
    "product_description": "一个示例产品描述",
    "scopes": [
      {
        "name": "用户管理",
        "description": "基础用户注册和登录",
        "priority": "high",
        "tags": ["auth"]
      }
    ],
    "deferred_items": ["支付模块 - Phase 1 栈不支持支付集成"],
    "risks": ["收缩后缺少支付能力，无法验证付费转化假设"]
  },
  "decision": {
    "retained_features": ["用户管理"],
    "deferred_features": [
      {
        "name": "支付模块",
        "reason": "Phase 1 栈支持度：支付集成实现成本极高，延后到 Phase 2"
      }
    ],
    "risks": ["缺少支付能力，无法验证付费转化假设"],
    "rationale": "保留用户管理作为核心价值路径，延后支付等高成本功能，总点数从 85 降至 45"
  }
}
```

### 约束
- 输出必须是单个合法 JSON 对象
- 不要包含注释、markdown 代码块标记或任何非 JSON 文本
- scopes 必须是输入 scopes 的子集，不能添加新功能
- priority 只能取 "high"、"medium"、"low" 三个值
- decision.retained_features 中的名称必须与 scope_draft.scopes 中的 name 一一对应
- confidence 取值范围 0.0 到 1.0
"""
