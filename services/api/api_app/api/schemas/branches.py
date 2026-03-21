"""分支相关的请求和响应模型 - 定义分支创建、fork、树形结构等数据结构。

包含：
- 创建分支请求
- Fork 分支请求
- 分支信息响应
- 分支树节点
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateBranchRequest(BaseModel):
    """创建分支请求。

    字段：
        parent_branch_id: 父分支 UUID
        branch_name: 分支名称，可选（不传则自动生成）
        base_snapshot_id: 分支起点快照 UUID，可选
    """

    parent_branch_id: UUID
    branch_name: str | None = None
    base_snapshot_id: UUID | None = None


class ForkBranchRequest(BaseModel):
    """Fork 分支请求。

    字段：
        fork_point_snapshot_id: fork 点的快照 UUID
        branch_name: 新分支名称，可选
    """

    fork_point_snapshot_id: UUID
    branch_name: str | None = None


class BranchResponse(BaseModel):
    """分支信息响应 - 返回分支基本信息。

    字段：
        id: 分支唯一标识
        conversation_id: 所属会话 UUID
        parent_branch_id: 父分支 UUID
        base_snapshot_id: 基线快照 UUID
        head_snapshot_id: 头部快照 UUID
        branch_name: 分支名称
        created_at: 创建时间
        message_count: 分支下的消息数量
    """

    id: UUID
    conversation_id: UUID
    parent_branch_id: UUID | None
    base_snapshot_id: UUID | None
    head_snapshot_id: UUID | None
    branch_name: str | None
    created_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class BranchTreeNode(BaseModel):
    """分支树节点 - 递归树形结构。

    字段：
        branch: 当前分支信息
        children: 子分支节点列表
    """

    branch: BranchResponse
    children: list[BranchTreeNode] = []

    model_config = ConfigDict(from_attributes=True)


class RollbackRequest(BaseModel):
    """回滚请求 - 指定要回滚到的目标快照。

    字段：
        snapshot_id: 要回滚到的目标快照 UUID
    """

    snapshot_id: UUID


class RollbackResponse(BaseModel):
    """回滚响应 - 返回回滚操作结果。

    字段：
        action: 回滚动作类型 ("forked" | "switched" | "no_change")
        switched_branch_id: 回滚后的活跃分支 ID
        new_branch_id: 新 fork 的分支 ID（仅 forked 时有值）
        snapshot_id: 回滚目标快照 ID
    """

    action: str
    switched_branch_id: str
    new_branch_id: str | None = None
    snapshot_id: str
