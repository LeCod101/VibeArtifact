"""
SchemaTranslator 模块 — 数据模型翻译器。

将 schema agent 输出的 SchemaPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 EntitySpec → create_node（类型 entity）
2. 每个 EndpointSpec → create_node（类型 endpoint）
3. 从端点路径推断关联实体，创建 endpoint → entity 的 queries/mutates 边
4. 从 relationships 字段推断实体间依赖，创建 entity → entity 的 depends_on 边
"""

import re

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import SchemaPlan

from .base import BaseTranslator, TranslatorResult

# 合法的字段数据类型集合，用于校验 FieldSpec.type
VALID_FIELD_TYPES = frozenset({
    "String", "Text", "Integer", "Float",
    "Boolean", "DateTime", "UUID", "JSON",
})

# 合法的 HTTP 方法集合
VALID_HTTP_METHODS = frozenset({
    "GET", "POST", "PUT", "DELETE", "PATCH",
})

# 每个实体必须包含的基础字段名称
REQUIRED_BASE_FIELDS = frozenset({
    "id", "created_at", "updated_at",
})


class SchemaTranslator(BaseTranslator):
    """
    数据模型翻译器。

    将 SchemaPlan（数据模型与 API 契约）翻译为 IR 操作列表。
    产生 entity 节点、endpoint 节点，以及它们之间的关联边：
    - endpoint → entity: queries 边（GET 请求）或 mutates 边（POST/PUT/DELETE/PATCH）
    - entity → entity: depends_on 边（外键依赖关系）
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 SchemaPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型和基本完整性
        2. 为每个 EntitySpec 创建 entity 类型节点
        3. 为每个 EndpointSpec 创建 endpoint 类型节点
        4. 推断 endpoint → entity 的关联边（queries/mutates）
        5. 推断 entity → entity 的依赖边（depends_on）

        - high_level_output: SchemaPlan 实例
        - 返回: TranslatorResult，包含创建节点和边的操作列表
        """
        if not isinstance(high_level_output, SchemaPlan):
            return TranslatorResult(
                operations=[],
                warnings=["SchemaTranslator 期望 SchemaPlan 类型，实际收到 "
                           f"{type(high_level_output).__name__}"],
            )

        plan: SchemaPlan = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：实体列表为空
        if not plan.entities:
            return TranslatorResult(
                operations=[],
                warnings=["entities 列表为空，至少需要一个数据实体才能继续"],
            )

        # 边界检查：端点列表为空
        if not plan.endpoints:
            warnings.append("endpoints 列表为空，将只创建实体节点，无 API 端点")

        # 记录实体名称到操作索引的映射，用于后续创建边
        entity_name_to_op_index: dict[str, int] = {}
        # 记录端点操作索引列表
        endpoint_op_indices: list[int] = []

        # ==============================
        # 阶段 1: 创建 entity 节点
        # ==============================
        for entity in plan.entities:
            # 校验必备字段是否存在
            field_names = {field.name for field in entity.fields}
            missing_base_fields = REQUIRED_BASE_FIELDS - field_names
            if missing_base_fields:
                missing_str = "、".join(sorted(missing_base_fields))
                warnings.append(
                    f"实体 '{entity.name}' 缺少必备字段：{missing_str}，"
                    "每个实体必须包含 id、created_at、updated_at"
                )

            # 校验字段类型是否合法
            for field in entity.fields:
                if field.type not in VALID_FIELD_TYPES:
                    warnings.append(
                        f"实体 '{entity.name}' 的字段 '{field.name}' "
                        f"使用了非标准类型 '{field.type}'，"
                        f"建议使用：{', '.join(sorted(VALID_FIELD_TYPES))}"
                    )

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
            entity_name_to_op_index[entity.name] = len(operations)
            operations.append(op)

        # ==============================
        # 阶段 2: 创建 endpoint 节点
        # ==============================
        for endpoint in plan.endpoints:
            # HTTP 方法统一转为大写，确保与 HttpMethod 枚举一致
            method_upper = endpoint.method.upper()

            # 校验 HTTP 方法是否合法
            if method_upper not in VALID_HTTP_METHODS:
                warnings.append(
                    f"端点 '{endpoint.path}' 使用了非法 HTTP 方法 "
                    f"'{method_upper}'，合法值：GET/POST/PUT/DELETE/PATCH"
                )

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
            endpoint_op_indices.append(len(operations))
            operations.append(op)

        # ==============================
        # 阶段 3: 创建 endpoint → entity 关联边
        # ==============================
        # 将实体名称转为小写复数形式的映射表，用于路径匹配
        entity_plural_map = self._build_entity_plural_map(
            list(entity_name_to_op_index.keys())
        )

        for ep_idx, endpoint in zip(endpoint_op_indices, plan.endpoints):
            # 从端点路径中提取资源名称
            resource_name = self._extract_resource_from_path(endpoint.path)
            if not resource_name:
                continue

            # 查找资源名称对应的实体
            matched_entity = entity_plural_map.get(resource_name)
            if not matched_entity:
                continue

            entity_op_idx = entity_name_to_op_index.get(matched_entity)
            if entity_op_idx is None:
                continue

            # 根据 HTTP 方法决定边类型
            method_upper = endpoint.method.upper()
            if method_upper == "GET":
                # GET 请求 → queries 边
                edge_type = EdgeType.QUERIES
            else:
                # POST/PUT/DELETE/PATCH → mutates 边
                edge_type = EdgeType.MUTATES

            edge_op = {
                "operation_type": OperationType.CREATE_EDGE,
                "edge_type": edge_type,
                # 通过操作索引引用（_ref:op_index 格式）
                "source_node_id": f"_ref:{ep_idx}",
                "target_node_id": f"_ref:{entity_op_idx}",
            }
            operations.append(edge_op)

        # ==============================
        # 阶段 4: 创建 entity → entity 依赖边
        # ==============================
        # 基于 relationships 字段解析实体间的外键依赖关系
        for entity in plan.entities:
            source_op_idx = entity_name_to_op_index.get(entity.name)
            if source_op_idx is None:
                continue

            for rel_text in entity.relationships:
                # 解析 "belongs_to User" 或 "has_many Post" 格式
                target_entity = self._parse_relationship_target(rel_text)
                if not target_entity:
                    continue

                target_op_idx = entity_name_to_op_index.get(target_entity)
                if target_op_idx is None:
                    warnings.append(
                        f"实体 '{entity.name}' 的关联关系 '{rel_text}' "
                        f"引用了未定义的实体 '{target_entity}'"
                    )
                    continue

                # 避免自引用产生 depends_on 边
                if source_op_idx == target_op_idx:
                    continue

                # belongs_to 表示当前实体依赖目标实体（外键在当前实体上）
                if rel_text.lower().startswith("belongs_to"):
                    edge_op = {
                        "operation_type": OperationType.CREATE_EDGE,
                        "edge_type": EdgeType.DEPENDS_ON,
                        "source_node_id": f"_ref:{source_op_idx}",
                        "target_node_id": f"_ref:{target_op_idx}",
                    }
                    operations.append(edge_op)

        return TranslatorResult(operations=operations, warnings=warnings)

    @staticmethod
    def _build_entity_plural_map(entity_names: list[str]) -> dict[str, str]:
        """
        构建实体名称的小写复数形式映射表。

        将 PascalCase 实体名转换为可能的 URL 资源名称格式，
        用于将端点路径中的资源名匹配回实体。

        - entity_names: 实体名称列表（PascalCase 格式）
        - 返回: 资源名称 → 实体名称的映射字典

        示例：
        - "User" → {"users": "User", "user": "User"}
        - "TodoItem" → {"todoitems": "TodoItem", "todoitem": "TodoItem",
                        "todo-items": "TodoItem", "todo_items": "TodoItem"}
        - "Post" → {"posts": "Post", "post": "Post"}
        """
        plural_map: dict[str, str] = {}

        for name in entity_names:
            # 基础小写形式
            lower = name.lower()
            plural_map[lower] = name

            # 简单复数形式（加 s）
            plural_map[lower + "s"] = name

            # 处理 PascalCase 转 kebab-case 和 snake_case
            # 如 "TodoItem" → "todo-items" / "todo_items"
            parts = re.findall(r"[A-Z][a-z]*", name)
            if len(parts) > 1:
                kebab = "-".join(p.lower() for p in parts)
                snake = "_".join(p.lower() for p in parts)
                plural_map[kebab] = name
                plural_map[kebab + "s"] = name
                plural_map[snake] = name
                plural_map[snake + "s"] = name

                # 连写形式（不分隔）
                joined = "".join(p.lower() for p in parts)
                plural_map[joined] = name
                plural_map[joined + "s"] = name

        return plural_map

    @staticmethod
    def _extract_resource_from_path(path: str) -> str | None:
        """
        从 API 路径中提取第一个资源名称段。

        去除 "/api/" 前缀后，取第一个非参数路径段作为资源名。
        跳过 "auth" 等非资源路径段。

        - path: API 端点路径，如 "/api/posts/{id}" 或 "/api/auth/login"
        - 返回: 资源名称字符串，或 None（无法提取时）

        示例：
        - "/api/posts" → "posts"
        - "/api/posts/{id}" → "posts"
        - "/api/posts/{post_id}/comments" → "posts"
        - "/api/auth/login" → None（auth 不是资源）
        """
        # 去除 /api/ 前缀
        cleaned = path.strip("/")
        if cleaned.startswith("api/"):
            cleaned = cleaned[4:]

        # 分割路径段
        segments = cleaned.split("/")
        if not segments:
            return None

        # 跳过非资源段
        non_resource_segments = {"auth"}
        for segment in segments:
            # 跳过路径参数
            if segment.startswith("{"):
                continue
            # 跳过非资源段
            if segment in non_resource_segments:
                return None
            # 返回第一个有效资源段
            return segment

        return None

    @staticmethod
    def _parse_relationship_target(rel_text: str) -> str | None:
        """
        从关联关系描述文本中解析目标实体名称。

        支持的格式：
        - "belongs_to User"
        - "has_many Post"
        - "has_one Profile"

        - rel_text: 关联关系描述文本
        - 返回: 目标实体名称，或 None（无法解析时）
        """
        # 标准化：去除多余空格
        parts = rel_text.strip().split()
        if len(parts) < 2:
            return None

        # 取最后一个词作为实体名称
        return parts[-1]
