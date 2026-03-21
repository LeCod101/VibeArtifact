"""M9 端到端集成测试 - 覆盖审批流程、IR 节点更新、模板创建和边界情况。

测试场景：
- TestApprovalFlow: 审批流程端到端（approve / reject / adjust）
- TestApprovalIRUpdate: approve 后 IR 节点状态验证
- TestTemplateIntegration: 模板创建项目端到端
- TestApprovalEdgeCases: 边界情况（非法状态、重复操作、历史记录）
"""

import uuid

import pytest
from httpx import AsyncClient
from platform_data.models.conversation import Conversation, ConversationBranch
from platform_data.models.execution import JobRun, RunStatus
from platform_data.models.ir import IRNode, IRSnapshot
from sqlalchemy import select

# 测试用户常量
INTEG_EMAIL = "integ-user@example.com"
INTEG_PASSWORD = "integ-password-123"
INTEG_DISPLAY = "Integration Tester"


async def _register_and_login(
    client: AsyncClient,
    email: str = INTEG_EMAIL,
    password: str = INTEG_PASSWORD,
    display_name: str = INTEG_DISPLAY,
) -> tuple[dict, dict]:
    """注册并登录用户，返回 (user_data, auth_headers)。

    参数：
        client: httpx 异步测试客户端
        email: 注册邮箱
        password: 注册密码
        display_name: 显示名

    返回：
        元组 (用户信息, 带 Bearer token 的请求头)
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


async def _create_project(client: AsyncClient, headers: dict) -> str:
    """创建项目并返回 project_id。

    参数：
        client: httpx 异步测试客户端
        headers: 携带 Bearer token 的请求头

    返回：
        project_id 字符串
    """
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "集成测试项目", "description": "端到端集成测试"},
        headers=headers,
    )
    return resp.json()["id"]


async def _create_run_with_nodes(
    db_session,
    project_id: str,
    run_status: RunStatus = RunStatus.waiting_approval,
    add_risks: bool = False,
    add_decisions: bool = False,
) -> tuple[str, str]:
    """在数据库中创建 JobRun + Snapshot，可选添加风险/决策节点。

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
    snapshot = IRSnapshot(project_id=pid, version=1)
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


# ══════════════════════════════════════════════
# TestApprovalFlow - 审批流程端到端
# ══════════════════════════════════════════════


class TestApprovalFlow:
    """审批流程端到端集成测试：approve / reject / adjust 全链路。"""

    @pytest.mark.asyncio
    async def test_full_approval_flow(self, client: AsyncClient, db_session):
        """完整审批流程：创建项目→创建 run→添加 HIGH risk→获取待审批项→approve→验证状态。"""
        user_data, headers = await _register_and_login(client)
        project_id = await _create_project(client, headers)

        # 创建带高风险节点的 waiting_approval run
        run_id, snapshot_id = await _create_run_with_nodes(
            db_session, project_id,
            RunStatus.waiting_approval,
            add_risks=True,
        )

        # 获取待审批项，确认有高风险
        resp_items = await client.get(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
            headers=headers,
        )
        assert resp_items.status_code == 200
        items = resp_items.json()
        assert items["requires_approval"] is True
        assert len(items["high_risks"]) == 1

        # 执行 approve
        resp_approve = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "风险可接受，批准继续"},
            headers=headers,
        )
        assert resp_approve.status_code == 200
        approve_data = resp_approve.json()
        assert approve_data["success"] is True
        assert approve_data["action"] == "approve"
        assert approve_data["new_status"] == "completed"

        # 验证 run 状态更新后，待审批项清空
        resp_after = await client.get(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
            headers=headers,
        )
        assert resp_after.status_code == 200
        after_data = resp_after.json()
        assert after_data["requires_approval"] is False
        assert after_data["high_risks"] == []

    @pytest.mark.asyncio
    async def test_reject_flow(self, client: AsyncClient, db_session):
        """拒绝流程：创建 run→reject→验证 run 状态 failed→验证 ApprovalRecord。"""
        user_data, headers = await _register_and_login(
            client,
            email="reject-flow@example.com",
            password="reject-password-123",
            display_name="Reject Tester",
        )
        project_id = await _create_project(client, headers)

        run_id, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.waiting_approval,
        )

        # 执行 reject
        resp_reject = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/reject",
            json={"reason": "方案不合适，需要重新设计"},
            headers=headers,
        )
        assert resp_reject.status_code == 200
        reject_data = resp_reject.json()
        assert reject_data["success"] is True
        assert reject_data["action"] == "reject"
        assert reject_data["new_status"] == "failed"

        # 验证审批历史记录
        resp_items = await client.get(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approvals",
            headers=headers,
        )
        assert resp_items.status_code == 200
        items = resp_items.json()
        assert len(items["approval_history"]) == 1
        assert items["approval_history"][0]["action"] == "reject"

    @pytest.mark.asyncio
    async def test_adjust_flow(self, client: AsyncClient, db_session):
        """调整流程：创建 run→adjust（带 feedback）→验证状态 needs_attention。"""
        user_data, headers = await _register_and_login(
            client,
            email="adjust-flow@example.com",
            password="adjust-password-123",
            display_name="Adjust Tester",
        )
        project_id = await _create_project(client, headers)

        run_id, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.waiting_approval,
        )

        # 执行 adjust
        resp_adjust = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/adjust",
            json={
                "feedback": "请将后端框架改为 FastAPI",
                "reason": "团队更熟悉 Python 生态",
            },
            headers=headers,
        )
        assert resp_adjust.status_code == 200
        adjust_data = resp_adjust.json()
        assert adjust_data["success"] is True
        assert adjust_data["action"] == "adjust"
        assert adjust_data["new_status"] == "needs_attention"


# ══════════════════════════════════════════════
# TestApprovalIRUpdate - IR 节点更新验证
# ══════════════════════════════════════════════


class TestApprovalIRUpdate:
    """approve 后 IR 中风险/决策节点状态变更验证。"""

    @pytest.mark.asyncio
    async def test_approve_updates_risk_status(self, client: AsyncClient, db_session):
        """approve 后 HIGH risk 节点的 props.status 应变为 accepted。"""
        user_data, headers = await _register_and_login(
            client,
            email="ir-risk@example.com",
            password="ir-risk-password-123",
            display_name="IR Risk Tester",
        )
        project_id = await _create_project(client, headers)

        run_id, snapshot_id = await _create_run_with_nodes(
            db_session, project_id,
            RunStatus.waiting_approval,
            add_risks=True,
        )

        # approve
        resp = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "接受风险"},
            headers=headers,
        )
        assert resp.status_code == 200

        # 直接查询数据库验证 risk 节点状态
        result = await db_session.execute(
            select(IRNode).where(
                IRNode.snapshot_id == uuid.UUID(snapshot_id),
                IRNode.node_type == "risk",
            )
        )
        risk_nodes = list(result.scalars().all())
        assert len(risk_nodes) == 1
        assert risk_nodes[0].props["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_approve_updates_decision_status(self, client: AsyncClient, db_session):
        """approve 后 PENDING decision 节点的 props.status 应变为 accepted。"""
        user_data, headers = await _register_and_login(
            client,
            email="ir-decision@example.com",
            password="ir-decision-password-123",
            display_name="IR Decision Tester",
        )
        project_id = await _create_project(client, headers)

        run_id, snapshot_id = await _create_run_with_nodes(
            db_session, project_id,
            RunStatus.waiting_approval,
            add_decisions=True,
        )

        # approve
        resp = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "决策通过"},
            headers=headers,
        )
        assert resp.status_code == 200

        # 直接查询数据库验证 decision 节点状态
        result = await db_session.execute(
            select(IRNode).where(
                IRNode.snapshot_id == uuid.UUID(snapshot_id),
                IRNode.node_type == "decision",
            )
        )
        decision_nodes = list(result.scalars().all())
        assert len(decision_nodes) == 1
        assert decision_nodes[0].props["status"] == "accepted"


# ══════════════════════════════════════════════
# TestTemplateIntegration - 模板端到端
# ══════════════════════════════════════════════


class TestTemplateIntegration:
    """模板创建项目端到端集成测试。"""

    @pytest.mark.asyncio
    async def test_create_project_from_todo_template(
        self, client: AsyncClient, db_session
    ):
        """从 Todo 模板创建项目→验证项目存在→验证 IR 节点数量正确。"""
        _, headers = await _register_and_login(
            client,
            email="tpl-todo@example.com",
            password="tpl-todo-password-123",
            display_name="Template Todo Tester",
        )

        # 获取模板列表，定位 Todo SaaS 模板
        list_resp = await client.get("/api/v1/templates")
        assert list_resp.status_code == 200
        templates = list_resp.json()

        todo_template = None
        for tpl in templates:
            if tpl["name"] == "Todo SaaS":
                todo_template = tpl
                break
        assert todo_template is not None, "Todo SaaS 模板应存在"

        # 从模板创建项目
        create_resp = await client.post(
            "/api/v1/projects/from-template",
            json={
                "template_id": todo_template["id"],
                "project_name": "集成测试 Todo 项目",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        project_id = data["project_id"]
        snapshot_id = data["snapshot_id"]

        # 验证项目存在
        project_resp = await client.get(
            f"/api/v1/projects/{project_id}",
            headers=headers,
        )
        assert project_resp.status_code == 200

        # 验证 IR 节点数量（Todo SaaS 有 10 个节点）
        node_result = await db_session.execute(
            select(IRNode).where(
                IRNode.snapshot_id == uuid.UUID(snapshot_id)
            )
        )
        nodes = list(node_result.scalars().all())
        assert len(nodes) == 10

    @pytest.mark.asyncio
    async def test_template_creates_conversation(
        self, client: AsyncClient, db_session
    ):
        """从模板创建项目后自动创建默认会话和 main 分支。"""
        _, headers = await _register_and_login(
            client,
            email="tpl-conv@example.com",
            password="tpl-conv-password-123",
            display_name="Template Conv Tester",
        )

        # 获取模板列表
        list_resp = await client.get("/api/v1/templates")
        templates = list_resp.json()
        template_id = templates[0]["id"]

        # 创建项目
        create_resp = await client.post(
            "/api/v1/projects/from-template",
            json={
                "template_id": template_id,
                "project_name": "会话验证项目",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        project_id = uuid.UUID(data["project_id"])

        # 验证默认会话已创建
        conv_result = await db_session.execute(
            select(Conversation).where(
                Conversation.project_id == project_id
            )
        )
        conversations = list(conv_result.scalars().all())
        assert len(conversations) == 1
        assert conversations[0].title == "默认对话"

        # 验证 main 分支已创建
        branch_result = await db_session.execute(
            select(ConversationBranch).where(
                ConversationBranch.conversation_id == conversations[0].id
            )
        )
        branches = list(branch_result.scalars().all())
        assert len(branches) == 1
        assert branches[0].branch_name == "main"


# ══════════════════════════════════════════════
# TestApprovalEdgeCases - 边界情况
# ══════════════════════════════════════════════


class TestApprovalEdgeCases:
    """审批操作边界情况测试。"""

    @pytest.mark.asyncio
    async def test_approve_non_waiting_run(self, client: AsyncClient, db_session):
        """对非 waiting_approval 状态的 run 调用 approve 应返回 400。"""
        user_data, headers = await _register_and_login(
            client,
            email="edge-non-waiting@example.com",
            password="edge-password-123",
            display_name="Edge Tester 1",
        )
        project_id = await _create_project(client, headers)

        # 创建状态为 running 的 run
        run_id, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.running,
        )

        resp = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "尝试审批"},
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_double_approve(self, client: AsyncClient, db_session):
        """同一 run approve 两次，第二次应返回 400（状态已变为 completed）。"""
        user_data, headers = await _register_and_login(
            client,
            email="edge-double@example.com",
            password="edge-double-123",
            display_name="Edge Tester 2",
        )
        project_id = await _create_project(client, headers)

        run_id, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.waiting_approval,
        )

        # 第一次 approve 应成功
        resp1 = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "第一次批准"},
            headers=headers,
        )
        assert resp1.status_code == 200

        # 第二次 approve 应失败（状态已不是 waiting_approval）
        resp2 = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id}/approve",
            json={"reason": "第二次批准"},
            headers=headers,
        )
        assert resp2.status_code == 400

    @pytest.mark.asyncio
    async def test_approval_history_recorded(self, client: AsyncClient, db_session):
        """多次操作后审批历史应正确记录所有操作。"""
        user_data, headers = await _register_and_login(
            client,
            email="edge-history@example.com",
            password="edge-history-123",
            display_name="Edge Tester 3",
        )
        project_id = await _create_project(client, headers)

        # 创建第一个 run 并 approve
        run_id_1, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.waiting_approval,
        )
        resp1 = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id_1}/approve",
            json={"reason": "首次批准"},
            headers=headers,
        )
        assert resp1.status_code == 200

        # 创建第二个 run 并 reject
        run_id_2, _ = await _create_run_with_nodes(
            db_session, project_id, RunStatus.waiting_approval,
        )
        resp2 = await client.post(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id_2}/reject",
            json={"reason": "需要修改"},
            headers=headers,
        )
        assert resp2.status_code == 200

        # 验证第一个 run 的审批历史
        resp_history_1 = await client.get(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id_1}/approvals",
            headers=headers,
        )
        assert resp_history_1.status_code == 200
        history_1 = resp_history_1.json()
        assert len(history_1["approval_history"]) == 1
        assert history_1["approval_history"][0]["action"] == "approve"
        assert history_1["approval_history"][0]["reason"] == "首次批准"

        # 验证第二个 run 的审批历史
        resp_history_2 = await client.get(
            f"/api/v1/projects/{project_id}/delegated-runs/{run_id_2}/approvals",
            headers=headers,
        )
        assert resp_history_2.status_code == 200
        history_2 = resp_history_2.json()
        assert len(history_2["approval_history"]) == 1
        assert history_2["approval_history"][0]["action"] == "reject"
        assert history_2["approval_history"][0]["reason"] == "需要修改"
