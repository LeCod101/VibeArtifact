"""
快照操作应用模块。

将一组 IROperationPayload 顺序应用到现有快照（节点列表 + 边列表）上，
返回新的节点和边列表。纯函数，不访问数据库，不修改原始输入。
"""

from __future__ import annotations

from uuid import UUID, uuid4

from ir_core.schema.data import IREdgeData, IRNodeData
from ir_core.schema.operation_types import (
    CreateEdgePayload,
    CreateNodePayload,
    DeleteEdgePayload,
    DeleteNodePayload,
    OperationType,
    UpdateEdgePropsPayload,
    UpdateNodePropsPayload,
)
from ir_core.validators.edge_validator import validate_edge
from ir_core.validators.node_validator import validate_node_props
from ir_core.validators.result import ValidationResult


class ApplyError(Exception):
    """
    操作应用失败时抛出的异常。

    包含 ValidationResult 对象，记录具体的校验错误信息。
    """

    def __init__(self, message: str, validation_result: ValidationResult) -> None:
        super().__init__(message)
        self.validation_result = validation_result


def _parse_uuid(value: str | UUID) -> UUID:
    """
    将字符串或 UUID 对象统一转换为 UUID。

    兼容 payload 中 node_id/edge_id 可能是字符串的情况。
    """
    if isinstance(value, UUID):
        return value
    return UUID(value)


def _parse_operation(raw: dict | object) -> tuple[str, dict]:
    """
    将原始操作数据解析为 (operation_type, payload_dict) 二元组。

    支持 dict 输入（来自 API/JSON）和 Pydantic model 输入。
    返回操作类型字符串和去掉 operation_type 字段的 payload 字典。
    """
    if isinstance(raw, dict):
        data = dict(raw)
    else:
        data = raw.model_dump()
    op_type = data.pop("operation_type")
    return op_type, data


def _apply_create_node(
    nodes: list[IRNodeData],
    payload_dict: dict,
) -> None:
    """
    执行 create_node 操作：校验 props、生成 ID、创建新节点并加入列表。

    - payload_dict: 包含 node_type, label, props 等字段的字典
    - 校验失败时抛出 ApplyError
    """
    parsed = CreateNodePayload.model_validate(payload_dict)

    # 校验节点属性
    result = validate_node_props(parsed.node_type, parsed.props)
    if not result.is_valid:
        raise ApplyError(
            f"create_node 校验失败: {result.errors}",
            result,
        )

    # 如果指定了 node_id 则使用，否则自动生成
    node_id = parsed.node_id if parsed.node_id is not None else uuid4()

    # 检查 node_id 是否已存在，防止重复
    if parsed.node_id is not None:
        for existing in nodes:
            if existing.id == node_id:
                raise ApplyError(
                    f"create_node 失败: 节点 {node_id} 已存在",
                    ValidationResult.fail([f"节点 {node_id} 已存在"]),
                )

    new_node = IRNodeData(
        id=node_id,
        node_type=parsed.node_type,
        label=parsed.label,
        props=parsed.props,
        position_x=parsed.position_x,
        position_y=parsed.position_y,
    )
    nodes.append(new_node)


def _apply_update_node_props(
    nodes: list[IRNodeData],
    payload_dict: dict,
) -> None:
    """
    执行 update_node_props 操作：找到目标节点，部分合并 props，校验合并结果。

    - payload_dict: 包含 node_id 和要更新的 props 字段
    - 节点不存在或合并后校验失败时抛出 ApplyError
    """
    parsed = UpdateNodePropsPayload.model_validate(payload_dict)
    target_id = parsed.node_id

    # 查找目标节点
    target_node: IRNodeData | None = None
    for node in nodes:
        if node.id == target_id:
            target_node = node
            break

    if target_node is None:
        raise ApplyError(
            f"update_node_props 失败: 节点 {target_id} 不存在",
            ValidationResult.fail([f"节点 {target_id} 不存在"]),
        )

    # 部分更新：合并 props
    merged_props = {**target_node.props, **parsed.props}

    # 校验合并后的 props
    result = validate_node_props(target_node.node_type, merged_props)
    if not result.is_valid:
        raise ApplyError(
            f"update_node_props 校验失败: {result.errors}",
            result,
        )

    # 写回合并结果
    target_node.props = merged_props


def _apply_delete_node(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
    payload_dict: dict,
) -> None:
    """
    执行 delete_node 操作：移除目标节点，并级联删除所有关联边。

    - payload_dict: 包含 node_id 字段
    - 节点不存在时抛出 ApplyError
    """
    parsed = DeleteNodePayload.model_validate(payload_dict)
    target_id = parsed.node_id

    # 查找目标节点索引
    found_idx: int | None = None
    for i, node in enumerate(nodes):
        if node.id == target_id:
            found_idx = i
            break

    if found_idx is None:
        raise ApplyError(
            f"delete_node 失败: 节点 {target_id} 不存在",
            ValidationResult.fail([f"节点 {target_id} 不存在"]),
        )

    # 移除节点
    nodes.pop(found_idx)

    # 级联删除：移除所有 source 或 target 为该节点的边
    edges[:] = [
        e for e in edges
        if e.source_node_id != target_id and e.target_node_id != target_id
    ]


def _apply_create_edge(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
    payload_dict: dict,
) -> None:
    """
    执行 create_edge 操作：校验边类型和源/目标组合，生成 ID，创建新边。

    - payload_dict: 包含 edge_type, source_node_id, target_node_id 等字段
    - 源/目标节点不存在或边约束不满足时抛出 ApplyError
    """
    parsed = CreateEdgePayload.model_validate(payload_dict)

    # 构建 node_id → node_type 映射，用于查找源/目标节点类型
    node_type_map: dict[UUID, str] = {}
    for node in nodes:
        node_type_map[node.id] = node.node_type

    # 检查源节点是否存在
    if parsed.source_node_id not in node_type_map:
        raise ApplyError(
            f"create_edge 失败: 源节点 {parsed.source_node_id} 不存在",
            ValidationResult.fail(
                [f"源节点 {parsed.source_node_id} 不存在"]
            ),
        )

    # 检查目标节点是否存在
    if parsed.target_node_id not in node_type_map:
        raise ApplyError(
            f"create_edge 失败: 目标节点 {parsed.target_node_id} 不存在",
            ValidationResult.fail(
                [f"目标节点 {parsed.target_node_id} 不存在"]
            ),
        )

    # 校验边类型和源/目标节点类型组合
    source_type = node_type_map[parsed.source_node_id]
    target_type = node_type_map[parsed.target_node_id]
    result = validate_edge(parsed.edge_type, source_type, target_type)
    if not result.is_valid:
        raise ApplyError(
            f"create_edge 校验失败: {result.errors}",
            result,
        )

    # 如果指定了 edge_id 则使用，否则自动生成
    edge_id = parsed.edge_id if parsed.edge_id is not None else uuid4()

    # 检查 edge_id 是否已存在，防止重复
    if parsed.edge_id is not None:
        for existing in edges:
            if existing.id == edge_id:
                raise ApplyError(
                    f"create_edge 失败: 边 {edge_id} 已存在",
                    ValidationResult.fail([f"边 {edge_id} 已存在"]),
                )

    new_edge = IREdgeData(
        id=edge_id,
        source_node_id=parsed.source_node_id,
        target_node_id=parsed.target_node_id,
        edge_type=parsed.edge_type,
        props=parsed.props,
    )
    edges.append(new_edge)


def _apply_update_edge_props(
    edges: list[IREdgeData],
    payload_dict: dict,
) -> None:
    """
    执行 update_edge_props 操作：找到目标边，更新 props。

    - payload_dict: 包含 edge_id 和要更新的 props 字段
    - 边不存在时抛出 ApplyError
    """
    parsed = UpdateEdgePropsPayload.model_validate(payload_dict)
    target_id = parsed.edge_id

    # 查找目标边
    target_edge: IREdgeData | None = None
    for edge in edges:
        if edge.id == target_id:
            target_edge = edge
            break

    if target_edge is None:
        raise ApplyError(
            f"update_edge_props 失败: 边 {target_id} 不存在",
            ValidationResult.fail([f"边 {target_id} 不存在"]),
        )

    # 合并更新 props
    existing = target_edge.props or {}
    target_edge.props = {**existing, **parsed.props}


def _apply_delete_edge(
    edges: list[IREdgeData],
    payload_dict: dict,
) -> None:
    """
    执行 delete_edge 操作：移除目标边。

    - payload_dict: 包含 edge_id 字段
    - 边不存在时抛出 ApplyError
    """
    parsed = DeleteEdgePayload.model_validate(payload_dict)
    target_id = parsed.edge_id

    # 查找目标边索引
    found_idx: int | None = None
    for i, edge in enumerate(edges):
        if edge.id == target_id:
            found_idx = i
            break

    if found_idx is None:
        raise ApplyError(
            f"delete_edge 失败: 边 {target_id} 不存在",
            ValidationResult.fail([f"边 {target_id} 不存在"]),
        )

    edges.pop(found_idx)


def apply_operations(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
    operations: list[dict | object],
) -> tuple[list[IRNodeData], list[IREdgeData]]:
    """
    将一组 IROperation 应用到现有快照上，返回新的节点和边列表。

    - nodes: 现有节点列表（不会被修改）
    - edges: 现有边列表（不会被修改）
    - operations: 操作列表，每项可以是 dict 或 Pydantic model

    核心行为：
    1. 深拷贝输入，不修改原数据
    2. 顺序执行每个操作
    3. 任何校验失败抛出 ApplyError（原子性：整体失败，不返回部分结果）

    返回：新的 (nodes, edges) 元组
    """
    # 深拷贝输入数据，避免修改原始列表
    new_nodes = [n.model_copy(deep=True) for n in nodes]
    new_edges = [e.model_copy(deep=True) for e in edges]

    # 操作类型到处理函数的分派表
    for raw_op in operations:
        op_type, payload_dict = _parse_operation(raw_op)

        if op_type == OperationType.CREATE_NODE:
            _apply_create_node(new_nodes, payload_dict)

        elif op_type == OperationType.UPDATE_NODE_PROPS:
            _apply_update_node_props(new_nodes, payload_dict)

        elif op_type == OperationType.DELETE_NODE:
            _apply_delete_node(new_nodes, new_edges, payload_dict)

        elif op_type == OperationType.CREATE_EDGE:
            _apply_create_edge(new_nodes, new_edges, payload_dict)

        elif op_type == OperationType.UPDATE_EDGE_PROPS:
            _apply_update_edge_props(new_edges, payload_dict)

        elif op_type == OperationType.DELETE_EDGE:
            _apply_delete_edge(new_edges, payload_dict)

        else:
            raise ApplyError(
                f"未知的操作类型: {op_type!r}",
                ValidationResult.fail([f"未知的操作类型: {op_type!r}"]),
            )

    return new_nodes, new_edges
