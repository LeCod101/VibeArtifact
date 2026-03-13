"""
图查询辅助函数模块。

提供纯函数风格的图查询工具，用于按类型过滤节点、获取关联边、
查找邻居节点、提取子图和拓扑排序等操作。
所有函数均不修改输入数据。
"""

from collections import deque
from typing import Literal
from uuid import UUID

from ir_core.schema.data import IREdgeData, IRNodeData


def get_nodes_by_type(
    node_type: str,
    nodes: list[IRNodeData],
) -> list[IRNodeData]:
    """
    按类型过滤节点。

    - node_type: 目标节点类型字符串
    - nodes: 待过滤的节点列表
    - 返回: 匹配类型的节点列表
    """
    return [n for n in nodes if n.node_type == node_type]


def get_edges_for_node(
    node_id: UUID,
    edges: list[IREdgeData],
    direction: Literal["outgoing", "incoming", "both"] = "both",
) -> list[IREdgeData]:
    """
    获取与指定节点关联的边。

    - node_id: 目标节点 ID
    - edges: 待过滤的边列表
    - direction: 方向过滤
      - "outgoing": 仅返回 source_node_id == node_id 的边
      - "incoming": 仅返回 target_node_id == node_id 的边
      - "both": 返回任一端匹配的边
    - 返回: 符合条件的边列表
    """
    if direction == "outgoing":
        return [e for e in edges if e.source_node_id == node_id]
    if direction == "incoming":
        return [e for e in edges if e.target_node_id == node_id]
    # both
    return [
        e for e in edges
        if e.source_node_id == node_id or e.target_node_id == node_id
    ]


def get_neighbors(
    node_id: UUID,
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
    direction: Literal["outgoing", "incoming", "both"] = "both",
) -> list[IRNodeData]:
    """
    获取指定节点的邻居节点。

    根据方向参数，通过关联边找到邻居节点 ID，再从节点列表中匹配返回。
    - node_id: 目标节点 ID
    - nodes: 完整节点列表
    - edges: 完整边列表
    - direction: "outgoing" / "incoming" / "both"
    - 返回: 邻居节点列表
    """
    # 收集邻居节点 ID
    neighbor_ids: set[UUID] = set()
    for e in edges:
        if direction in ("outgoing", "both") and e.source_node_id == node_id:
            neighbor_ids.add(e.target_node_id)
        if direction in ("incoming", "both") and e.target_node_id == node_id:
            neighbor_ids.add(e.source_node_id)

    # 构建节点索引并按 neighbor_ids 过滤
    return [n for n in nodes if n.id in neighbor_ids]


def get_subgraph(
    root_node_id: UUID,
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
    depth: int = 1,
) -> tuple[list[IRNodeData], list[IREdgeData]]:
    """
    从根节点出发，按 BFS 获取指定深度的子图。

    depth=0 表示只返回根节点本身（无边）。
    返回子图中的节点和边，边必须两端都在子图节点集合中。
    - root_node_id: BFS 起始节点 ID
    - nodes: 完整节点列表
    - edges: 完整边列表
    - depth: BFS 最大深度
    - 返回: (子图节点列表, 子图边列表)
    """
    # 构建节点索引
    node_map: dict[UUID, IRNodeData] = {n.id: n for n in nodes}

    # 根节点不存在时返回空结果
    if root_node_id not in node_map:
        return [], []

    # 构建邻接表（无向）
    adjacency: dict[UUID, list[UUID]] = {}
    for e in edges:
        adjacency.setdefault(e.source_node_id, []).append(e.target_node_id)
        adjacency.setdefault(e.target_node_id, []).append(e.source_node_id)

    # BFS 遍历
    visited: set[UUID] = {root_node_id}
    queue: deque[tuple[UUID, int]] = deque([(root_node_id, 0)])

    while queue:
        current_id, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        for neighbor_id in adjacency.get(current_id, []):
            if neighbor_id not in visited and neighbor_id in node_map:
                visited.add(neighbor_id)
                queue.append((neighbor_id, current_depth + 1))

    # 收集子图节点
    subgraph_nodes = [node_map[nid] for nid in visited]

    # 收集子图边（两端都必须在子图节点集合中）
    subgraph_edges = [
        e for e in edges
        if e.source_node_id in visited and e.target_node_id in visited
    ]

    return subgraph_nodes, subgraph_edges


def topological_sort(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> list[IRNodeData]:
    """
    按依赖关系（depends_on 边）对节点进行拓扑排序。

    无 depends_on 边的节点排在前面。
    有环时返回尽可能的排序结果，不抛出异常。
    使用 Kahn 算法：先输出入度为 0 的节点，再逐步移除已处理节点的出边。
    环中剩余节点按原始顺序追加到末尾。
    - nodes: 待排序节点列表
    - edges: 完整边列表（仅使用 depends_on 类型）
    - 返回: 排序后的节点列表
    """
    # 构建节点索引
    node_map: dict[UUID, IRNodeData] = {n.id: n for n in nodes}
    node_ids: set[UUID] = set(node_map.keys())

    # 仅关注 depends_on 边，且两端都在节点集合中
    dep_edges = [
        e for e in edges
        if e.edge_type == "depends_on"
        and e.source_node_id in node_ids
        and e.target_node_id in node_ids
    ]

    # 计算入度和邻接表
    # depends_on 语义：source 依赖 target，所以 target 应排在 source 前面
    # 拓扑序中 target → source，即 source 的入度 +1
    in_degree: dict[UUID, int] = {nid: 0 for nid in node_ids}
    adjacency: dict[UUID, list[UUID]] = {nid: [] for nid in node_ids}

    for e in dep_edges:
        # source 依赖 target，target 完成后才能处理 source
        in_degree[e.source_node_id] += 1
        adjacency[e.target_node_id].append(e.source_node_id)

    # Kahn 算法：入度为 0 的节点入队
    queue: deque[UUID] = deque(
        nid for nid in node_ids if in_degree[nid] == 0
    )
    sorted_ids: list[UUID] = []

    while queue:
        nid = queue.popleft()
        sorted_ids.append(nid)
        for neighbor_id in adjacency[nid]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)

    # 有环时，剩余节点按原始顺序追加
    sorted_set = set(sorted_ids)
    for n in nodes:
        if n.id not in sorted_set:
            sorted_ids.append(n.id)

    return [node_map[nid] for nid in sorted_ids]
