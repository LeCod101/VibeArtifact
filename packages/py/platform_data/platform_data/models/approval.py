"""审批记录模型 - 定义审批动作枚举和审批记录表。

记录用户对委托运行的审批决定，支持审计追踪。
每次审批操作（approve / reject / adjust）生成一条记录。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin


class ApprovalAction(str, enum.Enum):
    """审批动作类型。"""

    # 批准
    approve = "approve"
    # 驳回
    reject = "reject"
    # 调整（附带修改意见）
    adjust = "adjust"


class ApprovalRecord(UUIDPrimaryKeyMixin, Base):
    """审批记录表。

    记录用户对委托运行的审批决定。
    每次审批操作生成一条记录，支持审计追踪。
    """

    __tablename__ = "approval_records"

    # 关联的运行 ID
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_runs.id"), nullable=False, index=True,
    )
    # 执行审批的用户 ID
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True,
    )
    # 审批动作：approve / reject / adjust
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, name="approval_action", native_enum=True),
        nullable=False,
    )
    # 审批理由（可选）
    reason: Mapped[str | None] = mapped_column(Text)
    # 审批时关联的快照 ID（可选）
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ir_snapshots.id"),
    )
    # 待审批项摘要（JSON 格式）
    approval_items: Mapped[dict | None] = mapped_column(JSONB)
    # 记录创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
