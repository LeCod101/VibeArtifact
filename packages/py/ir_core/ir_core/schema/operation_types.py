"""
IR 操作类型定义模块。

定义所有合法的操作类型枚举，以及每种操作对应的 payload Pydantic model。
提供 OPERATION_PAYLOAD_MAP 映射表，方便根据操作类型查找对应的 payload model。
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType

# ============================================================
# 操作类型枚举
# ============================================================

class OperationType(StrEnum):
    """
    IR 图上所有合法的操作类型。

    使用 StrEnum 以便 JSON 序列化时直接输出字符串值。
    """

    # 创建节点
    CREATE_NODE = "create_node"
    # 更新节点属性（部分更新）
    UPDATE_NODE_PROPS = "update_node_props"
    # 删除节点
    DELETE_NODE = "delete_node"
    # 创建边
    CREATE_EDGE = "create_edge"
    # 更新边属性
    UPDATE_EDGE_PROPS = "update_edge_props"
    # 删除边
    DELETE_EDGE = "delete_edge"


# ============================================================
# 各操作类型的 Payload Model
# ============================================================

class CreateNodePayload(BaseModel):
    """
    创建节点操作的载荷。

    - node_id: 指定节点 ID（可选，用于 diff 往返保持一致性；不传则自动生成）
    - node_type: 要创建的节点类型
    - label: 节点显示标签
    - props: 节点属性字典（结构由 node_type 决定）
    - position_x: 画布上的 X 坐标（可选）
    - position_y: 画布上的 Y 坐标（可选）
    """

    node_id: UUID | None = None
    node_type: NodeType
    label: str
    props: dict
    position_x: float | None = None
    position_y: float | None = None


class UpdateNodePropsPayload(BaseModel):
    """
    更新节点属性操作的载荷。

    支持部分更新，只需传入要修改的字段。
    - node_id: 目标节点 ID
    - props: 要更新的属性字典（合并到现有属性）
    """

    node_id: UUID
    props: dict


class DeleteNodePayload(BaseModel):
    """
    删除节点操作的载荷。

    - node_id: 要删除的节点 ID
    """

    node_id: UUID


class CreateEdgePayload(BaseModel):
    """
    创建边操作的载荷。

    - edge_id: 指定边 ID（可选，用于 diff 往返保持一致性；不传则自动生成）
    - edge_type: 要创建的边类型
    - source_node_id: 源节点 ID
    - target_node_id: 目标节点 ID
    - props: 边的附加属性（可选）
    """

    edge_id: UUID | None = None
    edge_type: EdgeType
    source_node_id: UUID
    target_node_id: UUID
    props: dict | None = None


class UpdateEdgePropsPayload(BaseModel):
    """
    更新边属性操作的载荷。

    - edge_id: 目标边 ID
    - props: 要更新的属性字典
    """

    edge_id: UUID
    props: dict


class DeleteEdgePayload(BaseModel):
    """
    删除边操作的载荷。

    - edge_id: 要删除的边 ID
    """

    edge_id: UUID


# ============================================================
# 操作类型 → Payload Model 映射表
# ============================================================

# 根据操作类型查找对应的 payload model，用于动态校验操作载荷的合法性。
OPERATION_PAYLOAD_MAP: dict[OperationType, type[BaseModel]] = {
    OperationType.CREATE_NODE: CreateNodePayload,
    OperationType.UPDATE_NODE_PROPS: UpdateNodePropsPayload,
    OperationType.DELETE_NODE: DeleteNodePayload,
    OperationType.CREATE_EDGE: CreateEdgePayload,
    OperationType.UPDATE_EDGE_PROPS: UpdateEdgePropsPayload,
    OperationType.DELETE_EDGE: DeleteEdgePayload,
}
