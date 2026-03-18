"""快照相关的响应模型 - 定义快照列表和详情的数据结构。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SnapshotSummaryResponse(BaseModel):
    """快照摘要响应。

    字段：
        id: 快照唯一标识
        created_at: 创建时间
        parent_id: 父快照 ID（根快照为 None）
        node_count: 快照内节点数量
        edge_count: 快照内边数量
        is_current: 是否为当前活跃快照
    """

    id: UUID
    created_at: datetime
    parent_id: UUID | None
    node_count: int
    edge_count: int
    is_current: bool

    model_config = {"from_attributes": True}


class SnapshotDetailResponse(BaseModel):
    """快照详情响应，包含节点和边的摘要信息。

    字段：
        id: 快照唯一标识
        created_at: 创建时间
        parent_id: 父快照 ID
        nodes: 节点列表（id、node_type、label）
        edges: 边列表（id、edge_type、source_node_id、target_node_id）
    """

    id: UUID
    created_at: datetime
    parent_id: UUID | None
    nodes: list[dict]
    edges: list[dict]

    model_config = {"from_attributes": True}
