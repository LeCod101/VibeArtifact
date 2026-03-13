"""
Architecture Agent 投影模块。

为 diagram_agent 提供完整视图：原样返回全部节点和全部边。
"""

from ir_core.projections.result import ProjectionResult
from ir_core.schema.data import IREdgeData, IRNodeData


def architecture_projection(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> ProjectionResult:
    """
    diagram_agent 专用投影。

    不做任何过滤，直接返回完整的节点和边列表。
    - nodes: 完整节点列表
    - edges: 完整边列表
    - 返回: 包含全部节点和边的 ProjectionResult
    """
    return ProjectionResult(
        name="architecture",
        nodes=list(nodes),
        edges=list(edges),
    )
