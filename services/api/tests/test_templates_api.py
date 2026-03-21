"""模板 API 端点测试 - 验证模板列表、详情和从模板创建项目。"""

import uuid

from httpx import AsyncClient

# 测试用户数据
TPL_TEST_EMAIL = "template-user@example.com"
TPL_TEST_PASSWORD = "template-password-123"
TPL_TEST_DISPLAY = "Template Tester"


async def register_and_login(
    client: AsyncClient,
    email: str = TPL_TEST_EMAIL,
    password: str = TPL_TEST_PASSWORD,
    display_name: str = TPL_TEST_DISPLAY,
) -> tuple[dict, dict]:
    """注册并登录用户，返回 (user_data, auth_headers)。

    参数：
        client: httpx 异步测试客户端
        email: 注册邮箱
        password: 注册密码
        display_name: 显示名

    返回：
        元组 (注册接口返回的用户信息, 带 Bearer token 的请求头字典)
    """
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    user_data = reg_resp.json()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    return user_data, headers


# ──────────────────────────────
# 模板列表测试
# ──────────────────────────────


async def test_list_templates(client: AsyncClient):
    """列出模板应返回预置模板列表（自动 seed）。"""
    resp = await client.get("/api/v1/templates")

    assert resp.status_code == 200
    templates = resp.json()
    # 预置模板有 3 个
    assert len(templates) == 3
    # 验证字段存在
    for tpl in templates:
        assert "id" in tpl
        assert "name" in tpl
        assert "description" in tpl
        assert "category" in tpl
        assert "icon" in tpl
        assert "is_public" in tpl
        assert "created_at" in tpl
        # 列表接口不应返回 snapshot_data
        assert "snapshot_data" not in tpl


async def test_list_templates_by_category(client: AsyncClient):
    """按类别过滤模板应只返回对应类别。"""
    # 先触发 seed
    await client.get("/api/v1/templates")

    # 过滤 saas 类别
    resp = await client.get("/api/v1/templates?category=saas")
    assert resp.status_code == 200
    templates = resp.json()
    # saas 类别有 2 个模板（Todo SaaS 和 Blog Platform）
    assert len(templates) == 2
    for tpl in templates:
        assert tpl["category"] == "saas"

    # 过滤 api 类别
    resp = await client.get("/api/v1/templates?category=api")
    assert resp.status_code == 200
    templates = resp.json()
    # api 类别有 1 个模板
    assert len(templates) == 1
    assert templates[0]["category"] == "api"


# ──────────────────────────────
# 模板详情测试
# ──────────────────────────────


async def test_get_template_detail(client: AsyncClient):
    """获取模板详情应包含 snapshot_data。"""
    # 先获取模板列表
    list_resp = await client.get("/api/v1/templates")
    templates = list_resp.json()
    template_id = templates[0]["id"]

    # 获取详情
    resp = await client.get(f"/api/v1/templates/{template_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["id"] == template_id
    assert "snapshot_data" in detail
    assert "nodes" in detail["snapshot_data"]
    assert "edges" in detail["snapshot_data"]
    # 节点数量应大于 0
    assert len(detail["snapshot_data"]["nodes"]) > 0


async def test_get_template_not_found(client: AsyncClient):
    """获取不存在的模板应返回 404。"""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/templates/{fake_id}")
    assert resp.status_code == 404


# ──────────────────────────────
# 从模板创建项目测试
# ──────────────────────────────


async def test_create_project_from_template(client: AsyncClient):
    """从模板创建项目应返回 201 和项目信息。"""
    _, headers = await register_and_login(client)

    # 获取模板列表
    list_resp = await client.get("/api/v1/templates")
    templates = list_resp.json()
    template_id = templates[0]["id"]

    # 从模板创建项目
    resp = await client.post(
        "/api/v1/projects/from-template",
        json={
            "template_id": template_id,
            "project_name": "我的测试项目",
        },
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert "project_id" in data
    assert "snapshot_id" in data
    assert data["message"] == "项目创建成功"


async def test_create_project_from_template_creates_snapshot(
    client: AsyncClient,
    db_session,
):
    """从模板创建项目应生成 IR 节点和边。"""
    _, headers = await register_and_login(client)

    # 获取模板列表
    list_resp = await client.get("/api/v1/templates")
    templates = list_resp.json()

    # 使用 Todo SaaS 模板（有 10 个节点、2 条边）
    todo_template = None
    for tpl in templates:
        if tpl["name"] == "Todo SaaS":
            todo_template = tpl
            break
    assert todo_template is not None

    # 从模板创建项目
    resp = await client.post(
        "/api/v1/projects/from-template",
        json={
            "template_id": todo_template["id"],
            "project_name": "验证快照项目",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    snapshot_id = data["snapshot_id"]

    # 查询 IR 节点
    from platform_data.models.ir import IREdge, IRNode
    from sqlalchemy import select

    node_result = await db_session.execute(
        select(IRNode).where(
            IRNode.snapshot_id == uuid.UUID(snapshot_id)
        )
    )
    nodes = list(node_result.scalars().all())
    # Todo SaaS 模板有 10 个节点
    assert len(nodes) == 10

    # 查询 IR 边
    edge_result = await db_session.execute(
        select(IREdge).where(
            IREdge.snapshot_id == uuid.UUID(snapshot_id)
        )
    )
    edges = list(edge_result.scalars().all())
    # Todo SaaS 模板有 2 条边
    assert len(edges) == 2


async def test_create_project_from_template_not_found(
    client: AsyncClient,
):
    """使用不存在的模板 ID 创建项目应返回 404。"""
    _, headers = await register_and_login(client)

    fake_template_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/projects/from-template",
        json={
            "template_id": fake_template_id,
            "project_name": "不存在的模板项目",
        },
        headers=headers,
    )

    assert resp.status_code == 404


async def test_create_project_from_template_unauthorized(
    client: AsyncClient,
):
    """未认证用户创建项目应返回 401。"""
    # 先获取一个模板 ID
    list_resp = await client.get("/api/v1/templates")
    templates = list_resp.json()
    template_id = templates[0]["id"]

    # 不带 auth header 调用
    resp = await client.post(
        "/api/v1/projects/from-template",
        json={
            "template_id": template_id,
            "project_name": "未认证项目",
        },
    )

    assert resp.status_code == 401
