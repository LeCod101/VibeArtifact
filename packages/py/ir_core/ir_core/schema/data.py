"""
IR 数据传输对象（DTO）模块。

定义与数据库 model 解耦的 Pydantic 数据传输对象，
用于 API 层和业务逻辑层之间的数据交换。
"""

from uuid import UUID

from pydantic import BaseModel


class IRNodeData(BaseModel):
    """
    IR 节点的数据传输对象。

    与数据库 ORM model 解耦，用于序列化/反序列化节点数据。
    - id: 节点唯一标识
    - node_type: 节点类型（对应 NodeType 枚举值）
    - label: 节点显示标签
    - props: 节点属性字典（结构由 node_type 决定）
    - position_x: 画布上的 X 坐标（可选）
    - position_y: 画布上的 Y 坐标（可选）
    """

    id: UUID
    node_type: str
    label: str
    props: dict
    position_x: float | None = None
    position_y: float | None = None


class IREdgeData(BaseModel):
    """
    IR 边的数据传输对象。

    与数据库 ORM model 解耦，用于序列化/反序列化边数据。
    - id: 边的唯一标识
    - source_node_id: 源节点 ID
    - target_node_id: 目标节点 ID
    - edge_type: 边类型（对应 EdgeType 枚举值）
    - props: 边的附加属性（可选）
    """

    id: UUID
    source_node_id: UUID
    target_node_id: UUID
    edge_type: str
    props: dict | None = None


class IROperationPayload(BaseModel):
    """
    IR 操作的基础载荷。

    所有具体操作 payload 的基类，仅包含操作类型标识。
    具体的 payload 定义在 operation_types.py 中。
    - operation_type: 操作类型（对应 OperationType 枚举值）
    """

    operation_type: str
