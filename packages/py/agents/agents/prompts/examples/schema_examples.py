"""
Schema Agent Few-Shot 示例。

提供 2 个不同复杂度的示例，帮助 LLM 理解 SchemaPlan 的输出格式和粒度。
- 示例 1: Todo 应用（简单）：User + Todo 两个实体，CRUD 端点
- 示例 2: 博客应用（中等）：User + Post + Comment 三个实体，含关联关系
"""

# noqa: E501 — few-shot 示例中的 JSON 行长度受限于真实 JSON 格式

SCHEMA_EXAMPLES = (  # noqa: E501
    """## 示例

### 示例 1（简单 —— Todo 应用）

输入（ScopeDraft 功能模块摘要）：
产品名称：效率清单
功能模块：
- 用户认证（tags: auth）：用户注册、登录、退出
- 任务管理（tags: crud）：任务的创建、编辑、删除、状态变更

输出：
{
  "entities": [
    {
      "name": "User",
      "fields": [
        {
          "name": "id", "type": "UUID",
          "primary": true, "nullable": false,
          "unique": true, "default": "uuid4"
        },
        {
          "name": "username", "type": "String",
          "primary": false, "nullable": false,
          "unique": true, "default": null
        },
        {
          "name": "email", "type": "String",
          "primary": false, "nullable": false,
          "unique": true, "default": null
        },
        {
          "name": "password_hash", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "is_active", "type": "Boolean",
          "primary": false, "nullable": false,
          "unique": false, "default": "true"
        },
        {
          "name": "created_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        },
        {
          "name": "updated_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        }
      ],
      "relationships": ["has_many Todo"]
    },
    {
      "name": "Todo",
      "fields": [
        {
          "name": "id", "type": "UUID",
          "primary": true, "nullable": false,
          "unique": true, "default": "uuid4"
        },
        {
          "name": "title", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "description", "type": "Text",
          "primary": false, "nullable": true,
          "unique": false, "default": null
        },
        {
          "name": "status", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": "pending"
        },
        {
          "name": "user_id", "type": "UUID",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "created_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        },
        {
          "name": "updated_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        }
      ],
      "relationships": ["belongs_to User"]
    }
  ],
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/auth/register",
      "description": "用户注册",
      "request_schema": "UserRegister",
      "response_schema": "UserResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/auth/login",
      "description": "用户登录",
      "request_schema": "UserLogin",
      "response_schema": "TokenResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/auth/logout",
      "description": "用户登出",
      "request_schema": null,
      "response_schema": null,
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/auth/me",
      "description": "获取当前用户信息",
      "request_schema": null,
      "response_schema": "UserResponse",
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/todos",
      "description": "获取当前用户的任务列表",
      "request_schema": null,
      "response_schema": "TodoListResponse",
      "auth_required": true
    },
    {
      "method": "POST",
      "path": "/api/todos",
      "description": "创建新任务",
      "request_schema": "TodoCreate",
      "response_schema": "TodoResponse",
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/todos/{id}",
      "description": "获取单个任务详情",
      "request_schema": null,
      "response_schema": "TodoResponse",
      "auth_required": true
    },
    {
      "method": "PUT",
      "path": "/api/todos/{id}",
      "description": "更新任务信息",
      "request_schema": "TodoUpdate",
      "response_schema": "TodoResponse",
      "auth_required": true
    },
    {
      "method": "DELETE",
      "path": "/api/todos/{id}",
      "description": "删除任务",
      "request_schema": null,
      "response_schema": null,
      "auth_required": true
    }
  ]
}

### 示例 2（中等 —— 博客应用）

输入（ScopeDraft 功能模块摘要）：
产品名称：技术笔记
功能模块：
- 用户认证（tags: auth）：作者和读者的注册、登录，角色区分
- 文章管理（tags: crud）：文章的创建、编辑、删除、发布/草稿切换
- 评论系统（tags: crud）：读者对文章发表评论，支持楼层回复

输出：
{
  "entities": [
    {
      "name": "User",
      "fields": [
        {
          "name": "id", "type": "UUID",
          "primary": true, "nullable": false,
          "unique": true, "default": "uuid4"
        },
        {
          "name": "username", "type": "String",
          "primary": false, "nullable": false,
          "unique": true, "default": null
        },
        {
          "name": "email", "type": "String",
          "primary": false, "nullable": false,
          "unique": true, "default": null
        },
        {
          "name": "password_hash", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "role", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": "reader"
        },
        {
          "name": "bio", "type": "Text",
          "primary": false, "nullable": true,
          "unique": false, "default": null
        },
        {
          "name": "is_active", "type": "Boolean",
          "primary": false, "nullable": false,
          "unique": false, "default": "true"
        },
        {
          "name": "created_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        },
        {
          "name": "updated_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        }
      ],
      "relationships": ["has_many Post", "has_many Comment"]
    },
    {
      "name": "Post",
      "fields": [
        {
          "name": "id", "type": "UUID",
          "primary": true, "nullable": false,
          "unique": true, "default": "uuid4"
        },
        {
          "name": "title", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "content", "type": "Text",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "status", "type": "String",
          "primary": false, "nullable": false,
          "unique": false, "default": "draft"
        },
        {
          "name": "author_id", "type": "UUID",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "created_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        },
        {
          "name": "updated_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        }
      ],
      "relationships": ["belongs_to User", "has_many Comment"]
    },
    {
      "name": "Comment",
      "fields": [
        {
          "name": "id", "type": "UUID",
          "primary": true, "nullable": false,
          "unique": true, "default": "uuid4"
        },
        {
          "name": "content", "type": "Text",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "post_id", "type": "UUID",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "author_id", "type": "UUID",
          "primary": false, "nullable": false,
          "unique": false, "default": null
        },
        {
          "name": "parent_id", "type": "UUID",
          "primary": false, "nullable": true,
          "unique": false, "default": null
        },
        {
          "name": "created_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        },
        {
          "name": "updated_at", "type": "DateTime",
          "primary": false, "nullable": false,
          "unique": false, "default": "now"
        }
      ],
      "relationships": [
        "belongs_to Post",
        "belongs_to User",
        "belongs_to Comment"
      ]
    }
  ],
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/auth/register",
      "description": "用户注册",
      "request_schema": "UserRegister",
      "response_schema": "UserResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/auth/login",
      "description": "用户登录",
      "request_schema": "UserLogin",
      "response_schema": "TokenResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/auth/logout",
      "description": "用户登出",
      "request_schema": null,
      "response_schema": null,
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/auth/me",
      "description": "获取当前用户信息",
      "request_schema": null,
      "response_schema": "UserResponse",
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/posts",
      "description": "获取文章列表",
      "request_schema": null,
      "response_schema": "PostListResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/posts",
      "description": "创建新文章",
      "request_schema": "PostCreate",
      "response_schema": "PostResponse",
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/posts/{id}",
      "description": "获取单篇文章详情",
      "request_schema": null,
      "response_schema": "PostResponse",
      "auth_required": false
    },
    {
      "method": "PUT",
      "path": "/api/posts/{id}",
      "description": "更新文章内容",
      "request_schema": "PostUpdate",
      "response_schema": "PostResponse",
      "auth_required": true
    },
    {
      "method": "DELETE",
      "path": "/api/posts/{id}",
      "description": "删除文章",
      "request_schema": null,
      "response_schema": null,
      "auth_required": true
    },
    {
      "method": "GET",
      "path": "/api/posts/{post_id}/comments",
      "description": "获取文章的评论列表",
      "request_schema": null,
      "response_schema": "CommentListResponse",
      "auth_required": false
    },
    {
      "method": "POST",
      "path": "/api/posts/{post_id}/comments",
      "description": "对文章发表评论",
      "request_schema": "CommentCreate",
      "response_schema": "CommentResponse",
      "auth_required": true
    },
    {
      "method": "PUT",
      "path": "/api/comments/{id}",
      "description": "更新评论内容",
      "request_schema": "CommentUpdate",
      "response_schema": "CommentResponse",
      "auth_required": true
    },
    {
      "method": "DELETE",
      "path": "/api/comments/{id}",
      "description": "删除评论",
      "request_schema": null,
      "response_schema": null,
      "auth_required": true
    }
  ]
}
"""
)
