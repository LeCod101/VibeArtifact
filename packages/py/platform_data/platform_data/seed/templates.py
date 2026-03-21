"""预置模板种子数据 - 提供系统内置的项目模板定义。

包含 Todo SaaS、Blog Platform、REST API Service 三个预置模板，
每个模板包含完整的 IR 节点和边定义。
"""

PRESET_TEMPLATES = [
    {
        "name": "Todo SaaS",
        "description": "待办事项 SaaS 应用 — 包含用户认证、任务 CRUD、标签分类",
        "category": "saas",
        "icon": "✅",
        "snapshot_data": {
            "nodes": [
                {
                    "node_type": "scope",
                    "label": "Todo SaaS MVP",
                    "props": {
                        "description": "待办事项管理应用，支持用户注册登录、创建/编辑/删除待办、标签分类等功能",
                    },
                },
                {
                    "node_type": "entity",
                    "label": "User",
                    "props": {"fields": ["id", "email", "password_hash"]},
                },
                {
                    "node_type": "entity",
                    "label": "Todo",
                    "props": {"fields": ["id", "title", "completed", "user_id"]},
                },
                {
                    "node_type": "entity",
                    "label": "Tag",
                    "props": {"fields": ["id", "name", "color"]},
                },
                {
                    "node_type": "endpoint",
                    "label": "POST /auth/register",
                    "props": {"method": "POST", "path": "/auth/register"},
                },
                {
                    "node_type": "endpoint",
                    "label": "POST /auth/login",
                    "props": {"method": "POST", "path": "/auth/login"},
                },
                {
                    "node_type": "endpoint",
                    "label": "GET /todos",
                    "props": {"method": "GET", "path": "/todos"},
                },
                {
                    "node_type": "endpoint",
                    "label": "POST /todos",
                    "props": {"method": "POST", "path": "/todos"},
                },
                {
                    "node_type": "ui_page",
                    "label": "登录页",
                    "props": {"route": "/login"},
                },
                {
                    "node_type": "ui_page",
                    "label": "仪表盘",
                    "props": {"route": "/dashboard"},
                },
            ],
            "edges": [
                {"source": "User", "target": "Todo", "edge_type": "has_many"},
                {"source": "Todo", "target": "Tag", "edge_type": "has_many"},
            ],
        },
    },
    {
        "name": "Blog Platform",
        "description": "博客平台 — 包含文章发布、分类管理、评论系统",
        "category": "saas",
        "icon": "📝",
        "snapshot_data": {
            "nodes": [
                {
                    "node_type": "scope",
                    "label": "Blog Platform MVP",
                    "props": {
                        "description": "博客发布平台，支持文章发布、分类管理、评论互动等功能",
                    },
                },
                {
                    "node_type": "entity",
                    "label": "Author",
                    "props": {"fields": ["id", "name", "bio"]},
                },
                {
                    "node_type": "entity",
                    "label": "Post",
                    "props": {"fields": ["id", "title", "content", "published_at"]},
                },
                {
                    "node_type": "entity",
                    "label": "Category",
                    "props": {"fields": ["id", "name", "slug"]},
                },
                {
                    "node_type": "entity",
                    "label": "Comment",
                    "props": {"fields": ["id", "content", "post_id"]},
                },
                {
                    "node_type": "endpoint",
                    "label": "GET /posts",
                    "props": {"method": "GET", "path": "/posts"},
                },
                {
                    "node_type": "endpoint",
                    "label": "POST /posts",
                    "props": {"method": "POST", "path": "/posts"},
                },
                {
                    "node_type": "ui_page",
                    "label": "文章列表",
                    "props": {"route": "/posts"},
                },
                {
                    "node_type": "ui_page",
                    "label": "文章详情",
                    "props": {"route": "/posts/:id"},
                },
            ],
            "edges": [
                {"source": "Author", "target": "Post", "edge_type": "has_many"},
                {"source": "Post", "target": "Comment", "edge_type": "has_many"},
                {"source": "Post", "target": "Category", "edge_type": "belongs_to"},
            ],
        },
    },
    {
        "name": "REST API Service",
        "description": "REST API 服务 — 包含认证、CRUD、分页、错误处理",
        "category": "api",
        "icon": "🔌",
        "snapshot_data": {
            "nodes": [
                {
                    "node_type": "scope",
                    "label": "REST API Service",
                    "props": {
                        "description": "通用 REST API 服务骨架，包含资源 CRUD、认证、分页等基础功能",
                    },
                },
                {
                    "node_type": "entity",
                    "label": "Resource",
                    "props": {"fields": ["id", "name", "data", "created_at"]},
                },
                {
                    "node_type": "endpoint",
                    "label": "GET /resources",
                    "props": {"method": "GET", "path": "/resources"},
                },
                {
                    "node_type": "endpoint",
                    "label": "POST /resources",
                    "props": {"method": "POST", "path": "/resources"},
                },
                {
                    "node_type": "endpoint",
                    "label": "GET /resources/:id",
                    "props": {"method": "GET", "path": "/resources/:id"},
                },
                {
                    "node_type": "endpoint",
                    "label": "PUT /resources/:id",
                    "props": {"method": "PUT", "path": "/resources/:id"},
                },
                {
                    "node_type": "endpoint",
                    "label": "DELETE /resources/:id",
                    "props": {"method": "DELETE", "path": "/resources/:id"},
                },
            ],
            "edges": [],
        },
    },
]
