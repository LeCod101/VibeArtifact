"""认证端点测试 - 验证注册、登录、令牌刷新和用户信息获取。"""

from httpx import AsyncClient

# 测试用户数据
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "strong-password-123"
TEST_DISPLAY_NAME = "Test User"


async def register_user(client: AsyncClient) -> dict:
    """注册测试用户并返回响应 JSON。

    参数：
        client: httpx 异步测试客户端

    返回：
        注册接口返回的 JSON 字典
    """
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "display_name": TEST_DISPLAY_NAME,
        },
    )
    return resp


async def login_user(client: AsyncClient) -> dict:
    """登录测试用户并返回响应 JSON。

    参数：
        client: httpx 异步测试客户端

    返回：
        登录接口返回的 JSON 字典（包含 access_token 和 refresh_token）
    """
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    return resp


async def register_and_login(client: AsyncClient) -> dict:
    """先注册再登录，返回登录响应的 JSON。

    参数：
        client: httpx 异步测试客户端

    返回：
        登录接口返回的 JSON 字典
    """
    await register_user(client)
    resp = await login_user(client)
    return resp.json()


async def test_register(client: AsyncClient):
    """注册新用户应返回 201 和用户信息。"""
    resp = await register_user(client)

    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == TEST_EMAIL
    assert data["display_name"] == TEST_DISPLAY_NAME
    assert data["status"] == "active"
    # 应包含 id 和 created_at 字段
    assert "id" in data
    assert "created_at" in data


async def test_register_duplicate_email(client: AsyncClient):
    """重复邮箱注册应返回 409。"""
    # 先注册一次
    await register_user(client)
    # 再用同一邮箱注册
    resp = await register_user(client)

    assert resp.status_code == 409


async def test_login(client: AsyncClient):
    """正确邮箱密码登录应返回 200 和令牌对。"""
    # 先注册
    await register_user(client)
    # 再登录
    resp = await login_user(client)

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    """错误密码登录应返回 401。"""
    # 先注册
    await register_user(client)
    # 用错误密码登录
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "wrong-password",
        },
    )

    assert resp.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    """不存在的邮箱登录应返回 401。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "any-password",
        },
    )

    assert resp.status_code == 401


async def test_get_me(client: AsyncClient):
    """携带有效 Bearer token 请求 /users/me 应返回 200 和当前用户信息。"""
    tokens = await register_and_login(client)
    access_token = tokens["access_token"]

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_EMAIL
    assert data["display_name"] == TEST_DISPLAY_NAME


async def test_get_me_no_token(client: AsyncClient):
    """不携带 token 请求 /users/me 应返回 401。"""
    resp = await client.get("/api/v1/users/me")

    assert resp.status_code == 401


async def test_refresh(client: AsyncClient):
    """使用有效 refresh_token 刷新应返回 200 和新的 access_token。"""
    tokens = await register_and_login(client)
    refresh_token = tokens["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    # refresh_token 应保持不变
    assert data["refresh_token"] == refresh_token


async def test_refresh_with_access_token(client: AsyncClient):
    """使用 access_token 做刷新应返回 401（类型不匹配）。"""
    tokens = await register_and_login(client)
    access_token = tokens["access_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert resp.status_code == 401
