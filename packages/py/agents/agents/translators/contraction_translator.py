"""
ContractionTranslator 模块 — 功能收缩翻译器。

将 contraction agent 输出的 ScopeDraft 翻译为 IROperation 列表。
与 IntentTranslator 不同，ContractionTranslator 额外处理：
1. 为保留的功能创建 scope 节点
2. 为延后的功能创建 decision 节点（标记为 deferred）
3. 为收缩风险创建 risk 节点
4. 建立 scope → decision 之间的 references 边
"""

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import ScopeDraft

from .base import BaseTranslator, TranslatorResult


class ContractionTranslator(BaseTranslator):
    """
    功能收缩翻译器。

    将收缩后的 ScopeDraft 翻译为 IR 操作列表。
    产出 scope 节点（保留的功能）、decision 节点（延后的功能）、
    risk 节点（收缩风险），以及它们之间的 references 边。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 ScopeDraft 翻译为 IROperation 列表。

        翻译逻辑：
        1. 为每个保留的 ScopeItem 创建 scope 类型节点
        2. 为每个 deferred_item 创建 decision 类型节点，标记为 deferred
        3. 为每个 risk 创建 risk 类型节点
        4. 在第一个 scope 和第一个 decision 之间建立 references 边
        5. 在第一个 risk 和第一个 scope 之间建立 references 边

        - high_level_output: ScopeDraft 实例
        - 返回: TranslatorResult，包含创建节点和边的操作列表
        """
        if not isinstance(high_level_output, ScopeDraft):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "ContractionTranslator 期望 ScopeDraft 类型，"
                    f"实际收到 {type(high_level_output).__name__}"
                ],
            )

        draft: ScopeDraft = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 记录各类节点在 operations 列表中的索引，用于后续创建边
        scope_op_indices: list[int] = []
        decision_op_indices: list[int] = []
        risk_op_indices: list[int] = []

        # 翻译每个保留的 ScopeItem 为 scope 节点
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

        # 翻译每个延后功能为 decision 节点，标记为 deferred
        for deferred_text in draft.deferred_items:
            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.DECISION,
                "label": deferred_text,
                "props": {
                    "title": deferred_text,
                    "description": f"延后到后续版本：{deferred_text}",
                    "status": "pending",
                    "alternatives": None,
                },
            }
            decision_op_indices.append(len(operations))
            operations.append(op)

        # 翻译每个 risk 文本为 risk 节点
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

        # scope → decision 之间建立 references 边
        # 将每个 decision 关联到第一个 scope（表示"该功能从此 scope 延后"）
        if scope_op_indices and decision_op_indices:
            for decision_idx in decision_op_indices:
                edge_op = {
                    "operation_type": OperationType.CREATE_EDGE,
                    "edge_type": EdgeType.REFERENCES,
                    # 通过操作索引引用（_ref:op_index 格式）
                    "source_node_id": f"_ref:{scope_op_indices[0]}",
                    "target_node_id": f"_ref:{decision_idx}",
                }
                operations.append(edge_op)

        # risk → scope 之间建立 references 边
        if risk_op_indices and scope_op_indices:
            # 第一个 risk 引用第一个 scope
            edge_op = {
                "operation_type": OperationType.CREATE_EDGE,
                "edge_type": EdgeType.REFERENCES,
                "source_node_id": f"_ref:{risk_op_indices[0]}",
                "target_node_id": f"_ref:{scope_op_indices[0]}",
            }
            operations.append(edge_op)

        # 记录延后项汇总作为警告
        if draft.deferred_items:
            deferred_summary = "、".join(draft.deferred_items)
            warnings.append(f"以下功能被收缩延后：{deferred_summary}")

        return TranslatorResult(operations=operations, warnings=warnings)
