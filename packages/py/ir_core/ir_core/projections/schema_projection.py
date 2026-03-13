"""
Schema Agent 投影模块。

为 schema_agent 提供子视图：仅包含 entity 节点和它们之间的 depends_on 边。
"""

from ir_core.projections.result import ProjectionResult
from ir_core.schema.data import IREdgeData, IRNodeData


def schema_projection(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> ProjectionResult:
    """
    schema_agent 专用投影。

    过滤出 entity 类型节点，以及两端都是 entity 的 depends_on 边。
    - nodes: 完整节点列表
    - edges: 完整边列表
    - 返回: 仅含 entity 节点和 depends_on 边的 ProjectionResult
    """
    # 过滤 entity 类型节点
    entity_nodes = [n for n in nodes if n.node_type == "entity"]

    # 收集 entity 节点 ID 集合
    entity_ids = {n.id for n in entity_nodes}

    # 过滤两端都是 entity 的 depends_on 边
    filtered_edges = [
        e for e in edges
        if e.edge_type == "depends_on"
        and e.source_node_id in entity_ids
        and e.target_node_id in entity_ids
    ]

    return ProjectionResult(
        name="schema",
        nodes=entity_nodes,
        edges=filtered_edges,
    )
