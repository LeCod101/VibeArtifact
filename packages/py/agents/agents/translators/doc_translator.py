"""
DocTranslator 模块 — 文档翻译器。

将 doc agent 输出的 DocPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 FileSpec → create_node（类型 doc）
2. 节点 props 包含 path、content、format
3. format 固定为 "markdown"
"""

from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import DocPlan

from .base import BaseTranslator, TranslatorResult

# 必须包含的文档文件路径集合
_REQUIRED_DOC_PATHS = frozenset({
    "README.md",
    "docs/api.md",
})


class DocTranslator(BaseTranslator):
    """
    文档翻译器。

    将 DocPlan（文档文件列表）翻译为 IR 操作列表。
    每个文档文件对应一个 doc 类型的 IR 节点。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 DocPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型
        2. 检查必须包含的文档文件是否存在
        3. 为每个 FileSpec 创建 doc 类型节点

        - high_level_output: DocPlan 实例
        - 返回: TranslatorResult，包含创建节点的操作列表
        """
        if not isinstance(high_level_output, DocPlan):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "DocTranslator 期望 DocPlan 类型，实际收到 "
                    f"{type(high_level_output).__name__}"
                ],
            )

        plan: DocPlan = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：files 列表为空
        if not plan.files:
            return TranslatorResult(
                operations=[],
                warnings=["files 列表为空，至少需要 README.md 和 docs/api.md"],
            )

        # 检查必须包含的文档文件
        existing_paths = {f.path for f in plan.files}
        missing_paths = _REQUIRED_DOC_PATHS - existing_paths
        if missing_paths:
            missing_str = "、".join(sorted(missing_paths))
            warnings.append(
                f"缺少必须的文档文件：{missing_str}，"
                "DocPlan 至少需要包含 README.md 和 docs/api.md"
            )

        # 为每个文档文件创建 doc 节点
        for file_spec in plan.files:
            # 校验 path 不为空
            if not file_spec.path or not file_spec.path.strip():
                warnings.append(
                    "发现 path 为空的文件条目，已跳过"
                )
                continue

            # 校验 content 不为空
            if not file_spec.content or not file_spec.content.strip():
                warnings.append(
                    f"文件 '{file_spec.path}' 的 content 为空，已跳过"
                )
                continue

            # 从路径中提取文件名作为标签
            label = file_spec.path.rsplit("/", maxsplit=1)[-1]

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.DOC,
                "label": label,
                "props": {
                    "path": file_spec.path,
                    "content": file_spec.content,
                    "format": "markdown",
                },
            }
            operations.append(op)

        # 如果所有文件都被跳过，给出额外警告
        if not operations:
            warnings.append(
                "所有文档文件均被跳过（path 或 content 为空），未创建任何 IR 节点"
            )

        return TranslatorResult(operations=operations, warnings=warnings)
