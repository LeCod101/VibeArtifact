"""
投影结果模型模块。

定义所有 projection 函数统一使用的返回类型 ProjectionResult。
"""

from pydantic import BaseModel

from ir_core.schema.data import IREdgeData, IRNodeData


class ProjectionResult(BaseModel):
    """
    投影结果数据模型。

    所有 projection 函数的统一返回类型，包含投影名称、筛选后的节点和边。
    - name: 投影名称（标识此投影的用途）
    - nodes: 投影包含的节点列表
    - edges: 投影包含的边列表（两端节点必须都在 nodes 中）
    """

    name: str
    nodes: list[IRNodeData]
    edges: list[IREdgeData]
