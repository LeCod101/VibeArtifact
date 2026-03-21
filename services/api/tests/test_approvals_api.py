"""审批 API 端点测试 - 验证审批项查询、批准、拒绝、调整等操作。"""

import uuid

from httpx import AsyncClient
from platform_data.models.execution import JobRun, RunStatus
from platform_data.models.ir import IRNode, IRSnapshot

# 测试用户数据
APPROVAL_TEST_EMAIL = "approval-user@example.com"
APPROVAL_TEST_PASSWORD = "approval-password-123"
APPROVAL_TEST_DISPLAY = "Approval Tester"

# 第二个测试用户，用于权限隔离测试
APPROVAL_OTHER_EMAIL = "approval-other@example.com"
APPROVAL_OTHER_PASSWORD = "approval-other-456"
APPROVAL_OTHER_DISPLAY = "Approval Other"


async def register_and_login(
    client: AsyncClient,
    email: str = APPROVAL_TEST_EMAIL,
    password: str = APPROVAL_TEST_PASSWORD,
    display_name: str = APPROVAL_TEST_DISPLAY,
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


async def create_project(
    client: AsyncClient,
    headers: dict,
) -> str:
    """创建项目并返回 project_id。

    参数：
        client: httpx 异步测试客户端
        headers: 携带 Bearer token 的请求头

    返回：
        project_id 字符串
    """
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "审批测试项目", "description": "测试审批功能"},
        headers=headers,
    )
    return resp.json()["id"]


async def create_job_run_and_snapshot(
    db_session,
    project_id: str,
    run_status: RunStatus = RunStatus.waiting_approval,
    add_risks: bool = False,
    add_decisions: bool = False,
) -> tuple[str, str]:
    """在数据库中直接创建 JobRun 和 Snapshot，可选添加风险/决策节点。

    参数：
        db_session: 异步数据库会话
        project_id: 项目 UUID 字符串
        run_status: 运行初始状态
        add_risks: 是否添加高风险节点
        add_decisions: 是否添加待决策节点

    返回：
        元组 (run_id, snapshot_id)
    """
    pid = uuid.UUID(project_id)

    # 创建快照
    snapshot = IRSnapshot(
        project_id=pid,
        version=1,
    )
    db_session.add(snapshot)
    await db_session.flush()
    await db_session.refresh(snapshot)

    # 创建 job_run
    job_run = JobRun(
        project_id=pid,
        snapshot_id=snapshot.id,
        job_type="delegated",
        status=run_status,
    )
    db_session.add(job_run)
    await db_session.flush()
    await db_session.refresh(job_run)

    # 添加高风险节点
    if add_risks:
        risk_node = IRNode(
            snapshot_id=snapshot.id,
            node_type="risk",
            label="高风险：安全隐患",
            props={
                "severity": "high",
                "status": "open",
                "title": "安全隐患",
                "description": "发现潜在安全问题",
                "mitigation": "建议加强验证",
            },
        )
        db_session.add(risk_node)

    # 添加待决策节点
    if add_decisions:
        decision_node = IRNode(
            snapshot_id=snapshot.id,
            node_type="decision",
            label="决策：技术选型",
            props={
                "status": "pending",
                "title": "技术选型",
                "description": "需要决定使用哪个框架",
                "alternatives": ["React", "Vue", "Svelte"],
            },
        )
        db_session.add(decision_node)

    await db_session.flush()

    return str(job_run.id), str(snapshot.id)


# ──────────────────────────────
# 获取待审批项测试
# ──────────────────────────────


async def test_get_pending_approvals_empty(client: AsyncClient, db_session):
    """无待审批项时应返回空列表。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["high_risks"] == []
    assert data["pending_decisions"] == []
    assert data["requires_approval"] is False


async def test_get_pending_approvals_with_risks(client: AsyncClient, db_session):
    """有高风险节点时应返回风险项。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id,
        RunStatus.waiting_approval,
        add_risks=True,
    )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["high_risks"]) == 1
    assert data["high_risks"][0]["severity"] == "high"
    assert data["requires_approval"] is True


async def test_get_pending_approvals_with_decisions(client: AsyncClient, db_session):
    """有待决策节点时应返回决策项。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id,
        RunStatus.waiting_approval,
        add_decisions=True,
    )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["pending_decisions"]) == 1
    assert data["pending_decisions"][0]["status"] == "pending"
    assert data["requires_approval"] is True


# ──────────────────────────────
# 批准运行测试
# ──────────────────────────────


async def test_approve_run(client: AsyncClient, db_session):
    """批准运行应返回成功并更新状态为 completed。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
        json={"reason": "审核通过"},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["action"] == "approve"
    assert data["new_status"] == "completed"


async def test_approve_run_updates_ir(client: AsyncClient, db_session):
    """批准后 risk/decision 节点的 status 应更新为 accepted。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, snapshot_id = await create_job_run_and_snapshot(
        db_session, project_id,
        RunStatus.waiting_approval,
        add_risks=True,
        add_decisions=True,
    )

    # 执行批准
    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
        json={"reason": "全部通过"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 验证 IR 节点状态已更新
    # 再次查询审批项，应该没有 pending 或 open 的节点了
    resp2 = await client.get(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
        headers=headers,
    )

    data = resp2.json()
    assert data["high_risks"] == []
    assert data["pending_decisions"] == []
    assert data["requires_approval"] is False


async def test_approve_run_wrong_status(client: AsyncClient, db_session):
    """非 waiting_approval 状态不能审批，应返回 400。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    # 创建状态为 running 的 run
    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.running,
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
        json={"reason": "尝试审批"},
        headers=headers,
    )

    assert resp.status_code == 400


# ──────────────────────────────
# 拒绝运行测试
# ──────────────────────────────


async def test_reject_run(client: AsyncClient, db_session):
    """拒绝运行应返回成功。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/reject",
        json={"reason": "方案不合适"},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["action"] == "reject"


async def test_reject_run_sets_failed(client: AsyncClient, db_session):
    """拒绝后 run 状态应变为 failed。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/reject",
        json={"reason": "拒绝"},
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["new_status"] == "failed"


# ──────────────────────────────
# 调整运行测试
# ──────────────────────────────


async def test_adjust_run(client: AsyncClient, db_session):
    """调整运行应返回成功并将状态改为 needs_attention。"""
    user_data, headers = await register_and_login(client)
    project_id = await create_project(client, headers)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    resp = await client.post(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/adjust",
        json={
            "feedback": "请修改技术选型为 Vue",
            "reason": "团队更熟悉 Vue",
        },
        headers=headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["action"] == "adjust"
    assert data["new_status"] == "needs_attention"


# ──────────────────────────────
# 权限测试
# ──────────────────────────────


async def test_approval_unauthorized(client: AsyncClient, db_session):
    """非项目所有者访问审批端点应返回 404。"""
    # 用户 A 创建项目
    _, headers_a = await register_and_login(client)
    project_id = await create_project(client, headers_a)

    run_id, _ = await create_job_run_and_snapshot(
        db_session, project_id, RunStatus.waiting_approval,
    )

    # 用户 B 登录
    _, headers_b = await register_and_login(
        client,
        email=APPROVAL_OTHER_EMAIL,
        password=APPROVAL_OTHER_PASSWORD,
        display_name=APPROVAL_OTHER_DISPLAY,
    )

    # 用户 B 尝试访问用户 A 的审批项
    resp = await client.get(
        f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
        headers=headers_b,
    )

    # 应返回 404（项目不存在 / 无权限）
    assert resp.status_code == 404
