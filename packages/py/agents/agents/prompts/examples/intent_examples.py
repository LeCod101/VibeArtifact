"""
Intent Agent Few-Shot 示例。

提供 3 个不同复杂度的示例，帮助 LLM 理解 ScopeDraft 的输出格式和粒度。
- 示例 1: Todo 应用（小型项目，4 个模块）
- 示例 2: 技术博客平台（中型项目，5 个模块）
- 示例 3: 简易电商（中型项目，7 个模块，含 payment/upload）
"""

INTENT_EXAMPLES = """## 示例

### 示例 1

用户输入："做一个任务管理工具"

输出：
{
  "product_name": "效率清单",
  "product_description": "一个面向个人用户的任务管理工具，支持任务创建、分类和进度追踪",
  "scopes": [
    {
      "name": "用户认证",
      "description": "用户注册、登录、退出，基于 JWT 的会话管理",
      "priority": "high",
      "tags": ["auth"]
    },
    {
      "name": "任务管理",
      "description": "任务的创建、编辑、删除、状态变更（待办/进行中/已完成）",
      "priority": "high",
      "tags": ["crud"]
    },
    {
      "name": "任务分类",
      "description": "支持为任务添加标签和分组，按分类筛选任务",
      "priority": "medium",
      "tags": ["crud", "search"]
    },
    {
      "name": "仪表盘",
      "description": "展示任务完成率、近期截止任务等统计概览",
      "priority": "low",
      "tags": ["analytics"]
    }
  ],
  "deferred_items": [
    "团队协作与任务分配",
    "日历视图与提醒通知"
  ],
  "risks": [
    "任务状态机设计需要考虑并发场景"
  ]
}

### 示例 2

用户输入："做一个技术博客平台，支持 Markdown 写作和评论"

输出：
{
  "product_name": "技术笔记",
  "product_description": "一个面向开发者的技术博客平台，支持 Markdown 写作、文章分类和读者评论",
  "scopes": [
    {
      "name": "用户认证",
      "description": "作者和读者的注册、登录，角色区分（作者/读者）",
      "priority": "high",
      "tags": ["auth"]
    },
    {
      "name": "文章管理",
      "description": "文章的创建、编辑、删除、发布/草稿状态切换，支持 Markdown 编辑器",
      "priority": "high",
      "tags": ["crud"]
    },
    {
      "name": "评论系统",
      "description": "读者对文章发表评论，支持楼层回复",
      "priority": "high",
      "tags": ["crud"]
    },
    {
      "name": "分类与标签",
      "description": "文章按技术分类和标签归档，支持按分类浏览",
      "priority": "medium",
      "tags": ["crud", "search"]
    },
    {
      "name": "搜索功能",
      "description": "按标题和内容关键词搜索文章",
      "priority": "medium",
      "tags": ["search"]
    }
  ],
  "deferred_items": [
    "文章点赞与收藏",
    "作者个人主页定制",
    "RSS 订阅"
  ],
  "risks": [
    "Markdown 渲染需要 XSS 防护",
    "评论系统需要防垃圾评论策略"
  ]
}

### 示例 3

用户输入："做一个小型电商，能上架商品、下单支付"

输出：
{
  "product_name": "轻店铺",
  "product_description": "一个面向小型商家的电商平台，支持商品上架、用户下单和在线支付",
  "scopes": [
    {
      "name": "用户认证",
      "description": "买家和商家的注册、登录，角色权限区分",
      "priority": "high",
      "tags": ["auth"]
    },
    {
      "name": "商品管理",
      "description": "商品的上架、编辑、下架，包含商品图片上传和库存管理",
      "priority": "high",
      "tags": ["crud", "upload"]
    },
    {
      "name": "购物车",
      "description": "商品加入购物车、修改数量、删除商品",
      "priority": "high",
      "tags": ["crud"]
    },
    {
      "name": "订单系统",
      "description": "下单、订单状态流转（待支付/已支付/已发货/已完成/已取消）",
      "priority": "high",
      "tags": ["crud"]
    },
    {
      "name": "支付集成",
      "description": "对接第三方支付网关，处理支付回调和退款",
      "priority": "high",
      "tags": ["payment", "integration"]
    },
    {
      "name": "商品搜索",
      "description": "按名称、分类、价格区间搜索和筛选商品",
      "priority": "medium",
      "tags": ["search"]
    },
    {
      "name": "订单通知",
      "description": "订单状态变更时发送站内通知给买家和商家",
      "priority": "low",
      "tags": ["notification"]
    }
  ],
  "deferred_items": [
    "优惠券与促销活动",
    "商品评价与评分",
    "物流追踪集成",
    "数据分析与销售报表"
  ],
  "risks": [
    "支付安全性要求高，需要 HTTPS 和签名验证",
    "库存扣减需要处理并发冲突",
    "支付回调的幂等性处理"
  ]
}
"""
