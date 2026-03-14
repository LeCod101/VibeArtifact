"""
QATranslator 模块 — 质量检查翻译器。

将 qa agent 输出的 QAReport 翻译为 IROperation 列表。

翻译规则：
1. passed=true → 创建一个 decision 节点（qa_passed）
2. passed=false → 为每个 critical issue 创建一个 risk 节点，
   然后创建一个 decision 节点（qa_failed）
3. warning/info 级别的问题只记录在 decision 节点的 props 中，不单独建节点
"""

from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import QAReport

from .base import BaseTranslator, TranslatorResult

# 合法的严重度取值
VALID_SEVERITIES = frozenset({"critical", "warning", "info"})

# 合法的问题分类取值
VALID_CATEGORIES = frozenset({
    "missing_file", "schema_mismatch", "import_error", "config_error",
})


class QATranslator(BaseTranslator):
    """
    质量检查翻译器。

    将 QAReport（质量检查报告）翻译为 IR 操作列表。
    产生 decision 节点和 risk 节点：
    - passed=true: 一个 decision 节点（qa_passed）
    - passed=false: 每个 critical issue 一个 risk 节点 + 一个 decision 节点（qa_failed）
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 QAReport 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型
        2. 校验 issues 中的 severity 和 category
        3. 如果 passed=false，为每个 critical issue 创建 risk 节点
        4. 创建 decision 节点记录检查结果

        - high_level_output: QAReport 实例
        - 返回: TranslatorResult，包含创建节点的操作列表
        """
        if not isinstance(high_level_output, QAReport):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "QATranslator 期望 QAReport 类型，实际收到 "
                    f"{type(high_level_output).__name__}"
                ],
            )

        report: QAReport = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 校验 issues 中的字段合法性
        for idx, issue in enumerate(report.issues):
            if issue.severity not in VALID_SEVERITIES:
                warnings.append(
                    f"第 {idx + 1} 个 issue 的 severity '{issue.severity}' "
                    f"不在合法取值范围内，合法值：{', '.join(sorted(VALID_SEVERITIES))}"
                )
            if issue.category not in VALID_CATEGORIES:
                warnings.append(
                    f"第 {idx + 1} 个 issue 的 category '{issue.category}' "
                    f"不在合法取值范围内，合法值：{', '.join(sorted(VALID_CATEGORIES))}"
                )

        # 统计各级别 issue 数量
        critical_count = sum(
            1 for issue in report.issues if issue.severity == "critical"
        )
        warning_count = sum(
            1 for issue in report.issues if issue.severity == "warning"
        )
        info_count = sum(
            1 for issue in report.issues if issue.severity == "info"
        )

        # 校验 passed 与 critical 数量的一致性
        if report.passed and critical_count > 0:
            warnings.append(
                f"passed=true 但存在 {critical_count} 个 critical 级别问题，"
                "翻译器将按 passed=true 处理，但建议 QA agent 修正输出"
            )
        if not report.passed and critical_count == 0:
            warnings.append(
                "passed=false 但没有 critical 级别问题，"
                "翻译器将按 passed=false 处理，但建议 QA agent 修正输出"
            )

        # ==============================
        # 阶段 1: 为 critical issue 创建 risk 节点
        # ==============================
        if not report.passed:
            for issue in report.issues:
                # 只为 critical 级别的问题创建独立的 risk 节点
                if issue.severity != "critical":
                    continue

                risk_op = {
                    "operation_type": OperationType.CREATE_NODE,
                    "node_type": NodeType.RISK,
                    "label": f"QA: {issue.category} - {issue.affected_file}",
                    "props": {
                        "title": f"QA 检查失败: {issue.category}",
                        "description": issue.description,
                        "severity": "high",
                        "mitigation": None,
                        "status": "open",
                    },
                }
                operations.append(risk_op)

        # ==============================
        # 阶段 2: 创建 decision 节点
        # ==============================
        if report.passed:
            decision_op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.DECISION,
                "label": "QA 检查通过",
                "props": {
                    "title": "QA 检查通过",
                    "description": report.summary,
                    "status": "accepted",
                    "alternatives": None,
                },
            }
        else:
            decision_op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.DECISION,
                "label": "QA 检查未通过",
                "props": {
                    "title": "QA 检查未通过",
                    "description": (
                        f"{report.summary} "
                        f"(critical: {critical_count}, "
                        f"warning: {warning_count}, "
                        f"info: {info_count})"
                    ),
                    "status": "pending",
                    "alternatives": [
                        f"共 {len(report.issues)} 个问题待处理",
                    ],
                },
            }
        operations.append(decision_op)

        return TranslatorResult(operations=operations, warnings=warnings)
