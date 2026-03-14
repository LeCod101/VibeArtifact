"""
ContractionTranslator 测试。

覆盖：
- 基本翻译：scope 节点创建（含字段验证）
- deferred_items → decision 节点（多项）
- risks → risk 节点
- 边创建（scope → decision, risk → scope）
- 空输入处理
- 错误类型处理
- 仅有 deferred 无 scope 的边界情况
"""

from agents.schemas.high_level import ScopeDraft, ScopeItem
from agents.translators.contraction_translator import ContractionTranslator
from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType, Priority
from ir_core.schema.operation_types import OperationType


# ============================================================
# 测试辅助函数
# ============================================================


def _make_scope_draft(
    num_scopes: int = 2,
    deferred_items: list[str] | None = None,
    risks: list[str] | None = None,
) -> ScopeDraft:
    """构造测试用 ScopeDraft。

    参数：
        num_scopes: scope 数量
        deferred_items: 延后的功能列表
        risks: 风险列表

    返回：
        ScopeDraft 实例
    """
    scopes = [
        ScopeItem(
            name=f"功能{i + 1}",
            description=f"功能{i + 1}的描述",
            priority=Priority.HIGH if i == 0 else Priority.MEDIUM,
            tags=[f"tag{i + 1}"],
        )
        for i in range(num_scopes)
    ]
    return ScopeDraft(
        product_name="测试产品",
        product_description="测试描述",
        scopes=scopes,
        deferred_items=deferred_items or [],
        risks=risks or [],
    )


# ============================================================
# ContractionTranslator 测试
# ============================================================


class TestContractionTranslator:
    """ContractionTranslator 翻译逻辑测试。"""

    def test_translate_basic_scopes(self):
        """3 个 scope → 3 个 create_node 操作（scope 类型）。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=3)
        result = translator.translate(draft)

        # 3 个 scope 节点
        create_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(create_ops) == 3

        # 验证全部是 scope 类型
        for op in create_ops:
            assert op["node_type"] == NodeType.SCOPE

        # 验证 props 包含必要字段
        for i, op in enumerate(create_ops):
            assert op["label"] == f"功能{i + 1}"
            assert "name" in op["props"]
            assert "description" in op["props"]
            assert "priority" in op["props"]
            assert "tags" in op["props"]

    def test_translate_creates_scope_nodes(self):
        """保留的 scope 生成正确数量的 scope 节点，且字段完整。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=3)
        result = translator.translate(draft)

        scope_ops = [
            op for op in result.operations
            if (
                op["operation_type"] == OperationType.CREATE_NODE
                and op["node_type"] == NodeType.SCOPE
            )
        ]
        assert len(scope_ops) == 3

        # 验证第一个 scope 节点的具体内容
        first = scope_ops[0]
        assert first["label"] == "功能1"
        assert first["props"]["name"] == "功能1"
        assert first["props"]["description"] == "功能1的描述"
        assert first["props"]["priority"] == Priority.HIGH

    def test_translate_deferred_items(self):
        """有 deferred_items → 生成 decision 节点。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(
            num_scopes=2,
            deferred_items=["团队协作", "日历集成"],
        )
        result = translator.translate(draft)

        # 找出所有 decision 类型节点
        decision_ops = [
            op for op in result.operations
            if op.get("operation_type") == OperationType.CREATE_NODE
            and op.get("node_type") == NodeType.DECISION
        ]
        assert len(decision_ops) == 2

        # 验证 decision 节点内容
        assert decision_ops[0]["label"] == "团队协作"
        assert decision_ops[1]["label"] == "日历集成"

        # 验证 props
        for op in decision_ops:
            assert "title" in op["props"]
            assert "description" in op["props"]
            assert op["props"]["status"] == "pending"

        # 验证警告包含延后信息
        deferred_warnings = [w for w in result.warnings if "延后" in w]
        assert len(deferred_warnings) > 0
        assert "团队协作" in deferred_warnings[0]

    def test_translate_risks(self):
        """有 risks → 生成 risk 节点。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(
            num_scopes=1,
            risks=["需求扩大风险", "技术栈不确定"],
        )
        result = translator.translate(draft)

        # 找出所有 risk 类型节点
        risk_ops = [
            op for op in result.operations
            if op.get("operation_type") == OperationType.CREATE_NODE
            and op.get("node_type") == NodeType.RISK
        ]
        assert len(risk_ops) == 2

        # 验证 risk 节点内容
        assert risk_ops[0]["label"] == "需求扩大风险"
        assert risk_ops[1]["label"] == "技术栈不确定"

        # 验证 props
        for op in risk_ops:
            assert op["props"]["severity"] == "medium"
            assert op["props"]["status"] == "open"

    def test_translate_creates_decision_nodes_for_deferred(self):
        """3 个 deferred_items 生成 3 个 decision 类型节点。"""
        translator = ContractionTranslator()
        deferred = ["团队协作", "日历集成", "数据导出"]
        draft = _make_scope_draft(num_scopes=2, deferred_items=deferred)
        result = translator.translate(draft)

        decision_ops = [
            op for op in result.operations
            if (
                op["operation_type"] == OperationType.CREATE_NODE
                and op["node_type"] == NodeType.DECISION
            )
        ]
        assert len(decision_ops) == 3

        # 验证 label 与输入对应
        labels = [op["label"] for op in decision_ops]
        assert "团队协作" in labels
        assert "日历集成" in labels
        assert "数据导出" in labels

        # 验证 props 结构
        for op in decision_ops:
            assert "title" in op["props"]
            assert "description" in op["props"]
            assert op["props"]["status"] == "pending"

    def test_translate_creates_risk_nodes(self):
        """2 个 risks 生成 2 个 risk 类型节点，含正确的 severity 和 status。"""
        translator = ContractionTranslator()
        risks = ["技术栈不熟悉", "需求不明确"]
        draft = _make_scope_draft(num_scopes=2, risks=risks)
        result = translator.translate(draft)

        risk_ops = [
            op for op in result.operations
            if (
                op["operation_type"] == OperationType.CREATE_NODE
                and op["node_type"] == NodeType.RISK
            )
        ]
        assert len(risk_ops) == 2

        for op in risk_ops:
            assert "title" in op["props"]
            assert "description" in op["props"]
            assert op["props"]["severity"] == "medium"
            assert op["props"]["status"] == "open"

    def test_translate_edges(self):
        """有 scope + deferred → 建立 references 边。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(
            num_scopes=2,
            deferred_items=["延后功能A"],
            risks=["风险1"],
        )
        result = translator.translate(draft)

        # 找出所有 create_edge 操作
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]

        # 应有 2 条边：
        # 1. scope[0] → decision[0]（scope 引用 deferred）
        # 2. risk[0] → scope[0]（risk 引用 scope）
        assert len(edge_ops) == 2

        # 验证边类型
        for edge in edge_ops:
            assert edge["edge_type"] == EdgeType.REFERENCES

        # 验证 source/target 使用 _ref 格式
        for edge in edge_ops:
            assert edge["source_node_id"].startswith("_ref:")
            assert edge["target_node_id"].startswith("_ref:")

    def test_translate_creates_edges(self):
        """2 个 deferred + 1 个 risk → scope 和 decision 之间有 2 条边，risk 和 scope 之间有 1 条边。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(
            num_scopes=2,
            deferred_items=["延后功能A", "延后功能B"],
            risks=["风险1"],
        )
        result = translator.translate(draft)

        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]

        # 2 个 deferred → 2 条 scope→decision 边 + 1 条 risk→scope 边 = 3 条
        assert len(edge_ops) == 3

        # 所有边类型都是 references
        for op in edge_ops:
            assert op["edge_type"] == EdgeType.REFERENCES

        # 验证边引用格式正确
        for op in edge_ops:
            assert op["source_node_id"].startswith("_ref:")
            assert op["target_node_id"].startswith("_ref:")

    def test_translate_empty(self):
        """空 scopes → 无操作。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=0)
        result = translator.translate(draft)

        # 空 scopes 没有 scope 节点，也不会有边
        scope_ops = [
            op for op in result.operations
            if op.get("operation_type") == OperationType.CREATE_NODE
            and op.get("node_type") == NodeType.SCOPE
        ]
        assert len(scope_ops) == 0

    def test_translate_wrong_type(self):
        """传入非 ScopeDraft → 返回空操作 + 警告。"""
        from agents.schemas.high_level import SchemaPlan

        translator = ContractionTranslator()
        # 传入 SchemaPlan 而不是 ScopeDraft
        wrong_input = SchemaPlan(entities=[], endpoints=[])
        result = translator.translate(wrong_input)

        assert len(result.operations) == 0
        assert len(result.warnings) > 0
        assert "ScopeDraft" in result.warnings[0]

    def test_no_edges_without_deferred(self):
        """没有 deferred_items 时，不创建 scope→decision 边。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=2)
        result = translator.translate(draft)

        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]
        # 没有 deferred 和 risk，不应有边
        assert len(edge_ops) == 0

    def test_no_warnings_without_deferred(self):
        """没有 deferred_items 时，不应产生延后相关警告。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=2)
        result = translator.translate(draft)

        deferred_warnings = [w for w in result.warnings if "延后" in w]
        assert len(deferred_warnings) == 0

    def test_operation_counts(self):
        """综合验证操作数量：2 scope + 1 deferred + 1 risk + 2 edges。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(
            num_scopes=2,
            deferred_items=["延后功能A"],
            risks=["风险1"],
        )
        result = translator.translate(draft)

        # 2 scope + 1 decision + 1 risk + 2 edges = 6 操作
        assert len(result.operations) == 6

    def test_translate_empty_scope(self):
        """空 scope 不报错，返回空操作列表。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=0)
        result = translator.translate(draft)

        assert len(result.operations) == 0
        assert isinstance(result.warnings, list)

    def test_only_deferred_no_scope_generates_decisions_but_no_edges(self):
        """只有 deferred 没有 scope，生成 decision 节点但不生成边。"""
        translator = ContractionTranslator()
        draft = _make_scope_draft(num_scopes=0, deferred_items=["延后功能"])
        result = translator.translate(draft)

        # 1 个 decision 节点
        decision_ops = [
            op for op in result.operations
            if (
                op["operation_type"] == OperationType.CREATE_NODE
                and op["node_type"] == NodeType.DECISION
            )
        ]
        assert len(decision_ops) == 1

        # 没有 scope，不应该有边
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]
        assert len(edge_ops) == 0
