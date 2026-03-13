"""
API Doc Agent 投影模块。

为 doc_agent 提供子视图：包含 endpoint 节点及其通过 queries / mutates 边
关联的 entity 节点，以及这些关联边。
"""

from ir_core.projections.result import ProjectionResult
from ir_core.schema.data import IREdgeData, IRNodeData

# api_doc 投影关注的边类型
_API_DOC_EDGE_TYPES = {"queries", "mutates"}


def api_doc_projection(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> ProjectionResult:
    """
    doc_agent 专用投影。

    先取出所有 endpoint 节点，再通过 queries / mutates 边找到关联的 entity 节点。
    返回这些节点和对应的边。
    - nodes: 完整节点列表
    - edges: 完整边列表
    - 返回: 包含 API 文档相关节点和边的 ProjectionResult
    """
    # 构建节点索引
    node_map = {n.id: n for n in nodes}

    # 取出所有 endpoint 节点
    endpoint_nodes = [n for n in nodes if n.node_type == "endpoint"]
    endpoint_ids = {n.id for n in endpoint_nodes}

    # 找到 queries / mutates 边中，source 是 endpoint 的边
    related_edges = [
        e for e in edges
        if e.edge_type in _API_DOC_EDGE_TYPES
        and e.source_node_id in endpoint_ids
    ]

    # 通过边找到关联的 entity 节点 ID
    related_entity_ids = {
        e.target_node_id for e in related_edges
        if e.target_node_id in node_map
    }

    # 合并节点：endpoint + 关联的 entity
    result_node_ids = endpoint_ids | related_entity_ids
    result_nodes = [node_map[nid] for nid in result_node_ids if nid in node_map]

    # 过滤边：两端都必须在结果节点集中
    result_edges = [
        e for e in related_edges
        if e.source_node_id in result_node_ids
        and e.target_node_id in result_node_ids
    ]

    return ProjectionResult(
        name="api_doc",
        nodes=result_nodes,
        edges=result_edges,
    )
