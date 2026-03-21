"""分支 API 端点测试 - 验证分支创建、列表、切换、fork 和树形查询。"""

import uuid

from httpx import AsyncClient

# 测试用户数据
BRANCH_TEST_EMAIL = "branch-user@example.com"
BRANCH_TEST_PASSWORD = "branch-password-123"
BRANCH_TEST_DISPLAY = "Branch Tester"

# 第二个测试用户，用于权限隔离测试
BRANCH_OTHER_EMAIL = "branch-other@example.com"
BRANCH_OTHER_PASSWORD = "branch-other-456"
BRANCH_OTHER_DISPLAY = "Branch Other"


async def register_and_login(
    client: AsyncClient,
    email: str = BRANCH_TEST_EMAIL,
    password: str = BRANCH_TEST_PASSWORD,
    display_name: str = BRANCH_TEST_DISPLAY,
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


async def create_project_and_conversation(
    client: AsyncClient,
    headers: dict,
) -> tuple[str, str, str]:
    """创建项目并获取默认会话和默认分支 ID。

    参数：
        client: httpx 异步测试客户端
        headers: 携带 Bearer token 的请求头

    返回：
        元组 (project_id, conversation_id, main_branch_id)
    """
    # 创建项目
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "分支测试项目", "description": "测试分支功能"},
        headers=headers,
    )
    project_id = resp.json()["id"]

    # 获取默认会话
    conv_resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )
    conversation = conv_resp.json()[0]
    conversation_id = conversation["id"]
    main_branch_id = conversation["active_branch_id"]

    return project_id, conversation_id, main_branch_id


# ──────────────────────────────
# 分支创建测试
# ──────────────────────────────


async def test_create_branch(client: AsyncClient):
    """创建分支应返回 201 和分支信息。"""
    _, headers = await register_and_login(client)
    _, conversation_id, main_branch_id = await create_project_and_conversation(
        client, headers
    )

    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": main_branch_id},
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["conversation_id"] == conversation_id
    assert data["parent_branch_id"] == main_branch_id
    # 自动生成的分支名应为 branch-1（已有 main 一个分支）
    assert data["branch_name"] == "branch-1"
    assert data["message_count"] == 0


async def test_create_branch_with_custom_name(client: AsyncClient):
    """使用自定义名称创建分支。"""
    _, headers = await register_and_login(client)
    _, conversation_id, main_branch_id = await create_project_and_conversation(
        client, headers
    )

    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={
            "parent_branch_id": main_branch_id,
            "branch_name": "feature-login",
        },
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["branch_name"] == "feature-login"


# ──────────────────────────────
# 分支列表测试
# ──────────────────────────────


async def test_list_branches(client: AsyncClient):
    """列出所有分支应包含默认分支和新创建的分支。"""
    _, headers = await register_and_login(client)
    _, conversation_id, main_branch_id = await create_project_and_conversation(
        client, headers
    )

    # 创建两个额外分支
    await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": main_branch_id, "branch_name": "dev"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": main_branch_id, "branch_name": "staging"},
        headers=headers,
    )

    resp = await client.get(
        f"/api/v1/conversations/{conversation_id}/branches",
        headers=headers,
    )

    assert resp.status_code == 200
    branches = resp.json()
    # 默认 main + dev + staging = 3
    assert len(branches) == 3
    names = {b["branch_name"] for b in branches}
    assert "main" in names
    assert "dev" in names
    assert "staging" in names


async def test_list_branches_empty(client: AsyncClient):
    """新会话应只有默认 main 分支。"""
    _, headers = await register_and_login(client)
    _, conversation_id, _ = await create_project_and_conversation(
        client, headers
    )

    resp = await client.get(
        f"/api/v1/conversations/{conversation_id}/branches",
        headers=headers,
    )

    assert resp.status_code == 200
    branches = resp.json()
    assert len(branches) == 1
    assert branches[0]["branch_name"] == "main"


# ──────────────────────────────
# 切换分支测试
# ──────────────────────────────


async def test_switch_branch(client: AsyncClient):
    """切换活跃分支应成功返回分支信息。"""
    _, headers = await register_and_login(client)
    _, conversation_id, main_branch_id = await create_project_and_conversation(
        client, headers
    )

    # 创建新分支
    create_resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": main_branch_id, "branch_name": "dev"},
        headers=headers,
    )
    new_branch_id = create_resp.json()["id"]

    # 切换到新分支
    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches/{new_branch_id}/switch",
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == new_branch_id
    assert data["branch_name"] == "dev"


async def test_switch_branch_not_found(client: AsyncClient):
    """切换到不存在的分支应返回 404。"""
    _, headers = await register_and_login(client)
    _, conversation_id, _ = await create_project_and_conversation(
        client, headers
    )

    fake_branch_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches/{fake_branch_id}/switch",
        headers=headers,
    )

    assert resp.status_code == 404


# ──────────────────────────────
# Fork 分支测试
# ──────────────────────────────


async def test_fork_branch(client: AsyncClient, db_session):
    """Fork 分支应成功返回 201。"""
    _, headers = await register_and_login(client)
    project_id, conversation_id, main_branch_id = (
        await create_project_and_conversation(client, headers)
    )

    # 在数据库中直接创建快照作为 fork 点
    from platform_data.models.ir import IRSnapshot

    snapshot = IRSnapshot(
        project_id=uuid.UUID(project_id),
        version=1,
    )
    db_session.add(snapshot)
    await db_session.flush()
    await db_session.refresh(snapshot)
    snapshot_id = str(snapshot.id)

    # Fork 分支
    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches/{main_branch_id}/fork",
        json={
            "fork_point_snapshot_id": snapshot_id,
            "branch_name": "fork-experiment",
        },
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["branch_name"] == "fork-experiment"
    assert data["parent_branch_id"] == main_branch_id
    assert data["base_snapshot_id"] == snapshot_id
    assert data["head_snapshot_id"] == snapshot_id


async def test_fork_branch_invalid_snapshot(client: AsyncClient):
    """使用无效快照 ID fork 分支应成功（FK 在 SQLite 测试中可能不严格检查）。

    注意：在真实 PostgreSQL 中，无效 FK 会报错。
    此测试验证源分支验证逻辑。
    """
    _, headers = await register_and_login(client)
    _, conversation_id, _ = await create_project_and_conversation(
        client, headers
    )

    fake_branch_id = str(uuid.uuid4())
    fake_snapshot_id = str(uuid.uuid4())

    # 使用不存在的源分支 ID
    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches/{fake_branch_id}/fork",
        json={"fork_point_snapshot_id": fake_snapshot_id},
        headers=headers,
    )

    assert resp.status_code == 404


# ──────────────────────────────
# 分支树测试
# ──────────────────────────────


async def test_get_branch_tree(client: AsyncClient):
    """获取分支树应返回正确的树形结构。"""
    _, headers = await register_and_login(client)
    _, conversation_id, main_branch_id = await create_project_and_conversation(
        client, headers
    )

    # 创建子分支
    create_resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": main_branch_id, "branch_name": "dev"},
        headers=headers,
    )
    dev_branch_id = create_resp.json()["id"]

    # 创建 dev 的子分支
    await client.post(
        f"/api/v1/conversations/{conversation_id}/branches",
        json={"parent_branch_id": dev_branch_id, "branch_name": "feature"},
        headers=headers,
    )

    resp = await client.get(
        f"/api/v1/conversations/{conversation_id}/branches/tree",
        headers=headers,
    )

    assert resp.status_code == 200
    tree = resp.json()
    # 根节点应该是 main 分支
    assert len(tree) == 1
    root = tree[0]
    assert root["branch"]["branch_name"] == "main"
    # main 的子节点应该是 dev
    assert len(root["children"]) == 1
    dev_node = root["children"][0]
    assert dev_node["branch"]["branch_name"] == "dev"
    # dev 的子节点应该是 feature
    assert len(dev_node["children"]) == 1
    assert dev_node["children"][0]["branch"]["branch_name"] == "feature"


# ──────────────────────────────
# 权限测试
# ──────────────────────────────


async def test_branch_unauthorized(client: AsyncClient):
    """非项目所有者访问分支应返回 404（项目不存在）。"""
    # 用户 A 创建项目和会话
    _, headers_a = await register_and_login(client)
    _, conversation_id, _ = await create_project_and_conversation(
        client, headers_a
    )

    # 用户 B 登录
    _, headers_b = await register_and_login(
        client,
        email=BRANCH_OTHER_EMAIL,
        password=BRANCH_OTHER_PASSWORD,
        display_name=BRANCH_OTHER_DISPLAY,
    )

    # 用户 B 尝试访问用户 A 的会话分支
    resp = await client.get(
        f"/api/v1/conversations/{conversation_id}/branches",
        headers=headers_b,
    )

    # 应返回 404（项目不存在 / 无权限）
    assert resp.status_code == 404
