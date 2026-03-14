"""
PlannerTranslator 测试模块。

测试 PlannerTranslator 将 TaskPlan 翻译为 IROperation 列表的逻辑，
包括基础翻译、依赖边创建、非法 agent_id 和循环依赖检测。
"""

import pytest
from agents.schemas.high_level import TaskPlan, TaskStep
from agents.translators.planner_translator import PlannerTranslator
from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType


# ============================================================
# 辅助函数
# ============================================================

def _make_standard_task_plan() -> TaskPlan:
    """
    构造标准的 7 步任务计划。

    对应 DAG：schema → backend/frontend/doc/diagram → qa → export
    """
    return TaskPlan(
        steps=[
            TaskStep(
                step_id="step_1",
                agent_id="schema",
                description="设计数据模型与 API 契约",
                depends_on=[],
            ),
            TaskStep(
                step_id="step_2",
                agent_id="backend",
                description="生成后端代码",
                depends_on=["step_1"],
            ),
            TaskStep(
                step_id="step_3",
                agent_id="frontend",
                description="生成前端代码",
                depends_on=["step_1"],
            ),
            TaskStep(
                step_id="step_4",
                agent_id="doc",
                description="生成项目文档",
                depends_on=["step_1"],
            ),
            TaskStep(
                step_id="step_5",
                agent_id="diagram",
                description="生成 Mermaid 图表",
                depends_on=["step_1"],
            ),
            TaskStep(
                step_id="step_6",
                agent_id="qa",
                description="质量检查",
                depends_on=["step_2", "step_3", "step_4", "step_5"],
            ),
            TaskStep(
                step_id="step_7",
                agent_id="export",
                description="打包导出",
                depends_on=["step_6"],
            ),
        ],
        estimated_complexity="medium",
    )


# ============================================================
# PlannerTranslator 测试
# ============================================================

class TestPlannerTranslator:
    """PlannerTranslator 翻译逻辑测试。"""

    def test_basic_translation(self):
        """标准 TaskPlan → IROperation[]：节点数和边数正确。"""
        translator = PlannerTranslator()
        plan = _make_standard_task_plan()
        result = translator.translate(plan)

        # 统计 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        # 7 个 TaskStep → 7 个 task 节点
        assert len(node_ops) == 7

        # 验证节点类型都是 task
        for op in node_ops:
            assert op["node_type"] == NodeType.TASK

        # 验证节点 props 包含必要字段
        for op in node_ops:
            assert "step_id" in op["props"]
            assert "agent_id" in op["props"]
            assert "description" in op["props"]

    def test_dependency_edges(self):
        """依赖边正确创建：每个 depends_on 对应一条 create_edge。"""
        translator = PlannerTranslator()
        plan = _make_standard_task_plan()
        result = translator.translate(plan)

        # 统计 create_edge 操作
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]

        # 计算总依赖数：
        # step_1: 0, step_2→step_1: 1, step_3→step_1: 1, step_4→step_1: 1, step_5→step_1: 1
        # step_6→step_2: 1, step_6→step_3: 1, step_6→step_4: 1, step_6→step_5: 1
        # step_7→step_6: 1 → 总计 9 条 depends_on 边
        assert len(edge_ops) == 9

        # 验证边类型都是 depends_on
        for op in edge_ops:
            assert op["edge_type"] == EdgeType.DEPENDS_ON

        # 验证边使用 _ref 格式引用
        for op in edge_ops:
            assert op["source_node_id"].startswith("_ref:")
            assert op["target_node_id"].startswith("_ref:")

    def test_invalid_agent_id(self):
        """非法 agent_id 产生警告，但仍能翻译。"""
        translator = PlannerTranslator()
        plan = TaskPlan(
            steps=[
                TaskStep(
                    step_id="step_1",
                    agent_id="invalid_agent",
                    description="测试非法 agent_id",
                    depends_on=[],
                ),
            ],
            estimated_complexity="small",
        )
        result = translator.translate(plan)

        # 应该仍然创建节点
        assert len(result.operations) >= 1

        # 应该产生 agent_id 不合法的警告
        agent_warnings = [
            w for w in result.warnings
            if "invalid_agent" in w and "合法值" in w
        ]
        assert len(agent_warnings) >= 1

    def test_cycle_detection(self):
        """循环依赖检测：A → B → A 应产生警告。"""
        translator = PlannerTranslator()
        plan = TaskPlan(
            steps=[
                TaskStep(
                    step_id="step_a",
                    agent_id="schema",
                    description="步骤 A",
                    depends_on=["step_b"],
                ),
                TaskStep(
                    step_id="step_b",
                    agent_id="backend",
                    description="步骤 B",
                    depends_on=["step_a"],
                ),
            ],
            estimated_complexity="small",
        )
        result = translator.translate(plan)

        # 应该检测到循环依赖
        cycle_warnings = [
            w for w in result.warnings if "循环依赖" in w
        ]
        assert len(cycle_warnings) >= 1

    def test_empty_steps(self):
        """空 steps 列表返回空操作 + 警告。"""
        translator = PlannerTranslator()
        plan = TaskPlan(
            steps=[],
            estimated_complexity="small",
        )
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert len(result.warnings) >= 1
        assert "steps 列表为空" in result.warnings[0]

    def test_wrong_type(self):
        """传入非 TaskPlan 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import ScopeDraft, ScopeItem
        from ir_core.schema.node_types import Priority

        translator = PlannerTranslator()
        wrong_input = ScopeDraft(
            product_name="Test",
            product_description="test",
            scopes=[
                ScopeItem(
                    name="功能",
                    description="描述",
                    priority=Priority.HIGH,
                    tags=[],
                ),
            ],
        )
        result = translator.translate(wrong_input)

        assert len(result.operations) == 0
        assert "TaskPlan" in result.warnings[0]

    def test_missing_dependency_reference(self):
        """depends_on 引用的 step_id 不存在时产生警告。"""
        translator = PlannerTranslator()
        plan = TaskPlan(
            steps=[
                TaskStep(
                    step_id="step_1",
                    agent_id="schema",
                    description="步骤 1",
                    depends_on=["step_nonexistent"],
                ),
            ],
            estimated_complexity="small",
        )
        result = translator.translate(plan)

        # 应该产生引用不存在的警告
        ref_warnings = [
            w for w in result.warnings if "step_nonexistent" in w
        ]
        assert len(ref_warnings) >= 1

    def test_step_id_format_warning(self):
        """step_id 不以 step_ 开头时产生格式警告。"""
        translator = PlannerTranslator()
        plan = TaskPlan(
            steps=[
                TaskStep(
                    step_id="bad_format",
                    agent_id="schema",
                    description="格式不规范的 step_id",
                    depends_on=[],
                ),
            ],
            estimated_complexity="small",
        )
        result = translator.translate(plan)

        format_warnings = [
            w for w in result.warnings if "格式不规范" in w
        ]
        assert len(format_warnings) >= 1
