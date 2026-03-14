"""
DiagramTranslator 模块 — 图表翻译器。

将 diagram agent 输出的 DiagramPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 DiagramSpec → create_node（类型 diagram）
2. 节点 props 包含 name、diagram_type、content（mermaid）、description
3. 校验至少包含 ER 图和架构图
"""

from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import DiagramPlan

from .base import BaseTranslator, TranslatorResult

# 合法的图表类型集合
_VALID_DIAGRAM_TYPES = frozenset({
    "er", "flowchart", "sequence", "classDiagram",
})

# 必须包含的图表类型集合
_REQUIRED_DIAGRAM_TYPES = frozenset({
    "er", "flowchart",
})

# 图表类型与 Mermaid 语法起始关键字的映射
_MERMAID_PREFIXES: dict[str, list[str]] = {
    "er": ["erDiagram"],
    "flowchart": ["graph", "flowchart"],
    "sequence": ["sequenceDiagram"],
    "classDiagram": ["classDiagram"],
}


class DiagramTranslator(BaseTranslator):
    """
    图表翻译器。

    将 DiagramPlan（Mermaid 图表列表）翻译为 IR 操作列表。
    每个图表对应一个 diagram 类型的 IR 节点。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 DiagramPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型
        2. 检查图表数量和类型完整性
        3. 校验 Mermaid 语法起始关键字
        4. 为每个 DiagramSpec 创建 diagram 类型节点

        - high_level_output: DiagramPlan 实例
        - 返回: TranslatorResult，包含创建节点的操作列表
        """
        if not isinstance(high_level_output, DiagramPlan):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "DiagramTranslator 期望 DiagramPlan 类型，实际收到 "
                    f"{type(high_level_output).__name__}"
                ],
            )

        plan: DiagramPlan = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：diagrams 列表为空
        if not plan.diagrams:
            return TranslatorResult(
                operations=[],
                warnings=["diagrams 列表为空，至少需要 ER 图和架构图"],
            )

        # 检查最少数量
        if len(plan.diagrams) < 2:
            warnings.append(
                f"图表数量不足，至少需要 2 个（ER 图和架构图），"
                f"当前只有 {len(plan.diagrams)} 个"
            )

        # 收集已有的图表类型，用于检查必须包含的类型
        existing_types: set[str] = set()

        # 为每个图表创建 diagram 节点
        for diagram in plan.diagrams:
            # 校验 title 不为空
            if not diagram.title or not diagram.title.strip():
                warnings.append(
                    "发现 title 为空的图表条目，已跳过"
                )
                continue

            # 校验 mermaid_code 不为空
            if not diagram.mermaid_code or not diagram.mermaid_code.strip():
                warnings.append(
                    f"图表 '{diagram.title}' 的 mermaid_code 为空，已跳过"
                )
                continue

            # 校验 diagram_type 合法性
            if diagram.diagram_type not in _VALID_DIAGRAM_TYPES:
                warnings.append(
                    f"图表 '{diagram.title}' 的 diagram_type "
                    f"'{diagram.diagram_type}' 不在合法值列表中，"
                    f"合法值: {', '.join(sorted(_VALID_DIAGRAM_TYPES))}"
                )

            # 校验 Mermaid 语法起始关键字
            mermaid_warning = self._check_mermaid_prefix(
                diagram.title,
                diagram.diagram_type,
                diagram.mermaid_code,
            )
            if mermaid_warning:
                warnings.append(mermaid_warning)

            existing_types.add(diagram.diagram_type)

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.DIAGRAM,
                "label": diagram.title,
                "props": {
                    "name": diagram.title,
                    "diagram_type": diagram.diagram_type,
                    "content": diagram.mermaid_code,
                    "description": f"{diagram.diagram_type} 类型图表：{diagram.title}",
                },
            }
            operations.append(op)

        # 检查必须包含的图表类型
        missing_types = _REQUIRED_DIAGRAM_TYPES - existing_types
        if missing_types:
            type_names = {
                "er": "ER 关系图",
                "flowchart": "架构图",
            }
            missing_str = "、".join(
                type_names.get(t, t) for t in sorted(missing_types)
            )
            warnings.append(
                f"缺少必须的图表类型：{missing_str}"
            )

        # 如果所有图表都被跳过，给出额外警告
        if not operations:
            warnings.append(
                "所有图表均被跳过（title 或 mermaid_code 为空），"
                "未创建任何 IR 节点"
            )

        return TranslatorResult(operations=operations, warnings=warnings)

    @staticmethod
    def _check_mermaid_prefix(
        title: str, diagram_type: str, mermaid_code: str,
    ) -> str | None:
        """
        校验 Mermaid 代码的起始关键字是否与图表类型匹配。

        - title: 图表标题，用于警告信息
        - diagram_type: 声明的图表类型
        - mermaid_code: Mermaid 语法代码
        - 返回: 不匹配时返回警告字符串，匹配返回 None
        """
        expected_prefixes = _MERMAID_PREFIXES.get(diagram_type)
        if not expected_prefixes:
            return None

        # 取 mermaid_code 的首行并去除空白
        first_line = mermaid_code.strip().split("\n")[0].strip()

        # 检查首行是否以预期的关键字开头
        for prefix in expected_prefixes:
            if first_line.startswith(prefix):
                return None

        return (
            f"图表 '{title}' 声明类型为 '{diagram_type}'，"
            f"但 Mermaid 代码未以 {'/'.join(expected_prefixes)} 开头，"
            f"实际首行: '{first_line[:50]}'"
        )
