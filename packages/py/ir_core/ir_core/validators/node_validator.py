"""
节点属性校验器模块。

根据节点类型查找对应的 Pydantic model，校验 props 字典是否符合类型定义。
未知节点类型或属性不合法时返回包含详细错误信息的 ValidationResult。
"""

from pydantic import ValidationError

from ir_core.schema.node_types import NODE_PROPS_MAP
from ir_core.validators.result import ValidationResult


def validate_node_props(node_type: str, props: dict) -> ValidationResult:
    """
    校验节点 props 是否符合类型定义。

    - node_type: 节点类型字符串（对应 NodeType 枚举值）
    - props: 节点属性字典

    校验逻辑：
    1. 未知 node_type → 返回错误
    2. props 不符合对应 Pydantic model → 返回错误（含详细字段信息）
    3. 校验通过 → 返回 ok
    """

    # 在 NODE_PROPS_MAP 中查找对应的 props model
    props_model = None
    for key, model in NODE_PROPS_MAP.items():
        if key.value == node_type:
            props_model = model
            break

    # 未知节点类型
    if props_model is None:
        return ValidationResult.fail(
            errors=[f"未知的节点类型: {node_type!r}"],
        )

    # 使用对应 model 校验 props
    try:
        props_model.model_validate(props)
    except ValidationError as exc:
        # 从 Pydantic ValidationError 中提取每条错误的详细信息
        errors = []
        for err in exc.errors():
            # 拼接字段路径，例如 "fields -> 0 -> name"
            loc = " -> ".join(str(part) for part in err["loc"])
            msg = err["msg"]
            errors.append(
                f"节点类型 {node_type!r} 属性校验失败 [{loc}]: {msg}"
            )
        return ValidationResult.fail(errors=errors)

    return ValidationResult.ok()
