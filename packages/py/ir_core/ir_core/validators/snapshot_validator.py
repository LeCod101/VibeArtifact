"""
快照完整性校验器模块。

对整个快照（节点列表 + 边列表）进行全面的完整性校验：
1. 所有节点的 props 是否合法
2. 所有边的类型和源/目标组合是否合法
3. 是否存在悬挂边（指向不存在节点的边）
"""

from ir_core.schema.data import IREdgeData, IRNodeData
from ir_core.validators.edge_validator import validate_edge
from ir_core.validators.node_validator import validate_node_props
from ir_core.validators.result import ValidationResult


def validate_snapshot(
    nodes: list[IRNodeData],
    edges: list[IREdgeData],
) -> ValidationResult:
    """
    校验整个快照的完整性。

    - nodes: 快照中的所有节点列表
    - edges: 快照中的所有边列表

    校验流程：
    1. 逐一校验所有节点的 props 是否合法
    2. 构建 node_id → node_type 映射表
    3. 检查悬挂边（source/target 指向不存在的节点）
    4. 逐一校验所有边的类型和源/目标组合是否合法
    5. 合并所有校验结果并返回
    """

    result = ValidationResult.ok()

    # 构建节点 ID 到节点类型的映射表，供边校验使用
    node_type_map: dict[str, str] = {}
    for node in nodes:
        node_type_map[str(node.id)] = node.node_type

    # 校验所有节点的 props
    for node in nodes:
        node_result = validate_node_props(node.node_type, node.props)
        if not node_result.is_valid:
            # 为每条错误补充节点标识信息
            prefixed_errors = [
                f"节点 {node.label!r} (id={node.id}): {err}"
                for err in node_result.errors
            ]
            prefixed_result = ValidationResult.fail(
                errors=prefixed_errors,
                warnings=node_result.warnings,
            )
            result = result.merge(prefixed_result)

    # 校验所有边
    for edge in edges:
        source_id = str(edge.source_node_id)
        target_id = str(edge.target_node_id)

        # 检查悬挂边：source 不存在
        if source_id not in node_type_map:
            dangling_result = ValidationResult.fail(
                errors=[
                    f"悬挂边 (id={edge.id}): source_node_id={edge.source_node_id} "
                    f"指向不存在的节点"
                ],
            )
            result = result.merge(dangling_result)
            # source 不存在时无法进行类型组合校验，跳过
            continue

        # 检查悬挂边：target 不存在
        if target_id not in node_type_map:
            dangling_result = ValidationResult.fail(
                errors=[
                    f"悬挂边 (id={edge.id}): target_node_id={edge.target_node_id} "
                    f"指向不存在的节点"
                ],
            )
            result = result.merge(dangling_result)
            # target 不存在时无法进行类型组合校验，跳过
            continue

        # 获取源/目标节点类型，校验边类型和组合是否合法
        source_type = node_type_map[source_id]
        target_type = node_type_map[target_id]
        edge_result = validate_edge(edge.edge_type, source_type, target_type)
        if not edge_result.is_valid:
            # 为每条错误补充边标识信息
            prefixed_errors = [
                f"边 (id={edge.id}): {err}"
                for err in edge_result.errors
            ]
            prefixed_result = ValidationResult.fail(
                errors=prefixed_errors,
                warnings=edge_result.warnings,
            )
            result = result.merge(prefixed_result)

    return result
