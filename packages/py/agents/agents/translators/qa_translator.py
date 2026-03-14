"""
QATranslator 模块 — QA 修复翻译器（占位）。

将 qa agent 输出的 FixPlan 翻译为 IROperation 列表。
当前为占位实现，具体逻辑将在 M5 阶段填充。
"""

from pydantic import BaseModel

from .base import BaseTranslator, TranslatorResult


class QATranslator(BaseTranslator):
    """
    QA 修复翻译器（占位）。

    将 FixPlan 翻译为 IR 操作列表。
    M5 阶段将实现具体的翻译逻辑。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        占位实现，M5 填充具体逻辑。

        - high_level_output: FixPlan 实例（当前未使用）
        - 返回: 空操作列表和占位警告
        """
        return TranslatorResult(
            operations=[],
            warnings=["QATranslator 尚未实现，返回空操作列表"],
        )
