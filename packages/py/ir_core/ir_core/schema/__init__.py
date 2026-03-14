"""
IR Schema 统一导出模块。

汇总导出所有枚举、Pydantic model 和映射表，
外部可直接 from ir_core.schema import NodeType, EntityProps, ... 使用。
"""

from ir_core.schema.data import (
    IREdgeData,
    IRNodeData,
    IROperationPayload,
)
from ir_core.schema.edge_types import (
    EDGE_CONSTRAINTS,
    EdgeType,
)
from ir_core.schema.node_types import (
    NODE_PROPS_MAP,
    CodeProps,
    ComponentProps,
    DecisionProps,
    DecisionStatus,
    DeliveryProps,
    EndpointProps,
    EntityProps,
    FieldDef,
    FileEntryDef,
    HttpMethod,
    NodeType,
    PageProps,
    Priority,
    PropDef,
    RiskProps,
    RiskSeverity,
    RiskStatus,
    ScopeProps,
    TaskProps,
)
from ir_core.schema.operation_types import (
    OPERATION_PAYLOAD_MAP,
    CreateEdgePayload,
    CreateNodePayload,
    DeleteEdgePayload,
    DeleteNodePayload,
    OperationType,
    UpdateEdgePropsPayload,
    UpdateNodePropsPayload,
)

__all__ = [
    # 数据传输对象
    "IRNodeData",
    "IREdgeData",
    "IROperationPayload",
    # 节点类型
    "NodeType",
    "NODE_PROPS_MAP",
    "FieldDef",
    "FileEntryDef",
    "PropDef",
    "Priority",
    "HttpMethod",
    "DecisionStatus",
    "RiskSeverity",
    "RiskStatus",
    "ScopeProps",
    "EntityProps",
    "EndpointProps",
    "PageProps",
    "ComponentProps",
    "DecisionProps",
    "RiskProps",
    "TaskProps",
    "CodeProps",
    "DeliveryProps",
    # 边类型
    "EdgeType",
    "EDGE_CONSTRAINTS",
    # 操作类型
    "OperationType",
    "OPERATION_PAYLOAD_MAP",
    "CreateNodePayload",
    "UpdateNodePropsPayload",
    "DeleteNodePayload",
    "CreateEdgePayload",
    "UpdateEdgePropsPayload",
    "DeleteEdgePayload",
]
