"""审批模型与仓储测试 - 覆盖 RunStatus 枚举同步、ApprovalRecord CRUD、
SnapshotRepository 风险/决策查询等 M9 阶段 1 的核心功能。
"""

import uuid

import pytest
from platform_data.models.approval import ApprovalAction, ApprovalRecord
from platform_data.models.execution import JobRun, RunStatus
from platform_data.models.ir import IRNode, IRSnapshot, SnapshotStatus
from platform_data.models.project import Project, ProjectStatus
from platform_data.models.user import User, UserStatus
from platform_data.repositories.approval_repo import ApprovalRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository

# ──────────────────────────────────────────────
# 辅助函数 - 创建测试前置数据
# ──────────────────────────────────────────────

async def _create_user(session) -> User:
    """创建测试用户。"""
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="fake_hash",
        display_name="Test User",
        status=UserStatus.active,
    )
    session.add(user)
    await session.flush()
    return user


async def _create_project(session, user_id: uuid.UUID) -> Project:
    """创建测试项目。"""
    project = Project(
        id=uuid.uuid4(),
        user_id=user_id,
        name="Test Project",
        status=ProjectStatus.active,
    )
    session.add(project)
    await session.flush()
    return project


async def _create_snapshot(session, project_id: uuid.UUID) -> IRSnapshot:
    """创建测试快照。"""
    snapshot = IRSnapshot(
        id=uuid.uuid4(),
        project_id=project_id,
        version=1,
        status=SnapshotStatus.active,
    )
    session.add(snapshot)
    await session.flush()
    return snapshot


async def _create_job_run(session, project_id: uuid.UUID, snapshot_id: uuid.UUID) -> JobRun:
    """创建测试运行记录。"""
    job_run = JobRun(
        id=uuid.uuid4(),
        project_id=project_id,
        snapshot_id=snapshot_id,
        job_type="delegated",
        status=RunStatus.pending,
    )
    session.add(job_run)
    await session.flush()
    return job_run


# ──────────────────────────────────────────────
# 任务 1: RunStatus 枚举同步测试
# ──────────────────────────────────────────────

class TestRunStatusEnum:
    """RunStatus 枚举扩展测试。"""

    def test_run_status_has_needs_attention(self):
        """验证 RunStatus 枚举包含 needs_attention 值。"""
        assert hasattr(RunStatus, "needs_attention")
        assert RunStatus.needs_attention.value == "needs_attention"

    def test_run_status_has_waiting_approval(self):
        """验证 RunStatus 枚举包含 waiting_approval 值。"""
        assert hasattr(RunStatus, "waiting_approval")
        assert RunStatus.waiting_approval.value == "waiting_approval"


# ──────────────────────────────────────────────
# 任务 2-3: ApprovalRecord 模型与仓储测试
# ──────────────────────────────────────────────

class TestApprovalRecord:
    """审批记录模型和仓储测试。"""

    @pytest.mark.asyncio
    async def test_create_approval_record(self, db_session):
        """创建审批记录并验证字段持久化。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)
        job_run = await _create_job_run(db_session, project.id, snapshot.id)

        repo = ApprovalRepository(db_session)
        record = ApprovalRecord(
            id=uuid.uuid4(),
            run_id=job_run.id,
            user_id=user.id,
            action=ApprovalAction.approve,
            reason="LGTM",
            snapshot_id=snapshot.id,
            approval_items={"high_risks": [], "pending_decisions": []},
        )
        created = await repo.create(record)

        assert created.id == record.id
        assert created.run_id == job_run.id
        assert created.action == ApprovalAction.approve
        assert created.reason == "LGTM"
        assert created.approval_items is not None

    @pytest.mark.asyncio
    async def test_get_approvals_by_run(self, db_session):
        """按运行 ID 查询审批记录列表。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)
        job_run = await _create_job_run(db_session, project.id, snapshot.id)

        repo = ApprovalRepository(db_session)

        # 创建两条审批记录
        for action in [ApprovalAction.reject, ApprovalAction.approve]:
            record = ApprovalRecord(
                id=uuid.uuid4(),
                run_id=job_run.id,
                user_id=user.id,
                action=action,
            )
            await repo.create(record)

        results = await repo.get_by_run(job_run.id)
        assert len(results) == 2
        # 按时间升序，第一条应为 reject
        assert results[0].action == ApprovalAction.reject
        assert results[1].action == ApprovalAction.approve

    @pytest.mark.asyncio
    async def test_get_latest_approval(self, db_session):
        """获取指定运行的最新审批记录。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)
        job_run = await _create_job_run(db_session, project.id, snapshot.id)

        repo = ApprovalRepository(db_session)

        # 创建一条 reject 记录
        reject_record = ApprovalRecord(
            id=uuid.uuid4(),
            run_id=job_run.id,
            user_id=user.id,
            action=ApprovalAction.reject,
        )
        await repo.create(reject_record)

        # 创建一条 approve 记录（手动设置更晚的时间戳确保排序）
        from datetime import datetime, timedelta, timezone
        later_time = datetime.now(timezone.utc) + timedelta(seconds=10)
        approve_record = ApprovalRecord(
            id=uuid.uuid4(),
            run_id=job_run.id,
            user_id=user.id,
            action=ApprovalAction.approve,
            created_at=later_time,
        )
        await repo.create(approve_record)

        latest = await repo.get_latest_by_run(job_run.id)
        assert latest is not None
        # 最新一条应为 approve（时间戳更晚）
        assert latest.action == ApprovalAction.approve

    @pytest.mark.asyncio
    async def test_get_latest_approval_empty(self, db_session):
        """运行无审批记录时返回 None。"""
        repo = ApprovalRepository(db_session)
        result = await repo.get_latest_by_run(uuid.uuid4())
        assert result is None


# ──────────────────────────────────────────────
# 任务 4: SnapshotRepository 风险/决策查询测试
# ──────────────────────────────────────────────

class TestSnapshotRepoDecisionRisk:
    """SnapshotRepository 的 pending 决策和高风险查询测试。"""

    @pytest.mark.asyncio
    async def test_get_pending_decisions(self, db_session):
        """获取快照中状态为 pending 的决策节点。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)

        # 创建一个 pending 决策节点
        pending_node = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="decision",
            label="Use PostgreSQL",
            props={"title": "Use PostgreSQL", "description": "DB choice", "status": "pending"},
        )
        # 创建一个 accepted 决策节点（不应被查出）
        accepted_node = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="decision",
            label="Use FastAPI",
            props={"title": "Use FastAPI", "description": "API framework", "status": "accepted"},
        )
        db_session.add_all([pending_node, accepted_node])
        await db_session.flush()

        repo = SnapshotRepository(db_session)
        results = await repo.get_pending_decisions(snapshot.id)

        assert len(results) == 1
        assert results[0].id == pending_node.id
        assert results[0].props["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_high_risks(self, db_session):
        """获取快照中高严重度且 open 状态的风险节点。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)

        # 高风险 + open
        high_open = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="risk",
            label="Security Breach",
            props={
                "title": "Security Breach",
                "description": "Critical vulnerability",
                "severity": "high",
                "status": "open",
            },
        )
        # 高风险 + mitigated（不应被查出）
        high_mitigated = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="risk",
            label="Data Loss",
            props={
                "title": "Data Loss",
                "description": "Backup failure",
                "severity": "high",
                "status": "mitigated",
            },
        )
        # 低风险 + open（不应被查出）
        low_open = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="risk",
            label="Minor Issue",
            props={
                "title": "Minor Issue",
                "description": "UI glitch",
                "severity": "low",
                "status": "open",
            },
        )
        db_session.add_all([high_open, high_mitigated, low_open])
        await db_session.flush()

        repo = SnapshotRepository(db_session)
        results = await repo.get_high_risks(snapshot.id)

        assert len(results) == 1
        assert results[0].id == high_open.id

    @pytest.mark.asyncio
    async def test_get_approval_items_requires_approval(self, db_session):
        """存在 pending 决策或高风险时 requires_approval 为 True。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)

        # 添加一个 pending 决策和一个高风险节点
        decision = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="decision",
            label="DB Choice",
            props={"title": "DB Choice", "description": "Pick DB", "status": "pending"},
        )
        risk = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="risk",
            label="Perf Risk",
            props={
                "title": "Perf Risk",
                "description": "High load",
                "severity": "high",
                "status": "open",
            },
        )
        db_session.add_all([decision, risk])
        await db_session.flush()

        repo = SnapshotRepository(db_session)
        items = await repo.get_approval_items(snapshot.id)

        assert items["requires_approval"] is True
        assert len(items["pending_decisions"]) == 1
        assert len(items["high_risks"]) == 1

    @pytest.mark.asyncio
    async def test_get_approval_items_no_approval_needed(self, db_session):
        """无 pending 决策和高风险时 requires_approval 为 False。"""
        user = await _create_user(db_session)
        project = await _create_project(db_session, user.id)
        snapshot = await _create_snapshot(db_session, project.id)

        # 添加一个 accepted 决策和一个 mitigated 低风险
        decision = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="decision",
            label="Accepted Decision",
            props={"title": "Accepted", "description": "Done", "status": "accepted"},
        )
        risk = IRNode(
            id=uuid.uuid4(),
            snapshot_id=snapshot.id,
            node_type="risk",
            label="Low Risk",
            props={
                "title": "Low Risk",
                "description": "Minor",
                "severity": "low",
                "status": "open",
            },
        )
        db_session.add_all([decision, risk])
        await db_session.flush()

        repo = SnapshotRepository(db_session)
        items = await repo.get_approval_items(snapshot.id)

        assert items["requires_approval"] is False
        assert len(items["pending_decisions"]) == 0
        assert len(items["high_risks"]) == 0
