"""
Translator 抽象基类模块。

Translator 是 Agent 高层输出与 IR 操作之间的桥梁。
每个 Agent 对应一个 Translator，负责将该 Agent 输出的高层结构体
（如 ScopeDraft、SchemaPlan 等）翻译为 IROperation 列表。

核心设计原则：
- 翻译是确定性的纯 Python 逻辑，不调用 LLM
- 输入是 Pydantic BaseModel 子类，输出是 TranslatorResult
- 操作列表可被 apply_operations() 直接消费
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class TranslatorResult(BaseModel):
    """
    翻译结果。

    包含翻译后的 IROperation 列表和翻译过程中产生的警告。
    - operations: 每项是一个字典，包含 "operation_type" 和对应的 payload 字段
    - warnings: 翻译过程中产生的警告信息列表
    """

    operations: list[dict]
    warnings: list[str] = []


class BaseTranslator(ABC):
    """
    Translator 抽象基类。

    将 Agent 高层输出翻译为 IROperation 列表。
    翻译是确定性的纯 Python 逻辑，不调用 LLM。

    子类必须实现 translate() 方法，将特定的高层结构体
    转换为可被 apply_operations() 消费的操作列表。
    """

    @abstractmethod
    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将高层结构体翻译为 IROperation 列表。

        - high_level_output: Agent 输出的高层结构体（如 ScopeDraft, SchemaPlan 等）
        - 返回: TranslatorResult，包含可被 apply_operations() 消费的操作列表
        """
        ...
