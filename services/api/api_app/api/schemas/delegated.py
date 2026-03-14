"""全权委托运行相关的请求和响应模型。

定义创建、查询全权委托运行所需的
请求体和响应体 Schema。
"""

from pydantic import BaseModel, Field


class CreateDelegatedRunRequest(BaseModel):
    """创建全权委托运行请求。

    字段：
        snapshot_id: 快照 ID（可选，不传则使用最新快照）
    """

    snapshot_id: str | None = Field(
        default=None,
        description="快照 ID，不传则使用项目最新快照",
    )


class CreateDelegatedRunResponse(BaseModel):
    """创建全权委托运行的响应。

    字段：
        run_id: 新建的运行 ID
        status: 运行初始状态（pending）
    """

    run_id: str
    status: str = "pending"


class DelegatedStepResponse(BaseModel):
    """单个 agent 步骤状态。

    字段：
        agent_id: agent 标识名称
        status: 步骤当前状态（pending / running / completed / failed）
        started_at: 开始时间（ISO 格式字符串，未开始则为 null）
        completed_at: 完成时间（ISO 格式字符串，未完成则为 null）
        duration_ms: 执行耗时（毫秒，未完成则为 null）
    """

    agent_id: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None


class DelegatedRunResponse(BaseModel):
    """全权委托运行详情响应。

    字段：
        run_id: 运行 ID
        status: 运行当前状态
        steps: 各 agent 步骤的状态列表
        created_at: 创建时间（ISO 格式字符串）
        completed_at: 完成时间（ISO 格式字符串，未完成则为 null）
        error_message: 失败原因（运行成功则为 null）
    """

    run_id: str
    status: str
    steps: list[DelegatedStepResponse] = []
    created_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None
