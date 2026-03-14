"""
IntentTranslator 模块 — 意图收缩翻译器。

将 intent/contraction agent 输出的 ScopeDraft 翻译为 IROperation 列表。

翻译规则：
1. 每个 ScopeItem → create_node（类型 scope）
2. 每个 risk → create_node（类型 risk）
3. 第一个 risk 与第一个 scope 之间建立 references 边
"""

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import ScopeDraft

from .base import BaseTranslator, TranslatorResult


class IntentTranslator(BaseTranslator):
    """
    意图收缩翻译器。

    将 ScopeDraft（功能范围草案）翻译为 IR 操作列表。
    产生 scope 节点、risk 节点，以及它们之间的 references 边。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 ScopeDraft 翻译为 IROperation 列表。

        翻译逻辑：
        1. 为每个 ScopeItem 创建 scope 类型节点
        2. 为每个 risk 文本创建 risk 类型节点
        3. 如果同时存在 risk 和 scope，在第一个 risk 与第一个 scope 之间建立 references 边

        - high_level_output: ScopeDraft 实例
        - 返回: TranslatorResult，包含创建节点和边的操作列表
        """
        if not isinstance(high_level_output, ScopeDraft):
            return TranslatorResult(
                operations=[],
                warnings=["IntentTranslator 期望 ScopeDraft 类型，实际收到 "
                           f"{type(high_level_output).__name__}"],
            )

        draft: ScopeDraft = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：product_name 为空
        if not draft.product_name or not draft.product_name.strip():
            warnings.append("product_name 为空，请提供产品名称")

        # 边界检查：scopes 为空列表
        if not draft.scopes:
            return TranslatorResult(
                operations=[],
                warnings=["scopes 列表为空，至少需要一个功能模块才能继续"],
            )

        # 边界检查：scopes 超过 10 个（范围过大）
        if len(draft.scopes) > 10:
            warnings.append(
                f"scopes 数量为 {len(draft.scopes)}，超过 10 个，"
                "建议收缩功能范围以控制 MVP 复杂度"
            )

        # 记录已创建节点的临时 ID（使用列表索引作为占位引用）
        scope_op_indices: list[int] = []
        risk_op_indices: list[int] = []

        # 翻译每个 ScopeItem 为 create_node 操作
        for scope_item in draft.scopes:
            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.SCOPE,
                "label": scope_item.name,
                "props": {
                    "name": scope_item.name,
                    "description": scope_item.description,
                    "priority": scope_item.priority,
                    "tags": scope_item.tags,
                },
            }
            scope_op_indices.append(len(operations))
            operations.append(op)

        # 翻译每个 risk 文本为 create_node 操作
        for risk_text in draft.risks:
            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.RISK,
                "label": risk_text,
                "props": {
                    "title": risk_text,
                    "description": risk_text,
                    "severity": "medium",
                    "status": "open",
                },
            }
            risk_op_indices.append(len(operations))
            operations.append(op)

        # 如果同时有 risk 和 scope，建立 references 边
        # 边的 source/target 需要节点 ID，但此处节点 ID 尚未生成
        # 因此使用 _ref 字段标记引用关系，由 apply_operations 解析
        if risk_op_indices and scope_op_indices:
            # 第一个 risk 引用第一个 scope
            edge_op = {
                "operation_type": OperationType.CREATE_EDGE,
                "edge_type": EdgeType.REFERENCES,
                # 通过操作索引引用（_ref:op_index 格式）
                "source_node_id": f"_ref:{risk_op_indices[0]}",
                "target_node_id": f"_ref:{scope_op_indices[0]}",
            }
            operations.append(edge_op)

        # 记录延后项作为警告
        if draft.deferred_items:
            deferred_summary = "、".join(draft.deferred_items)
            warnings.append(f"以下功能被延后：{deferred_summary}")

        return TranslatorResult(operations=operations, warnings=warnings)
