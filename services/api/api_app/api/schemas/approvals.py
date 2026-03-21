"""审批相关的请求和响应模型。

定义审批操作（批准、拒绝、调整）的请求体和响应体 Schema。
"""

from pydantic import BaseModel, Field


class ApproveRequest(BaseModel):
    """批准请求体。

    字段：
        reason: 批准理由（可选）
    """

    reason: str | None = Field(
        default=None,
        description="批准理由",
    )


class RejectRequest(BaseModel):
    """拒绝请求体。

    字段：
        reason: 拒绝理由（可选）
    """

    reason: str | None = Field(
        default=None,
        description="拒绝理由",
    )


class AdjustRequest(BaseModel):
    """调整请求体。

    字段：
        feedback: 调整反馈内容（必填）
        reason: 调整理由（可选）
    """

    feedback: str = Field(
        ...,
        description="调整反馈内容",
    )
    reason: str | None = Field(
        default=None,
        description="调整理由",
    )


class ApprovalItemResponse(BaseModel):
    """审批项汇总响应。

    字段：
        run_id: 运行 ID
        status: 当前运行状态
        high_risks: 高风险节点列表
        pending_decisions: 待决策节点列表
        requires_approval: 是否需要审批
        approval_history: 审批历史记录
    """

    run_id: str
    status: str
    high_risks: list[dict] = []
    pending_decisions: list[dict] = []
    requires_approval: bool = False
    approval_history: list[dict] = []


class ApprovalActionResponse(BaseModel):
    """审批操作响应。

    字段：
        success: 操作是否成功
        action: 执行的操作类型（approve / reject / adjust）
        run_id: 运行 ID
        new_status: 更新后的运行状态
        message: 操作结果描述
    """

    success: bool
    action: str
    run_id: str
    new_status: str
    message: str
