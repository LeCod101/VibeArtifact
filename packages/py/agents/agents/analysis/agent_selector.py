"""
Agent 选择器模块。

AgentSelector 根据 ImpactReport 决定需要执行哪些 Agent，
并按 DAG 依赖关系排列为分层执行计划（同层可并行）。

依赖关系 DAG（reviewer 不在此列，由 conversation_graph 在
配对 author 执行步内多轮调用）：
    intent → contraction → planner → schema
        → backend / frontend / doc / diagram (同层并行)
            → export
"""

from agents.analysis.models import ImpactReport

# ────────────────────────────────────────────
# Agent 依赖图（DAG）
# ────────────────────────────────────────────

# 每个 Agent 的前置依赖列表
DEPENDENCY_MAP: dict[str, list[str]] = {
    "intent": [],
    "contraction": ["intent"],
    "planner": ["contraction"],
    "schema": ["planner"],
    "backend": ["schema"],
    "frontend": ["schema"],
    "doc": ["schema"],
    "diagram": ["schema"],
    "export": ["backend", "frontend", "doc", "diagram"],
}

# Agent → 执行层级（数字越小越先执行，同层级可并行）
LAYER_ORDER: dict[str, int] = {
    "intent": 0,
    "contraction": 1,
    "planner": 2,
    "schema": 3,
    "backend": 4,
    "frontend": 4,
    "doc": 4,
    "diagram": 4,
    "export": 5,
}


class AgentSelector:
    """
    Agent 选择器。

    根据 ImpactReport 生成分层执行计划：
    - 冷启动时返回完整初始化链
    - 增量修改时按 DAG 层级排序，同层可并行

    代码类 Agent 的质量把关由其配对 reviewer 在执行步内完成
    （conversation_graph 多轮循环），不再追加独立 QA 层。
    """

    def select(self, report: ImpactReport) -> list[list[str]]:
        """
        根据影响报告生成分层执行计划。

        参数：
        - report: ImpactAnalyzer 产出的影响分析报告

        返回：
        - 分层执行计划，每层是一个 Agent 列表，同层内可并行执行
          示例：[["intent"], ["contraction"], ["planner"], ["schema"]]
        """
        # ── 冷启动：返回完整初始化链 ──
        if report.requires_cold_start:
            return [["intent"], ["contraction"], ["planner"], ["schema"]]

        # ── 增量修改：收集需要执行的 Agent ──
        agents_to_run: set[str] = set(report.affected_agents)

        # ── 按层级分组 ──
        return self._group_by_layer(agents_to_run)

    def _group_by_layer(self, agents: set[str]) -> list[list[str]]:
        """
        将 Agent 集合按 DAG 层级分组排序。

        同一层级的 Agent 放在同一个列表中（可并行执行），
        不同层级按从小到大排列。

        参数：
        - agents: 需要执行的 Agent 集合

        返回：
        - 分层执行计划（外层列表按层级排序，内层列表为同层 Agent）
        """
        # 按层级号分组
        layer_groups: dict[int, list[str]] = {}
        for agent in agents:
            layer = LAYER_ORDER.get(agent)
            # 跳过未知 Agent（防御性编程）
            if layer is None:
                continue
            layer_groups.setdefault(layer, [])
            layer_groups[layer].append(agent)

        # 按层级号排序，每层内按字母排序（确保确定性输出）
        result: list[list[str]] = []
        for layer_num in sorted(layer_groups.keys()):
            result.append(sorted(layer_groups[layer_num]))
        return result
