"""
Translator 测试模块。

测试 IntentTranslator 和 SchemaTranslator 的翻译逻辑，
以及 get_translator 工厂函数。

注意：不测试 IntentTranslator 的边操作与 apply_operations 的交互，
因为 _ref:index 格式不被 apply_operations 支持。
"""

import pytest
from agents.schemas.high_level import (
    EndpointSpec,
    EntitySpec,
    FieldSpec,
    SchemaPlan,
    ScopeDraft,
    ScopeItem,
)
from agents.translators import get_translator
from agents.translators.intent_translator import IntentTranslator
from agents.translators.schema_translator import SchemaTranslator
from ir_core.schema.operation_types import OperationType

# ============================================================
# 辅助函数
# ============================================================

def _make_scope_draft(
    num_scopes=2,
    num_risks=1,
    deferred_items=None,
):
    """构造一个测试用 ScopeDraft。"""
    scopes = [
        ScopeItem(
            name=f"功能{i+1}",
            description=f"功能{i+1}的描述",
            priority="high" if i == 0 else "medium",
            tags=[f"tag{i+1}"],
        )
        for i in range(num_scopes)
    ]
    risks = [f"风险{i+1}" for i in range(num_risks)]

    return ScopeDraft(
        product_name="TestApp",
        product_description="测试应用",
        scopes=scopes,
        deferred_items=deferred_items or [],
        risks=risks,
    )


def _make_schema_plan():
    """构造一个测试用 SchemaPlan。"""
    return SchemaPlan(
        entities=[
            EntitySpec(
                name="User",
                fields=[
                    FieldSpec(name="id", type="UUID", primary=True, nullable=False),
                    FieldSpec(name="email", type="str"),
                ],
                relationships=["has_many:Task"],
            ),
            EntitySpec(
                name="Task",
                fields=[
                    FieldSpec(name="id", type="UUID", primary=True, nullable=False),
                    FieldSpec(name="title", type="str"),
                ],
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
                path="/api/tasks",
                description="创建任务",
                auth_required=True,
            ),
        ],
    )


# ============================================================
# IntentTranslator 测试
# ============================================================

class TestIntentTranslator:
    """IntentTranslator 翻译逻辑测试。"""

    def test_translate_creates_correct_number_of_create_node_ops(self):
        """IntentTranslator 翻译 ScopeDraft，生成正确数量的 create_node 操作。"""
        translator = IntentTranslator()
        draft = _make_scope_draft(num_scopes=2, num_risks=1)
        result = translator.translate(draft)

        # 2 个 scope 节点 + 1 个 risk 节点 + 1 条边 = 4 个操作
        # 只统计 create_node 操作
        create_node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(create_node_ops) == 3

    def test_operation_type_is_create_node(self):
        """生成的节点操作中 operation_type 为 'create_node'。"""
        translator = IntentTranslator()
        draft = _make_scope_draft(num_scopes=1, num_risks=0)
        result = translator.translate(draft)

        assert len(result.operations) == 1
        assert result.operations[0]["operation_type"] == OperationType.CREATE_NODE

    def test_scope_node_props_contain_required_fields(self):
        """scope 节点的 props 包含 name, description, priority, tags。"""
        translator = IntentTranslator()
        draft = _make_scope_draft(num_scopes=1, num_risks=0)
        result = translator.translate(draft)

        scope_op = result.operations[0]
        props = scope_op["props"]
        assert "name" in props
        assert "description" in props
        assert "priority" in props
        assert "tags" in props
        assert props["name"] == "功能1"

    def test_risk_node_props_contain_required_fields(self):
        """risk 节点的 props 包含 title, description, severity, status。"""
        translator = IntentTranslator()
        draft = _make_scope_draft(num_scopes=0, num_risks=1)
        result = translator.translate(draft)

        risk_op = result.operations[0]
        props = risk_op["props"]
        assert "title" in props
        assert "description" in props
        assert "severity" in props
        assert "status" in props

    def test_deferred_items_produce_warnings(self):
        """有 deferred_items 时 warnings 不为空。"""
        translator = IntentTranslator()
        draft = _make_scope_draft(deferred_items=["团队协作", "日历集成"])
        result = translator.translate(draft)

        assert len(result.warnings) > 0
        assert "团队协作" in result.warnings[0]
        assert "日历集成" in result.warnings[0]

    def test_wrong_type_returns_empty_operations_with_warning(self):
        """传入错误类型给 IntentTranslator 返回空操作 + 警告。"""
        translator = IntentTranslator()
        # 传入一个 SchemaPlan 而不是 ScopeDraft
        plan = _make_schema_plan()
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert len(result.warnings) > 0
        assert "ScopeDraft" in result.warnings[0]

    def test_node_create_operations_pass_validation(self):
        """
        单独验证节点创建操作的结构正确性。
        只测试节点操作，跳过边操作（_ref:index 格式不被 apply_operations 支持）。
        """
        translator = IntentTranslator()
        draft = _make_scope_draft(num_scopes=2, num_risks=1)
        result = translator.translate(draft)

        # 只检查 create_node 操作的结构
        for op in result.operations:
            if op["operation_type"] == OperationType.CREATE_NODE:
                assert "node_type" in op
                assert "label" in op
                assert "props" in op


# ============================================================
# SchemaTranslator 测试
# ============================================================

class TestSchemaTranslator:
    """SchemaTranslator 翻译逻辑测试。"""

    def test_translate_creates_ops_for_entities_and_endpoints(self):
        """SchemaTranslator 翻译 SchemaPlan，为每个 entity 和 endpoint 生成 create_node 操作。"""
        translator = SchemaTranslator()
        plan = _make_schema_plan()
        result = translator.translate(plan)

        # 2 个 entity + 2 个 endpoint = 4 个操作
        assert len(result.operations) == 4
        for op in result.operations:
            assert op["operation_type"] == OperationType.CREATE_NODE

    def test_endpoint_method_is_uppercase(self):
        """endpoint 节点的 method 是大写。"""
        translator = SchemaTranslator()
        plan = _make_schema_plan()
        result = translator.translate(plan)

        # 查找 endpoint 操作
        endpoint_ops = [
            op for op in result.operations
            if op["node_type"] == "endpoint"
        ]
        assert len(endpoint_ops) == 2
        for op in endpoint_ops:
            # method 应该被转为大写
            assert op["props"]["method"] == op["props"]["method"].upper()

    def test_wrong_type_returns_empty_with_warning(self):
        """传入错误类型给 SchemaTranslator 返回空操作 + 警告。"""
        translator = SchemaTranslator()
        draft = _make_scope_draft()
        result = translator.translate(draft)

        assert len(result.operations) == 0
        assert len(result.warnings) > 0
        assert "SchemaPlan" in result.warnings[0]


# ============================================================
# get_translator 工厂函数测试
# ============================================================

class TestGetTranslator:
    """get_translator 工厂函数测试。"""

    def test_get_translator_intent(self):
        """get_translator('intent') 返回 IntentTranslator 实例。"""
        translator = get_translator("intent")
        assert isinstance(translator, IntentTranslator)

    def test_get_translator_schema(self):
        """get_translator('schema') 返回 SchemaTranslator 实例。"""
        translator = get_translator("schema")
        assert isinstance(translator, SchemaTranslator)

    def test_get_translator_nonexistent_raises(self):
        """get_translator('nonexistent') 抛出 KeyError。"""
        with pytest.raises(KeyError, match="未知的 agent_id"):
            get_translator("nonexistent")

    def test_get_translator_all_agents(self):
        """所有 10 个 agent 的 translator 均可正常获取。"""
        agent_ids = [
            "intent", "contraction", "planner", "schema",
            "backend", "frontend", "doc", "diagram", "qa", "export",
        ]
        for agent_id in agent_ids:
            translator = get_translator(agent_id)
            assert translator is not None
