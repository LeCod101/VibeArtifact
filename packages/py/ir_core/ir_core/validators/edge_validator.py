"""
边类型校验器模块。

校验边类型是否合法，以及源/目标节点类型组合是否符合 EDGE_CONSTRAINTS 约束。
references 类型允许任意节点组合，其他类型需严格匹配约束表。
"""

from ir_core.schema.edge_types import EDGE_CONSTRAINTS
from ir_core.validators.result import ValidationResult


def validate_edge(
    edge_type: str,
    source_node_type: str,
    target_node_type: str,
) -> ValidationResult:
    """
    校验边类型及源/目标节点类型组合是否合法。

    - edge_type: 边类型字符串（对应 EdgeType 枚举值）
    - source_node_type: 源节点类型字符串
    - target_node_type: 目标节点类型字符串

    校验逻辑：
    1. 未知 edge_type → 返回错误
    2. references 类型 → 允许任意组合，直接通过
    3. 其他类型：源/目标不在 EDGE_CONSTRAINTS 合法组合内 → 返回错误
    4. 校验通过 → 返回 ok
    """

    # 在 EDGE_CONSTRAINTS 中查找对应的约束
    constraints = None
    found = False
    for key, value in EDGE_CONSTRAINTS.items():
        if key.value == edge_type:
            constraints = value
            found = True
            break

    # 未知边类型
    if not found:
        return ValidationResult.fail(
            errors=[f"未知的边类型: {edge_type!r}"],
        )

    # references 类型允许任意节点组合（constraints 为 None）
    if constraints is None:
        return ValidationResult.ok()

    # 检查 (source_node_type, target_node_type) 是否在合法组合列表中
    pair_valid = any(
        src.value == source_node_type and tgt.value == target_node_type
        for src, tgt in constraints
    )

    if not pair_valid:
        # 构造合法组合的可读描述
        allowed = ", ".join(
            f"({src.value}, {tgt.value})" for src, tgt in constraints
        )
        return ValidationResult.fail(
            errors=[
                f"边类型 {edge_type!r} 不允许 ({source_node_type!r}, "
                f"{target_node_type!r}) 组合，"
                f"合法组合: {allowed}"
            ],
        )

    return ValidationResult.ok()
