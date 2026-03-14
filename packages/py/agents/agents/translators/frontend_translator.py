"""
FrontendTranslator 模块 — 前端代码翻译器（占位）。

将 frontend agent 输出的 FrontendPlan 翻译为 IROperation 列表。
当前为占位实现，具体逻辑将在 M5 阶段填充。
"""

from pydantic import BaseModel

from .base import BaseTranslator, TranslatorResult


class FrontendTranslator(BaseTranslator):
    """
    前端代码翻译器（占位）。

    将 FrontendPlan 翻译为 IR 操作列表。
    M5 阶段将实现具体的翻译逻辑。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        占位实现，M5 填充具体逻辑。

        - high_level_output: FrontendPlan 实例（当前未使用）
        - 返回: 空操作列表和占位警告
        """
        return TranslatorResult(
            operations=[],
            warnings=["FrontendTranslator 尚未实现，返回空操作列表"],
        )
