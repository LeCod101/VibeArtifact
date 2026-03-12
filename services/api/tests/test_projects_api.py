"""项目与对话端点测试 - 验证项目 CRUD、对话创建和消息保存。"""

import uuid

from httpx import AsyncClient

# 测试用户数据（使用独立邮箱前缀，避免与 test_auth_api 冲突）
PROJECT_TEST_EMAIL = "proj-user@example.com"
PROJECT_TEST_PASSWORD = "strong-password-123"
PROJECT_TEST_DISPLAY = "Project Tester"

# 第二个测试用户，用于跨用户隔离测试
OTHER_EMAIL = "other-user@example.com"
OTHER_PASSWORD = "other-password-456"
OTHER_DISPLAY = "Other User"


async def register_and_login(
    client: AsyncClient,
    email: str = PROJECT_TEST_EMAIL,
    password: str = PROJECT_TEST_PASSWORD,
    display_name: str = PROJECT_TEST_DISPLAY,
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
    # 注册
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    user_data = reg_resp.json()

    # 登录
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    return user_data, headers


async def create_project(
    client: AsyncClient,
    headers: dict,
    name: str = "测试项目",
    description: str = "测试描述",
) -> dict:
    """创建项目并返回响应 JSON。

    参数：
        client: httpx 异步测试客户端
        headers: 携带 Bearer token 的请求头
        name: 项目名称
        description: 项目描述

    返回：
        创建项目接口返回的 JSON 字典
    """
    resp = await client.post(
        "/api/v1/projects",
        json={"name": name, "description": description},
        headers=headers,
    )
    return resp


# ──────────────────────────────
# 项目端点测试
# ──────────────────────────────


async def test_create_project(client: AsyncClient):
    """创建项目应返回 201 和项目信息。"""
    _, headers = await register_and_login(client)

    resp = await create_project(client, headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "测试项目"
    assert data["description"] == "测试描述"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data


async def test_list_projects(client: AsyncClient):
    """查询项目列表应只返回当前用户的项目。"""
    # 用户 A 创建项目
    _, headers_a = await register_and_login(client)
    await create_project(client, headers_a, name="A 的项目")

    # 用户 B 创建项目
    _, headers_b = await register_and_login(
        client,
        email=OTHER_EMAIL,
        password=OTHER_PASSWORD,
        display_name=OTHER_DISPLAY,
    )
    await create_project(client, headers_b, name="B 的项目")

    # 用户 A 查询列表，应该只能看到自己的项目
    resp = await client.get("/api/v1/projects", headers=headers_a)

    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "A 的项目"


async def test_get_project(client: AsyncClient):
    """根据 ID 查询项目详情应返回 200。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{project_id}", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == project_id
    assert data["name"] == "测试项目"


async def test_get_project_not_found(client: AsyncClient):
    """查询不存在的项目 ID 应返回 404。"""
    _, headers = await register_and_login(client)
    fake_id = str(uuid.uuid4())

    resp = await client.get(f"/api/v1/projects/{fake_id}", headers=headers)

    assert resp.status_code == 404


async def test_get_project_other_user(client: AsyncClient):
    """查询其他用户的项目应返回 404（防止信息泄露）。"""
    # 用户 A 创建项目
    _, headers_a = await register_and_login(client)
    create_resp = await create_project(client, headers_a)
    project_id = create_resp.json()["id"]

    # 用户 B 尝试访问
    _, headers_b = await register_and_login(
        client,
        email=OTHER_EMAIL,
        password=OTHER_PASSWORD,
        display_name=OTHER_DISPLAY,
    )

    resp = await client.get(f"/api/v1/projects/{project_id}", headers=headers_b)

    assert resp.status_code == 404


# ──────────────────────────────
# 对话端点测试
# ──────────────────────────────


async def test_create_conversation(client: AsyncClient):
    """为项目创建新对话应返回 201。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/conversations",
        json={"title": "新对话"},
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "新对话"
    assert data["project_id"] == project_id
    assert data["mode"] == "chat"
    assert data["status"] == "active"
    # 自动创建了默认分支，active_branch_id 不为空
    assert data["active_branch_id"] is not None


async def test_list_conversations(client: AsyncClient):
    """查询项目对话列表应返回该项目下的所有对话。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    # 创建项目时已自动创建 1 个默认对话，再手动创建 1 个
    await client.post(
        f"/api/v1/projects/{project_id}/conversations",
        json={"title": "手动创建的对话"},
        headers=headers,
    )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )

    assert resp.status_code == 200
    conversations = resp.json()
    # 默认对话 + 手动创建的对话 = 2
    assert len(conversations) == 2


# ──────────────────────────────
# 消息端点测试
# ──────────────────────────────


async def test_save_message(client: AsyncClient):
    """保存消息到对话应返回 201。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    # 获取默认对话
    conv_resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )
    conversation_id = conv_resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "你好"},
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "user"
    assert data["content"] == "你好"
    assert data["conversation_id"] == conversation_id
    assert data["content_type"] == "text"


async def test_list_messages(client: AsyncClient):
    """查询对话消息列表应返回该对话的消息。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    # 获取默认对话
    conv_resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )
    conversation_id = conv_resp.json()[0]["id"]

    # 保存两条消息
    await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"role": "user", "content": "第一条"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"role": "assistant", "content": "第二条"},
        headers=headers,
    )

    resp = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
    )

    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2


# ──────────────────────────────
# 创建项目自动初始化测试
# ──────────────────────────────


async def test_create_project_auto_init(client: AsyncClient):
    """创建项目后应自动创建默认对话（带活跃分支）。"""
    _, headers = await register_and_login(client)
    create_resp = await create_project(client, headers)
    project_id = create_resp.json()["id"]

    # 查询对话列表，应有 1 个自动创建的默认对话
    resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )

    assert resp.status_code == 200
    conversations = resp.json()
    assert len(conversations) == 1

    # 默认对话应有标题 "默认对话"、chat 模式、且有活跃分支
    default_conv = conversations[0]
    assert default_conv["title"] == "默认对话"
    assert default_conv["mode"] == "chat"
    assert default_conv["active_branch_id"] is not None
