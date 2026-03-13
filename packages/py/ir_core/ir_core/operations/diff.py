"""
快照差异计算模块。

计算两个快照（旧快照 → 新快照）之间的最小操作列表，
使得将这些操作应用到旧快照上可以得到新快照。纯函数，不访问数据库。
"""

from __future__ import annotations

from uuid import UUID

from ir_core.schema.data import IREdgeData, IRNodeData
from ir_core.schema.operation_types import OperationType


def _diff_props(old_props: dict, new_props: dict) -> dict | None:
    """
    计算两个 props 字典之间的差异字段。

    只返回值发生了变化的字段。如果没有差异，返回 None。
    """
    changed: dict = {}
    # 检查新增或修改的字段
    for key, value in new_props.items():
        if key not in old_props or old_props[key] != value:
            changed[key] = value
    # 这里不处理删除的字段（props 通常是增量更新，不删除 key）
    if not changed:
        return None
    return changed


def compute_diff(
    old_nodes: list[IRNodeData],
    old_edges: list[IREdgeData],
    new_nodes: list[IRNodeData],
    new_edges: list[IREdgeData],
) -> list[dict]:
    """
    计算两个快照之间的最小操作列表，使 old -> new。

    - old_nodes, old_edges: 旧快照的节点和边
    - new_nodes, new_edges: 新快照的节点和边

    操作顺序：先删边 -> 删节点 -> 新增节点 -> 新增边 -> 更新节点 -> 更新边
    （这个顺序确保 apply 时不会有悬挂引用）

    返回：dict 格式的操作列表（兼容 apply_operations 的输入）
    """
    operations: list[dict] = []

    # 构建旧快照的节点/边索引（id -> 对象）
    old_node_map: dict[UUID, IRNodeData] = {n.id: n for n in old_nodes}
    new_node_map: dict[UUID, IRNodeData] = {n.id: n for n in new_nodes}
    old_edge_map: dict[UUID, IREdgeData] = {e.id: e for e in old_edges}
    new_edge_map: dict[UUID, IREdgeData] = {e.id: e for e in new_edges}

    # 计算节点/边的 ID 集合
    old_node_ids = set(old_node_map.keys())
    new_node_ids = set(new_node_map.keys())
    old_edge_ids = set(old_edge_map.keys())
    new_edge_ids = set(new_edge_map.keys())

    # --- 第 1 步：删除的边（在 old 中有但 new 中没有）---
    # 先计算被删除的节点 ID，用于排除会被 DELETE_NODE 级联删除的边
    deleted_node_ids = old_node_ids - new_node_ids
    deleted_edge_ids = old_edge_ids - new_edge_ids
    # 排除两端有节点在 deleted_node_ids 中的边，
    # 因为 DELETE_NODE 会级联删除这些边，无需额外生成 DELETE_EDGE
    for edge_id in deleted_edge_ids:
        edge = old_edge_map[edge_id]
        if (
            edge.source_node_id in deleted_node_ids
            or edge.target_node_id in deleted_node_ids
        ):
            continue
        operations.append({
            "operation_type": OperationType.DELETE_EDGE,
            "edge_id": str(edge_id),
        })

    # --- 第 2 步：删除的节点（在 old 中有但 new 中没有）---
    for node_id in deleted_node_ids:
        operations.append({
            "operation_type": OperationType.DELETE_NODE,
            "node_id": str(node_id),
        })

    # --- 第 3 步：新增的节点（在 new 中有但 old 中没有）---
    created_node_ids = new_node_ids - old_node_ids
    for node_id in created_node_ids:
        node = new_node_map[node_id]
        operations.append({
            "operation_type": OperationType.CREATE_NODE,
            # 带上 node_id 以保持 diff 往返一致性
            "node_id": str(node.id),
            "node_type": node.node_type,
            "label": node.label,
            "props": node.props,
            "position_x": node.position_x,
            "position_y": node.position_y,
        })

    # --- 第 4 步：新增的边（在 new 中有但 old 中没有）---
    created_edge_ids = new_edge_ids - old_edge_ids
    for edge_id in created_edge_ids:
        edge = new_edge_map[edge_id]
        operations.append({
            "operation_type": OperationType.CREATE_EDGE,
            # 带上 edge_id 以保持 diff 往返一致性
            "edge_id": str(edge.id),
            "edge_type": edge.edge_type,
            "source_node_id": str(edge.source_node_id),
            "target_node_id": str(edge.target_node_id),
            "props": edge.props,
        })

    # --- 第 5 步：修改的节点（id 相同但 props 不同）---
    common_node_ids = old_node_ids & new_node_ids
    for node_id in common_node_ids:
        old_node = old_node_map[node_id]
        new_node = new_node_map[node_id]
        changed_props = _diff_props(old_node.props, new_node.props)
        if changed_props is not None:
            operations.append({
                "operation_type": OperationType.UPDATE_NODE_PROPS,
                "node_id": str(node_id),
                "props": changed_props,
            })

    # --- 第 6 步：修改的边（id 相同但 props 不同）---
    common_edge_ids = old_edge_ids & new_edge_ids
    for edge_id in common_edge_ids:
        old_edge = old_edge_map[edge_id]
        new_edge = new_edge_map[edge_id]
        old_props = old_edge.props or {}
        new_props = new_edge.props or {}
        changed_props = _diff_props(old_props, new_props)
        if changed_props is not None:
            operations.append({
                "operation_type": OperationType.UPDATE_EDGE_PROPS,
                "edge_id": str(edge_id),
                "props": changed_props,
            })

    return operations
