"""
Frontend Agent 投影模块。

为 frontend_agent 提供子视图：包含 page + component 节点，
以及 renders / depends_on 边。
"""

from ir_core.projections.result import ProjectionResult
from ir_core.schema.data import IREdgeData, IRNodeData

# frontend 投影允许的边类型
_FRONTEND_EDGE_TYPES = {"renders", "depends_on"}


def frontend_projection(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> ProjectionResult:
    """
    frontend_agent 专用投影。

    过滤出 page 和 component 类型节点，
    以及类型为 renders / depends_on 且两端节点都在结果集中的边。
    - nodes: 完整节点列表
    - edges: 完整边列表
    - 返回: 包含前端相关节点和边的 ProjectionResult
    """
    # 过滤 page 和 component 节点
    frontend_nodes = [
        n for n in nodes if n.node_type in ("page", "component")
    ]

    # 收集结果集节点 ID
    node_ids = {n.id for n in frontend_nodes}

    # 过滤边：类型匹配且两端都在节点集合中
    filtered_edges = [
        e for e in edges
        if e.edge_type in _FRONTEND_EDGE_TYPES
        and e.source_node_id in node_ids
        and e.target_node_id in node_ids
    ]

    return ProjectionResult(
        name="frontend",
        nodes=frontend_nodes,
        edges=filtered_edges,
    )
