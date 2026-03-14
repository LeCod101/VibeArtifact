"""
IR 边类型定义模块。

定义所有合法的边类型枚举，以及每种边类型允许的源/目标节点类型约束。
提供 EDGE_CONSTRAINTS 映射表，用于校验边的合法性。
"""

from enum import StrEnum

from ir_core.schema.node_types import NodeType

# ============================================================
# 边类型枚举
# ============================================================

class EdgeType(StrEnum):
    """
    IR 图中所有合法的边类型。

    使用 StrEnum 以便 JSON 序列化时直接输出字符串值。
    """

    # scope 定义实体/端点/页面
    DEFINES = "defines"
    # 端点查询实体
    QUERIES = "queries"
    # 端点修改实体
    MUTATES = "mutates"
    # 页面渲染组件
    RENDERS = "renders"
    # 实体/组件之间的依赖关系
    DEPENDS_ON = "depends_on"
    # 任意节点之间的引用关系
    REFERENCES = "references"
    # 决策解决风险
    RESOLVES = "resolves"


# ============================================================
# 边类型合法约束映射表
# ============================================================

# 每种边类型允许的 (源节点类型, 目标节点类型) 组合列表。
# references 类型允许任意组合，用 None 标记。
EDGE_CONSTRAINTS: dict[EdgeType, list[tuple[NodeType, NodeType]] | None] = {
    EdgeType.DEFINES: [
        (NodeType.SCOPE, NodeType.ENTITY),
        (NodeType.SCOPE, NodeType.ENDPOINT),
        (NodeType.SCOPE, NodeType.PAGE),
    ],
    EdgeType.QUERIES: [
        (NodeType.ENDPOINT, NodeType.ENTITY),
    ],
    EdgeType.MUTATES: [
        (NodeType.ENDPOINT, NodeType.ENTITY),
    ],
    EdgeType.RENDERS: [
        (NodeType.PAGE, NodeType.COMPONENT),
    ],
    EdgeType.DEPENDS_ON: [
        (NodeType.ENTITY, NodeType.ENTITY),
        (NodeType.COMPONENT, NodeType.COMPONENT),
        (NodeType.TASK, NodeType.TASK),
        # 代码文件之间的依赖（如 models → schemas → routes）
        (NodeType.CODE, NodeType.CODE),
    ],
    # references 允许任意节点类型之间的引用，用 None 标记
    EdgeType.REFERENCES: None,
    EdgeType.RESOLVES: [
        (NodeType.DECISION, NodeType.RISK),
    ],
}
