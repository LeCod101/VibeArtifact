"""
SchemaTranslator 模块 — 数据模型翻译器。

将 schema agent 输出的 SchemaPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 EntitySpec → create_node（类型 entity）
2. 每个 EndpointSpec → create_node（类型 endpoint）
"""

from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import SchemaPlan

from .base import BaseTranslator, TranslatorResult


class SchemaTranslator(BaseTranslator):
    """
    数据模型翻译器。

    将 SchemaPlan（数据模型与 API 契约）翻译为 IR 操作列表。
    产生 entity 节点和 endpoint 节点。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 SchemaPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 为每个 EntitySpec 创建 entity 类型节点，
           将字段列表序列化为 dict 列表
        2. 为每个 EndpointSpec 创建 endpoint 类型节点，
           HTTP 方法统一转为大写以匹配 HttpMethod 枚举

        - high_level_output: SchemaPlan 实例
        - 返回: TranslatorResult，包含创建节点操作列表
        """
        if not isinstance(high_level_output, SchemaPlan):
            return TranslatorResult(
                operations=[],
                warnings=["SchemaTranslator 期望 SchemaPlan 类型，实际收到 "
                           f"{type(high_level_output).__name__}"],
            )

        plan: SchemaPlan = high_level_output
        operations: list[dict] = []

        # 翻译每个 EntitySpec 为 create_node 操作
        for entity in plan.entities:
            # 将 FieldSpec 列表序列化为 dict 列表
            fields_data = [field.model_dump() for field in entity.fields]

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.ENTITY,
                "label": entity.name,
                "props": {
                    "name": entity.name,
                    "fields": fields_data,
                    "relationships": entity.relationships,
                },
            }
            operations.append(op)

        # 翻译每个 EndpointSpec 为 create_node 操作
        for endpoint in plan.endpoints:
            # HTTP 方法统一转为大写，确保与 HttpMethod 枚举一致
            method_upper = endpoint.method.upper()

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.ENDPOINT,
                "label": f"{method_upper} {endpoint.path}",
                "props": {
                    "method": method_upper,
                    "path": endpoint.path,
                    "description": endpoint.description,
                    "request_schema": endpoint.request_schema,
                    "response_schema": endpoint.response_schema,
                    "auth_required": endpoint.auth_required,
                },
            }
            operations.append(op)

        return TranslatorResult(operations=operations)
