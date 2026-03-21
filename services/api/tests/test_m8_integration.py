"""M8 树状会话集成测试。

覆盖分支全生命周期、回滚、快照绑定、上下文构建、
摘要压缩、决策抽取等端到端场景。
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ============================================================
# 测试用户常量
# ============================================================

M8_TEST_EMAIL = "m8-integration@example.com"
M8_TEST_PASSWORD = "m8-integration-pwd"
M8_TEST_DISPLAY = "M8 Integration"


# ============================================================
# 辅助函数
# ============================================================


async def _register_and_login(
    client: AsyncClient,
    email: str = M8_TEST_EMAIL,
    password: str = M8_TEST_PASSWORD,
    display_name: str = M8_TEST_DISPLAY,
) -> dict:
    """注册并登录，返回带 Bearer token 的请求头。

    参数：
        client: httpx 异步测试客户端
        email: 注册邮箱
        password: 注册密码
        display_name: 显示名

    返回：
        携带 Authorization header 的字典
    """
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    tokens = login_resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _create_project_and_conversation(
    client: AsyncClient,
    headers: dict,
) -> tuple[str, str, str]:
    """创建项目，获取默认会话和 main 分支 ID。

    参数：
        client: httpx 异步测试客户端
        headers: 认证请求头

    返回：
        元组 (project_id, conversation_id, main_branch_id)
    """
    # 创建项目
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "M8集成测试项目", "description": "集成测试"},
        headers=headers,
    )
    project_id = resp.json()["id"]

    # 获取默认会话（创建项目时自动创建）
    conv_resp = await client.get(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
    )
    conversation = conv_resp.json()[0]
    conversation_id = conversation["id"]
    main_branch_id = conversation["active_branch_id"]

    return project_id, conversation_id, main_branch_id


def _make_msg(role: str, content: str) -> SimpleNamespace:
    """构造测试用消息对象（SimpleNamespace 模拟）。

    参数：
        role: 消息角色
        content: 消息内容

    返回：
        SimpleNamespace 消息对象
    """
    return SimpleNamespace(
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def _make_conversation(rounds: int) -> list[SimpleNamespace]:
    """构造指定轮数的对话消息列表。

    每轮包含一条 user 消息和一条 assistant 消息。

    参数：
        rounds: 对话轮数

    返回：
        消息列表
    """
    messages = []
    for i in range(rounds):
        messages.append(_make_msg("user", f"用户第 {i + 1} 轮消息"))
        messages.append(
            _make_msg("assistant", f"助手第 {i + 1} 轮回复\n补充说明 {i + 1}")
        )
    return messages


# ============================================================
# 分支全生命周期测试
# ============================================================


class TestBranchLifecycle:
    """分支全生命周期测试。"""

    async def test_branch_lifecycle(self, client: AsyncClient):
        """创建→切换→fork→切回的完整生命周期。"""
        headers = await _register_and_login(
            client, email="lifecycle@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 1. 验证初始只有 main 分支
        resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/branches",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["branch_name"] == "main"

        # 2. 创建子分支 dev
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": main_branch_id,
                "branch_name": "dev",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        dev_branch_id = resp.json()["id"]
        assert resp.json()["branch_name"] == "dev"
        assert resp.json()["parent_branch_id"] == main_branch_id

        # 3. 切换到 dev 分支
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches/{dev_branch_id}/switch",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == dev_branch_id

        # 4. 在数据库创建快照用于 fork

        # 通过 API 的 db_session fixture 间接访问
        # 这里用 fork 不指定快照的方式测试（使用 dev 分支的 head_snapshot）
        # 先创建一个有快照的 fork 场景
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": dev_branch_id,
                "branch_name": "feature",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["parent_branch_id"] == dev_branch_id

        # 5. 切回 main 分支
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches/{main_branch_id}/switch",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == main_branch_id

        # 6. 最终验证分支总数
        resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/branches",
            headers=headers,
        )
        assert resp.status_code == 200
        branches = resp.json()
        # main + dev + feature = 3
        assert len(branches) == 3
        names = {b["branch_name"] for b in branches}
        assert names == {"main", "dev", "feature"}


# ============================================================
# 回滚测试
# ============================================================


class TestRollback:
    """回滚测试。"""

    async def test_rollback_no_change(self, client: AsyncClient, db_session):
        """回滚到当前 head snapshot 应返回 no_change。"""
        headers = await _register_and_login(
            client, email="rollback-nc@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 为 main 分支设置一个 head_snapshot_id
        from platform_data.models.ir import IRSnapshot
        from platform_data.repositories.branch_repo import BranchRepository

        snapshot = IRSnapshot(
            project_id=uuid.UUID(project_id),
            version=1,
        )
        db_session.add(snapshot)
        await db_session.flush()
        await db_session.refresh(snapshot)

        # 更新 main 分支的 head_snapshot_id
        branch_repo = BranchRepository(db_session)
        branch = await branch_repo.get_by_id(uuid.UUID(main_branch_id))
        branch.head_snapshot_id = snapshot.id
        await db_session.flush()

        # 回滚到当前 head
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/rollback",
            json={"snapshot_id": str(snapshot.id)},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "no_change"
        assert data["snapshot_id"] == str(snapshot.id)

    async def test_rollback_creates_fork(self, client: AsyncClient, db_session):
        """回滚到旧 snapshot 应创建新分支（forked）。"""
        headers = await _register_and_login(
            client, email="rollback-fork@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        from platform_data.models.ir import IRSnapshot
        from platform_data.repositories.branch_repo import BranchRepository

        # 创建两个快照：旧快照和新快照
        old_snapshot = IRSnapshot(
            project_id=uuid.UUID(project_id),
            version=1,
        )
        db_session.add(old_snapshot)
        await db_session.flush()
        await db_session.refresh(old_snapshot)

        new_snapshot = IRSnapshot(
            project_id=uuid.UUID(project_id),
            version=2,
        )
        db_session.add(new_snapshot)
        await db_session.flush()
        await db_session.refresh(new_snapshot)

        # 设置 main 分支的 base_snapshot 为 old，head 为 new
        branch_repo = BranchRepository(db_session)
        branch = await branch_repo.get_by_id(uuid.UUID(main_branch_id))
        branch.base_snapshot_id = old_snapshot.id
        branch.head_snapshot_id = new_snapshot.id
        await db_session.flush()

        # 回滚到旧快照（在 base_snapshot 中匹配）
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/rollback",
            json={"snapshot_id": str(old_snapshot.id)},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "forked"
        assert data["new_branch_id"] is not None
        assert data["snapshot_id"] == str(old_snapshot.id)

    async def test_rollback_nonexistent_snapshot(self, client: AsyncClient, db_session):
        """回滚到不存在的 snapshot 应返回 404。"""
        headers = await _register_and_login(
            client, email="rollback-404@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 设置 head_snapshot 避免 no_change 路径
        from platform_data.models.ir import IRSnapshot
        from platform_data.repositories.branch_repo import BranchRepository

        snapshot = IRSnapshot(
            project_id=uuid.UUID(project_id),
            version=1,
        )
        db_session.add(snapshot)
        await db_session.flush()
        await db_session.refresh(snapshot)

        branch_repo = BranchRepository(db_session)
        branch = await branch_repo.get_by_id(uuid.UUID(main_branch_id))
        branch.head_snapshot_id = snapshot.id
        await db_session.flush()

        # 回滚到不存在的快照
        fake_snapshot_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/rollback",
            json={"snapshot_id": fake_snapshot_id},
            headers=headers,
        )
        assert resp.status_code == 404


# ============================================================
# 快照绑定验证
# ============================================================


class TestSnapshotBinding:
    """快照绑定测试。"""

    async def test_message_response_schema(self, client: AsyncClient):
        """MessageResponse 应包含 snapshot_before_id 和 snapshot_after_id 字段。"""
        from api_app.api.schemas.conversations import MessageResponse

        # 验证 schema 定义包含快照字段
        fields = MessageResponse.model_fields
        assert "snapshot_before_id" in fields
        assert "snapshot_after_id" in fields

    async def test_message_has_snapshot_before(self, client: AsyncClient, db_session):
        """通过服务层保存的消息应携带 snapshot_before_id。"""
        headers = await _register_and_login(
            client, email="snap-bind@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        from platform_data.models.ir import IRSnapshot

        # 创建快照
        snapshot = IRSnapshot(
            project_id=uuid.UUID(project_id),
            version=1,
        )
        db_session.add(snapshot)
        await db_session.flush()
        await db_session.refresh(snapshot)

        # 通过 MessageService 保存消息（带 snapshot_before_id）
        from api_app.application.services.message_service import MessageService

        msg_service = MessageService(db_session)
        message = await msg_service.save_message_with_snapshot(
            conversation_id=uuid.UUID(conversation_id),
            branch_id=uuid.UUID(main_branch_id),
            role="user",
            content="测试快照绑定",
            snapshot_before_id=snapshot.id,
        )
        await db_session.flush()

        # 验证消息的 snapshot_before_id 被正确设置
        assert message.snapshot_before_id == snapshot.id


# ============================================================
# 上下文构建集成测试
# ============================================================


class TestContextIntegration:
    """上下文构建集成测试。"""

    async def test_context_builder_with_db_messages(
        self, client: AsyncClient, db_session
    ):
        """向分支发多条消息，验证 ContextBuilder 能正确组装。"""
        headers = await _register_and_login(
            client, email="ctx-build@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 插入 4 轮消息到 main 分支
        from api_app.application.services.message_service import MessageService

        msg_service = MessageService(db_session)
        for i in range(4):
            await msg_service.save_message(
                conversation_id=uuid.UUID(conversation_id),
                branch_id=uuid.UUID(main_branch_id),
                role="user",
                content=f"用户消息第 {i + 1} 轮",
            )
            await msg_service.save_message(
                conversation_id=uuid.UUID(conversation_id),
                branch_id=uuid.UUID(main_branch_id),
                role="assistant",
                content=f"助手回复第 {i + 1} 轮",
            )
        await db_session.flush()

        # 用 ContextBuilder 构建上下文
        from api_app.application.services.context_builder import (
            ConversationContextBuilder,
        )

        builder = ConversationContextBuilder(db_session)
        context = await builder.build_context(
            conversation_id=uuid.UUID(conversation_id),
            branch_id=uuid.UUID(main_branch_id),
        )

        # 上下文应包含消息（至少有 user + assistant 消息）
        assert len(context) > 0

        # 验证消息中包含 user 和 assistant 角色
        roles = {m["role"] for m in context}
        assert "user" in roles
        assert "assistant" in roles

    async def test_context_builder_respects_round_limit(
        self, client: AsyncClient, db_session
    ):
        """发超过 RECENT_ROUNDS 条消息，验证只返回最近几轮。"""
        headers = await _register_and_login(
            client, email="ctx-limit@example.com"
        )
        project_id, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 插入 8 轮消息（远超 RECENT_ROUNDS=3）
        from api_app.application.services.message_service import MessageService

        msg_service = MessageService(db_session)
        for i in range(8):
            await msg_service.save_message(
                conversation_id=uuid.UUID(conversation_id),
                branch_id=uuid.UUID(main_branch_id),
                role="user",
                content=f"用户消息第 {i + 1} 轮",
            )
            await msg_service.save_message(
                conversation_id=uuid.UUID(conversation_id),
                branch_id=uuid.UUID(main_branch_id),
                role="assistant",
                content=f"助手回复第 {i + 1} 轮",
            )
        await db_session.flush()

        from api_app.application.services.context_builder import (
            ConversationContextBuilder,
        )

        builder = ConversationContextBuilder(db_session)
        context = await builder.build_context(
            conversation_id=uuid.UUID(conversation_id),
            branch_id=uuid.UUID(main_branch_id),
        )

        # 过滤掉 system 消息，只统计 user 消息
        user_messages = [m for m in context if m["role"] == "user"]
        # 最多应只返回 RECENT_ROUNDS 轮的 user 消息
        assert len(user_messages) <= ConversationContextBuilder.RECENT_ROUNDS


# ============================================================
# 摘要压缩集成测试
# ============================================================


class TestSummaryIntegration:
    """摘要压缩集成测试。"""

    async def test_summary_compression_threshold(self):
        """发 >10 轮消息后应触发压缩。"""
        from agents.analysis.summary_generator import SummaryGenerator

        gen = SummaryGenerator()

        # 11 轮消息应超过 COMPRESSION_THRESHOLD=10
        messages = _make_conversation(11)
        should = await gen.should_compress(messages)
        assert should is True

        # 生成摘要
        summary = await gen.generate_summary(messages)
        assert len(summary) > 0
        # 摘要应包含 assistant 消息的第一行
        assert "助手第 1 轮回复" in summary

    async def test_summary_preserves_recent(self):
        """压缩后最近 KEEP_RECENT 轮不被压缩。"""
        from agents.analysis.summary_generator import SummaryGenerator

        gen = SummaryGenerator()
        messages = _make_conversation(12)

        # 模拟 compress_branch 的切分逻辑
        # 从后往前找到第 KEEP_RECENT 个 user 消息位置
        user_count = 0
        split_idx = len(messages)
        for i in range(len(messages) - 1, -1, -1):
            role = getattr(messages[i], "role", "")
            if role == "user":
                user_count += 1
                if user_count >= gen.KEEP_RECENT:
                    split_idx = i
                    break

        # 需要压缩的消息
        to_compress = messages[:split_idx]
        # 保留的消息
        preserved = messages[split_idx:]

        # 保留的消息中应有 KEEP_RECENT 条 user 消息
        preserved_user = [
            m for m in preserved if getattr(m, "role", "") == "user"
        ]
        assert len(preserved_user) == gen.KEEP_RECENT

        # 压缩部分能正常生成摘要
        summary = await gen.generate_summary(to_compress)
        assert len(summary) > 0

        # 保留部分的最后一轮消息不在摘要中
        last_user_content = preserved[-2].content
        assert last_user_content not in summary


# ============================================================
# 决策抽取集成测试
# ============================================================


class TestDecisionIntegration:
    """决策抽取集成测试。"""

    async def test_decision_extraction_from_messages(self):
        """包含决策关键词的消息能被抽取。"""
        from agents.analysis.decision_extractor import DecisionExtractor

        extractor = DecisionExtractor()
        messages = [
            _make_msg("user", "我们选择 React 作为前端框架"),
            _make_msg("assistant", "好的，使用 React"),
            _make_msg("user", "去掉注册功能，只保留登录"),
            _make_msg("assistant", "了解，移除注册流程"),
            _make_msg("user", "今天天气不错"),
            _make_msg("assistant", "确实如此"),
        ]

        decisions = await extractor.extract_decisions(messages)

        # 应该抽取到 2 条决策
        assert len(decisions) == 2

        # 第一条：tech_choice（"选择"）
        assert decisions[0].decision_type == "tech_choice"
        assert "React" in decisions[0].description

        # 第二条：feature_scope（"去掉"）
        assert decisions[1].decision_type == "feature_scope"
        assert "注册" in decisions[1].description

    async def test_decision_write_to_ir_operations(self):
        """write_to_ir 应返回正确的 create_node 操作。"""
        from agents.analysis.decision_extractor import (
            DecisionExtractor,
            DecisionRecord,
        )

        extractor = DecisionExtractor()

        decisions = [
            DecisionRecord(
                decision_type="tech_choice",
                title="选择 PostgreSQL",
                description="数据库选择 PostgreSQL",
                rationale="成熟稳定",
                affected_nodes=[],
                timestamp=datetime.now(timezone.utc),
            ),
        ]

        operations = await extractor.write_to_ir(
            db=None,
            project_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
            decisions=decisions,
        )

        assert len(operations) == 1
        op = operations[0]
        assert op["operation_type"] == "create_node"
        assert op["node_type"] == "decision"
        assert op["label"] == "选择 PostgreSQL"
        assert op["props"]["status"] == "accepted"


# ============================================================
# 分支树形结构测试
# ============================================================


class TestBranchTree:
    """分支树测试。"""

    async def test_branch_tree_structure(self, client: AsyncClient):
        """创建多级分支，验证树形结构正确。"""
        headers = await _register_and_login(
            client, email="tree-struct@example.com"
        )
        _, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 创建 main -> dev -> feature 三级分支
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": main_branch_id,
                "branch_name": "dev",
            },
            headers=headers,
        )
        dev_branch_id = resp.json()["id"]

        await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": dev_branch_id,
                "branch_name": "feature-a",
            },
            headers=headers,
        )

        # 创建 main -> staging 同级分支
        await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": main_branch_id,
                "branch_name": "staging",
            },
            headers=headers,
        )

        # 获取树形结构
        resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/branches/tree",
            headers=headers,
        )
        assert resp.status_code == 200
        tree = resp.json()

        # 根节点应该是 main
        assert len(tree) == 1
        root = tree[0]
        assert root["branch"]["branch_name"] == "main"

        # main 应有两个子节点: dev 和 staging
        assert len(root["children"]) == 2
        child_names = {c["branch"]["branch_name"] for c in root["children"]}
        assert child_names == {"dev", "staging"}

        # dev 应有一个子节点: feature-a
        dev_node = next(
            c for c in root["children"]
            if c["branch"]["branch_name"] == "dev"
        )
        assert len(dev_node["children"]) == 1
        assert dev_node["children"][0]["branch"]["branch_name"] == "feature-a"

        # staging 应无子节点
        staging_node = next(
            c for c in root["children"]
            if c["branch"]["branch_name"] == "staging"
        )
        assert len(staging_node["children"]) == 0

    async def test_branch_tree_with_messages(
        self, client: AsyncClient, db_session
    ):
        """树节点应包含正确的 message_count。"""
        headers = await _register_and_login(
            client, email="tree-msg@example.com"
        )
        _, conversation_id, main_branch_id = (
            await _create_project_and_conversation(client, headers)
        )

        # 向 main 分支插入 3 条消息
        from api_app.application.services.message_service import MessageService

        msg_service = MessageService(db_session)
        for i in range(3):
            await msg_service.save_message(
                conversation_id=uuid.UUID(conversation_id),
                branch_id=uuid.UUID(main_branch_id),
                role="user",
                content=f"消息 {i + 1}",
            )
        await db_session.flush()

        # 创建子分支 dev（不添加消息）
        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches",
            json={
                "parent_branch_id": main_branch_id,
                "branch_name": "dev",
            },
            headers=headers,
        )
        assert resp.status_code == 201

        # 获取树形结构
        resp = await client.get(
            f"/api/v1/conversations/{conversation_id}/branches/tree",
            headers=headers,
        )
        assert resp.status_code == 200
        tree = resp.json()

        root = tree[0]
        # main 分支应有 3 条消息
        assert root["branch"]["message_count"] == 3

        # dev 分支应有 0 条消息
        dev_node = root["children"][0]
        assert dev_node["branch"]["message_count"] == 0


# ============================================================
# 边界情况测试
# ============================================================


class TestEdgeCases:
    """边界情况测试。"""

    async def test_fork_nonexistent_snapshot(self, client: AsyncClient):
        """fork 不存在的 snapshot 对应的不存在的分支应返回 404。"""
        headers = await _register_and_login(
            client, email="edge-fork@example.com"
        )
        _, conversation_id, _ = await _create_project_and_conversation(
            client, headers
        )

        fake_branch_id = str(uuid.uuid4())
        fake_snapshot_id = str(uuid.uuid4())

        resp = await client.post(
            f"/api/v1/conversations/{conversation_id}/branches/{fake_branch_id}/fork",
            json={"fork_point_snapshot_id": fake_snapshot_id},
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_switch_branch_wrong_conversation(self, client: AsyncClient):
        """切换不属于当前会话的分支应返回 404。"""
        headers = await _register_and_login(
            client, email="edge-switch@example.com"
        )
        # 创建两个项目各带一个会话
        _, conv1_id, _ = await _create_project_and_conversation(client, headers)

        # 创建第二个项目和会话
        resp2 = await client.post(
            "/api/v1/projects",
            json={"name": "项目2", "description": "测试"},
            headers=headers,
        )
        project2_id = resp2.json()["id"]
        conv2_resp = await client.get(
            f"/api/v1/projects/{project2_id}/conversations",
            headers=headers,
        )
        conv2_branch_id = conv2_resp.json()[0]["active_branch_id"]

        # 尝试在 conv1 中切换到 conv2 的分支
        resp = await client.post(
            f"/api/v1/conversations/{conv1_id}/branches/{conv2_branch_id}/switch",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_create_branch_with_nonexistent_conversation(
        self, client: AsyncClient
    ):
        """向不存在的会话创建分支应返回 404。"""
        headers = await _register_and_login(
            client, email="edge-noconv@example.com"
        )

        fake_conversation_id = str(uuid.uuid4())
        fake_branch_id = str(uuid.uuid4())

        resp = await client.post(
            f"/api/v1/conversations/{fake_conversation_id}/branches",
            json={"parent_branch_id": fake_branch_id},
            headers=headers,
        )
        assert resp.status_code == 404
