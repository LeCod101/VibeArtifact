"""
AgentSelector 单元测试。

覆盖：
- 冷启动返回完整初始化链
- 单个 Agent 的执行计划
- 同层 Agent 并行分组
- 多层 Agent 按 DAG 排列
- 重复 Agent 去重
- 空 agents 列表返回空计划

质量把关已由配对 reviewer 在执行步内完成（conversation_graph），
不再有独立 QA 层的追加逻辑。
"""


from agents.analysis.agent_selector import AgentSelector
from agents.analysis.models import ChangeScope, ImpactReport

# ============================================================
# 测试辅助函数
# ============================================================


def make_report(
    agents: list[str],
    cold_start: bool = False,
    scope: ChangeScope = ChangeScope.PARTIAL,
) -> ImpactReport:
    """
    构造测试用 ImpactReport。

    参数：
        agents: affected_agents 列表
        cold_start: 是否需要冷启动
        scope: 变更范围

    返回：
        ImpactReport 实例
    """
    return ImpactReport(
        change_scope=scope,
        requires_cold_start=cold_start,
        affected_areas=[],
        affected_agents=agents,
        reasoning="test",
        user_intent_summary="test",
    )


# ============================================================
# AgentSelector 测试
# ============================================================


class TestAgentSelector:
    """AgentSelector Agent 选择器测试。"""

    def setup_method(self):
        """每个测试方法执行前创建 AgentSelector 实例。"""
        self.selector = AgentSelector()

    def test_cold_start_returns_full_chain(self):
        """requires_cold_start=True 时返回完整初始化链。"""
        report = make_report(
            agents=["intent", "contraction", "planner", "schema"],
            cold_start=True,
        )
        plan = self.selector.select(report)
        assert plan == [["intent"], ["contraction"], ["planner"], ["schema"]]

    def test_single_frontend_agent(self):
        """affected_agents 仅含 frontend 时，计划只含 frontend。"""
        report = make_report(agents=["frontend"])
        plan = self.selector.select(report)
        assert plan == [["frontend"]]

    def test_single_backend_agent(self):
        """affected_agents 仅含 backend 时，计划只含 backend。"""
        report = make_report(agents=["backend"])
        plan = self.selector.select(report)
        assert plan == [["backend"]]

    def test_parallel_agents_same_layer(self):
        """backend 和 frontend 在同一层级，应并行排列。"""
        report = make_report(agents=["backend", "frontend"])
        plan = self.selector.select(report)
        assert plan == [["backend", "frontend"]]

    def test_multi_layer_agents(self):
        """schema 和 backend 跨层，按 DAG 顺序排列。"""
        report = make_report(agents=["schema", "backend"])
        plan = self.selector.select(report)
        # schema 在 layer 3, backend 在 layer 4
        assert plan == [["schema"], ["backend"]]

    def test_doc_only(self):
        """affected_agents 仅含 doc 时计划只含 doc。"""
        report = make_report(agents=["doc"])
        plan = self.selector.select(report)
        assert plan == [["doc"]]

    def test_deduplication(self):
        """重复 Agent 在执行计划中去重。"""
        report = make_report(agents=["backend", "backend", "frontend"])
        plan = self.selector.select(report)
        # 去重后 backend 和 frontend 在同层
        flat_agents = [a for layer in plan for a in layer]
        assert flat_agents.count("backend") == 1
        assert flat_agents.count("frontend") == 1

    def test_unknown_agent_skipped(self):
        """未知 Agent（如已撤销的 qa）被防御性跳过。"""
        report = make_report(agents=["backend", "qa"])
        plan = self.selector.select(report)
        flat_agents = [a for layer in plan for a in layer]
        assert "qa" not in flat_agents
        assert "backend" in flat_agents

    def test_empty_agents_returns_empty(self):
        """affected_agents 为空时返回空执行计划。"""
        report = make_report(agents=[])
        plan = self.selector.select(report)
        assert plan == []
