"""
SchemaTranslator 测试模块。

测试 SchemaTranslator 将 SchemaPlan 翻译为 IROperation 列表的逻辑，
包括实体节点、端点节点、关联边和边界情况处理。
"""

import pytest
from agents.schemas.high_level import (
    EndpointSpec,
    EntitySpec,
    FieldSpec,
    SchemaPlan,
)
from agents.translators.schema_translator import SchemaTranslator
from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType


# ============================================================
# 辅助函数
# ============================================================

def _make_todo_schema_plan() -> SchemaPlan:
    """
    构造 Todo 应用的标准 SchemaPlan。

    包含 User 和 Todo 两个实体，以及对应的 CRUD 端点。
    """
    return SchemaPlan(
        entities=[
            EntitySpec(
                name="User",
                fields=[
                    FieldSpec(name="id", type="UUID", primary=True, nullable=False),
                    FieldSpec(name="email", type="String", unique=True),
                    FieldSpec(name="created_at", type="DateTime"),
                    FieldSpec(name="updated_at", type="DateTime"),
                ],
                relationships=["has_many Todo"],
            ),
            EntitySpec(
                name="Todo",
                fields=[
                    FieldSpec(name="id", type="UUID", primary=True, nullable=False),
                    FieldSpec(name="title", type="String"),
                    FieldSpec(name="done", type="Boolean", default="false"),
                    FieldSpec(name="created_at", type="DateTime"),
                    FieldSpec(name="updated_at", type="DateTime"),
                ],
                relationships=["belongs_to User"],
            ),
        ],
        endpoints=[
            EndpointSpec(
                method="GET",
                path="/api/users",
                description="获取用户列表",
            ),
            EndpointSpec(
                method="POST",
                path="/api/todos",
                description="创建待办事项",
                auth_required=True,
            ),
            EndpointSpec(
                method="DELETE",
                path="/api/todos/{id}",
                description="删除待办事项",
                auth_required=True,
            ),
        ],
    )


# ============================================================
# SchemaTranslator 测试
# ============================================================

class TestSchemaTranslator:
    """SchemaTranslator 翻译逻辑测试。"""

    def test_entity_nodes(self):
        """EntitySpec → entity 节点：数量和类型正确。"""
        translator = SchemaTranslator()
        plan = _make_todo_schema_plan()
        result = translator.translate(plan)

        # 筛选 entity 类型的 create_node 操作
        entity_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
            and op["node_type"] == NodeType.ENTITY
        ]

        # 2 个实体
        assert len(entity_ops) == 2

        # 验证实体名称
        names = {op["label"] for op in entity_ops}
        assert names == {"User", "Todo"}

        # 验证 props 包含必要字段
        for op in entity_ops:
            assert "name" in op["props"]
            assert "fields" in op["props"]

    def test_endpoint_nodes(self):
        """EndpointSpec → endpoint 节点：数量和类型正确。"""
        translator = SchemaTranslator()
        plan = _make_todo_schema_plan()
        result = translator.translate(plan)

        # 筛选 endpoint 类型的 create_node 操作
        endpoint_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
            and op["node_type"] == NodeType.ENDPOINT
        ]

        # 3 个端点
        assert len(endpoint_ops) == 3

        # 验证 method 都是大写
        for op in endpoint_ops:
            method = op["props"]["method"]
            assert method == method.upper()

    def test_entity_endpoint_edges(self):
        """endpoint → entity 关联边正确创建。"""
        translator = SchemaTranslator()
        plan = _make_todo_schema_plan()
        result = translator.translate(plan)

        # 筛选 create_edge 操作
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]

        # 应该有关联边：
        # GET /api/users → User (queries)
        # POST /api/todos → Todo (mutates)
        # DELETE /api/todos/{id} → Todo (mutates)
        # belongs_to User → depends_on 边
        assert len(edge_ops) >= 3

        # 检查有 queries 类型的边
        queries_edges = [
            op for op in edge_ops if op["edge_type"] == EdgeType.QUERIES
        ]
        assert len(queries_edges) >= 1

        # 检查有 mutates 类型的边
        mutates_edges = [
            op for op in edge_ops if op["edge_type"] == EdgeType.MUTATES
        ]
        assert len(mutates_edges) >= 1

    def test_empty_entities(self):
        """空 entities 列表返回空操作 + 警告。"""
        translator = SchemaTranslator()
        plan = SchemaPlan(
            entities=[],
            endpoints=[
                EndpointSpec(
                    method="GET",
                    path="/api/test",
                    description="测试端点",
                ),
            ],
        )
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert len(result.warnings) >= 1
        assert "entities 列表为空" in result.warnings[0]

    def test_empty_endpoints_produces_warning(self):
        """空 endpoints 列表产生警告但仍创建实体节点。"""
        translator = SchemaTranslator()
        plan = SchemaPlan(
            entities=[
                EntitySpec(
                    name="User",
                    fields=[
                        FieldSpec(name="id", type="UUID", primary=True),
                        FieldSpec(name="created_at", type="DateTime"),
                        FieldSpec(name="updated_at", type="DateTime"),
                    ],
                ),
            ],
            endpoints=[],
        )
        result = translator.translate(plan)

        # 应该创建 entity 节点
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1

        # 应该有空 endpoints 的警告
        ep_warnings = [w for w in result.warnings if "endpoints 列表为空" in w]
        assert len(ep_warnings) >= 1

    def test_wrong_type(self):
        """传入非 SchemaPlan 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import TaskPlan, TaskStep

        translator = SchemaTranslator()
        wrong_input = TaskPlan(
            steps=[
                TaskStep(
                    step_id="step_1",
                    agent_id="schema",
                    description="test",
                ),
            ],
            estimated_complexity="small",
        )
        result = translator.translate(wrong_input)

        assert len(result.operations) == 0
        assert "SchemaPlan" in result.warnings[0]

    def test_belongs_to_creates_depends_on_edge(self):
        """belongs_to 关系产生 depends_on 边。"""
        translator = SchemaTranslator()
        plan = _make_todo_schema_plan()
        result = translator.translate(plan)

        # 查找 depends_on 类型的边
        depends_edges = [
            op for op in result.operations
            if op.get("operation_type") == OperationType.CREATE_EDGE
            and op.get("edge_type") == EdgeType.DEPENDS_ON
        ]

        # Todo belongs_to User → 应该有一条 depends_on 边
        assert len(depends_edges) >= 1

    def test_missing_base_fields_warning(self):
        """缺少必备字段（id/created_at/updated_at）产生警告。"""
        translator = SchemaTranslator()
        plan = SchemaPlan(
            entities=[
                EntitySpec(
                    name="Incomplete",
                    fields=[
                        FieldSpec(name="name", type="String"),
                    ],
                ),
            ],
            endpoints=[],
        )
        result = translator.translate(plan)

        # 应该有缺少必备字段的警告
        field_warnings = [w for w in result.warnings if "必备字段" in w]
        assert len(field_warnings) >= 1
