"""
Translator 统一导出模块。

汇总导出所有 Translator 类、TranslatorResult、TRANSLATOR_MAP 映射表
以及 get_translator() 工厂函数。

外部使用方式：
    from agents.translators import get_translator, TranslatorResult
    translator = get_translator("intent")
    result = translator.translate(scope_draft)
"""

from .backend_translator import BackendTranslator
from .base import BaseTranslator, TranslatorResult
from .contraction_translator import ContractionTranslator
from .diagram_translator import DiagramTranslator
from .doc_translator import DocTranslator
from .export_translator import ExportTranslator
from .frontend_translator import FrontendTranslator
from .intent_translator import IntentTranslator
from .planner_translator import PlannerTranslator
from .qa_translator import QATranslator
from .schema_translator import SchemaTranslator

# agent_id → Translator 实例的映射
# 所有 Translator 均为轻量无状态对象，模块级实例化是有意为之：
# 避免每次调用 get_translator() 时重复创建实例，且无共享可变状态风险
TRANSLATOR_MAP: dict[str, BaseTranslator] = {
    "intent": IntentTranslator(),
    "contraction": ContractionTranslator(),
    "planner": PlannerTranslator(),
    "schema": SchemaTranslator(),
    "backend": BackendTranslator(),
    "frontend": FrontendTranslator(),
    "doc": DocTranslator(),
    "diagram": DiagramTranslator(),
    "qa": QATranslator(),
    "export": ExportTranslator(),
}


def get_translator(agent_id: str) -> BaseTranslator:
    """
    根据 agent_id 获取对应的 Translator 实例。

    - agent_id: Agent 标识符（如 "intent", "schema" 等）
    - 返回: 对应的 BaseTranslator 子类实例
    - 异常: KeyError 当 agent_id 不存在于 TRANSLATOR_MAP 中
    """
    if agent_id not in TRANSLATOR_MAP:
        available = ", ".join(sorted(TRANSLATOR_MAP.keys()))
        raise KeyError(
            f"未知的 agent_id: '{agent_id}'，"
            f"可用的 agent_id: {available}"
        )
    return TRANSLATOR_MAP[agent_id]


__all__ = [
    # 基类和结果类型
    "BaseTranslator",
    "TranslatorResult",
    # 具体翻译器
    "IntentTranslator",
    "ContractionTranslator",
    "PlannerTranslator",
    "SchemaTranslator",
    "BackendTranslator",
    "FrontendTranslator",
    "DocTranslator",
    "DiagramTranslator",
    "QATranslator",
    "ExportTranslator",
    # 映射表和工厂函数
    "TRANSLATOR_MAP",
    "get_translator",
]
