"""审批服务 - 处理委托运行的审批流程。

提供待审批项查询、批准、拒绝、调整等操作。
通过 SnapshotRepository 获取 IR 中的风险和决策节点，
通过 ApprovalRepository 记录审批历史。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from platform_data.models.approval import ApprovalAction, ApprovalRecord
from platform_data.models.execution import JobRun, RunStatus
from platform_data.repositories.approval_repo import ApprovalRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ApprovalService:
    """审批服务。

    处理委托运行的审批流程：获取待审批项、执行审批/拒绝/调整操作。

    参数:
        db: SQLAlchemy 异步数据库会话
    """

    def __init__(self, db: AsyncSession) -> None:
        """初始化审批服务，创建所需的 Repository 实例。

        参数:
            db: SQLAlchemy 异步数据库会话
        """
        self._db = db
        self._approval_repo = ApprovalRepository(db)
        self._snapshot_repo = SnapshotRepository(db)

    async def _get_job_run(self, run_id: UUID) -> JobRun:
        """获取指定的 JobRun 记录。

        参数:
            run_id: 运行 UUID

        返回:
            JobRun ORM 对象

        异常:
            ValueError: run 不存在
        """
        result = await self._db.execute(
            select(JobRun).where(JobRun.id == run_id)
        )
        job_run = result.scalar_one_or_none()
        if job_run is None:
            raise ValueError(f"运行记录不存在: {run_id}")
        return job_run

    async def _get_snapshot_id_for_run(self, job_run: JobRun) -> UUID | None:
        """获取 run 关联的快照 ID。

        优先使用 job_run.snapshot_id，如果为空则通过 project_id 获取最新活跃快照。

        参数:
            job_run: JobRun ORM 对象

        返回:
            快照 UUID，没有可用快照时返回 None
        """
        if job_run.snapshot_id is not None:
            return job_run.snapshot_id

        # 回退：通过项目获取最新活跃快照
        snapshot = await self._snapshot_repo.get_active(job_run.project_id)
        if snapshot is not None:
            return snapshot.id
        return None

    async def get_pending_approvals(self, run_id: UUID) -> dict:
        """获取运行的待审批项。

        流程：
        1. 查找 run 记录
        2. 获取 run 关联的快照
        3. 调用 snapshot_repo.get_approval_items() 获取风险/决策
        4. 获取审批历史记录
        5. 返回审批汇总

        参数:
            run_id: 运行 UUID

        返回:
            审批汇总字典，包含 high_risks / pending_decisions /
            requires_approval / approval_history 等字段
        """
        job_run = await self._get_job_run(run_id)
        run_status = (
            job_run.status.value
            if hasattr(job_run.status, "value")
            else str(job_run.status)
        )

        # 获取快照中的审批项
        snapshot_id = await self._get_snapshot_id_for_run(job_run)
        if snapshot_id is not None:
            approval_items = await self._snapshot_repo.get_approval_items(
                snapshot_id
            )
        else:
            approval_items = {
                "high_risks": [],
                "pending_decisions": [],
                "requires_approval": False,
            }

        # 获取审批历史
        history_records = await self._approval_repo.get_by_run(run_id)
        approval_history = [
            {
                "id": str(record.id),
                "action": record.action.value
                if hasattr(record.action, "value")
                else str(record.action),
                "reason": record.reason,
                "user_id": str(record.user_id),
                "created_at": record.created_at.isoformat()
                if record.created_at
                else None,
            }
            for record in history_records
        ]

        return {
            "run_id": str(run_id),
            "status": run_status,
            "high_risks": approval_items["high_risks"],
            "pending_decisions": approval_items["pending_decisions"],
            "requires_approval": approval_items["requires_approval"],
            "approval_history": approval_history,
        }

    async def _validate_waiting_approval(self, job_run: JobRun) -> None:
        """验证 run 状态是否为 waiting_approval。

        参数:
            job_run: JobRun ORM 对象

        异常:
            ValueError: 状态不是 waiting_approval
        """
        current_status = (
            job_run.status.value
            if hasattr(job_run.status, "value")
            else str(job_run.status)
        )
        if current_status != "waiting_approval":
            raise ValueError(
                f"运行状态为 {current_status}，无法执行审批操作"
            )

    async def _update_ir_nodes_status(
        self, snapshot_id: UUID, new_status: str
    ) -> int:
        """更新 IR 中所有高风险和待决策节点的状态。

        将 HIGH risk 节点的 status 从 open 改为 new_status，
        将 PENDING decision 节点的 status 从 pending 改为 new_status。

        参数:
            snapshot_id: 快照 UUID
            new_status: 要设置的新状态值

        返回:
            更新的节点总数
        """
        updated_count = 0

        # 更新高风险节点状态
        high_risks = await self._snapshot_repo.get_high_risks(snapshot_id)
        for node in high_risks:
            if node.props is None:
                node.props = {}
            # 拷贝 props dict 以触发 SQLAlchemy 脏检测
            new_props = dict(node.props)
            new_props["status"] = new_status
            node.props = new_props
            updated_count += 1

        # 更新待决策节点状态
        pending_decisions = await self._snapshot_repo.get_pending_decisions(
            snapshot_id
        )
        for node in pending_decisions:
            if node.props is None:
                node.props = {}
            new_props = dict(node.props)
            new_props["status"] = new_status
            node.props = new_props
            updated_count += 1

        return updated_count

    async def approve_run(
        self,
        run_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ) -> dict:
        """批准运行继续。

        流程：
        1. 验证 run 状态是 waiting_approval
        2. 更新 IR 中所有 HIGH risk 节点的状态为 accepted
        3. 更新 IR 中所有 PENDING decision 节点的状态为 accepted
        4. 创建 ApprovalRecord
        5. 更新 run 状态为 completed
        6. 返回结果

        参数:
            run_id: 运行 UUID
            user_id: 执行审批的用户 UUID
            reason: 审批理由（可选）

        返回:
            操作结果字典
        """
        job_run = await self._get_job_run(run_id)
        await self._validate_waiting_approval(job_run)

        # 更新 IR 节点状态
        snapshot_id = await self._get_snapshot_id_for_run(job_run)
        if snapshot_id is not None:
            await self._update_ir_nodes_status(snapshot_id, "accepted")

        # 创建审批记录
        record = ApprovalRecord(
            run_id=run_id,
            user_id=user_id,
            action=ApprovalAction.approve,
            reason=reason,
            snapshot_id=snapshot_id,
        )
        await self._approval_repo.create(record)

        # 更新 run 状态为 completed
        job_run.status = RunStatus.completed
        job_run.completed_at = datetime.now(timezone.utc)
        await self._db.flush()

        return {
            "success": True,
            "action": "approve",
            "run_id": str(run_id),
            "new_status": "completed",
            "message": "运行已批准，状态更新为 completed",
        }

    async def reject_run(
        self,
        run_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ) -> dict:
        """拒绝运行。

        流程：
        1. 验证 run 状态是 waiting_approval
        2. 创建 ApprovalRecord
        3. 更新 run 状态为 failed
        4. 返回结果

        参数:
            run_id: 运行 UUID
            user_id: 执行审批的用户 UUID
            reason: 拒绝理由（可选）

        返回:
            操作结果字典
        """
        job_run = await self._get_job_run(run_id)
        await self._validate_waiting_approval(job_run)

        # 获取快照 ID 用于记录
        snapshot_id = await self._get_snapshot_id_for_run(job_run)

        # 创建审批记录
        record = ApprovalRecord(
            run_id=run_id,
            user_id=user_id,
            action=ApprovalAction.reject,
            reason=reason,
            snapshot_id=snapshot_id,
        )
        await self._approval_repo.create(record)

        # 更新 run 状态为 failed
        job_run.status = RunStatus.failed
        job_run.completed_at = datetime.now(timezone.utc)
        job_run.error_message = reason or "用户拒绝审批"
        await self._db.flush()

        return {
            "success": True,
            "action": "reject",
            "run_id": str(run_id),
            "new_status": "failed",
            "message": "运行已拒绝，状态更新为 failed",
        }

    async def adjust_run(
        self,
        run_id: UUID,
        user_id: UUID,
        feedback: str,
        reason: str | None = None,
    ) -> dict:
        """调整运行（要求重跑）。

        Phase 1 简化实现：
        1. 验证 run 状态是 waiting_approval
        2. 创建 ApprovalRecord（action=adjust, reason=feedback）
        3. 更新 run 状态为 needs_attention（让用户在对话中继续调整）
        4. 返回结果

        参数:
            run_id: 运行 UUID
            user_id: 执行审批的用户 UUID
            feedback: 调整反馈内容
            reason: 调整理由（可选，默认使用 feedback）

        返回:
            操作结果字典
        """
        job_run = await self._get_job_run(run_id)
        await self._validate_waiting_approval(job_run)

        # 获取快照 ID 用于记录
        snapshot_id = await self._get_snapshot_id_for_run(job_run)

        # 创建审批记录，reason 字段存放 feedback
        record = ApprovalRecord(
            run_id=run_id,
            user_id=user_id,
            action=ApprovalAction.adjust,
            reason=reason or feedback,
            snapshot_id=snapshot_id,
            approval_items={"feedback": feedback},
        )
        await self._approval_repo.create(record)

        # 更新 run 状态为 needs_attention
        job_run.status = RunStatus.needs_attention
        await self._db.flush()

        return {
            "success": True,
            "action": "adjust",
            "run_id": str(run_id),
            "new_status": "needs_attention",
            "message": "运行已标记为需要调整，状态更新为 needs_attention",
        }
