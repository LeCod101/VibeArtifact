"""
影响分析器模块。

ImpactAnalyzer 是纯规则匹配引擎（不调用 LLM），负责：
1. 检测冷启动（IR 图为空 → 全量重建）
2. 通过关键词正则匹配用户消息，确定需要执行的 Agent
3. 根据 Agent 反推受影响的节点类型
4. 遍历 IR 图，沿 edges 扩展 1 跳邻居，收集受影响节点 ID
5. 根据受影响 Agent 数量判定变更范围（FULL/PARTIAL/COSMETIC）
"""

import re
from uuid import UUID

from ir_core.schema.data import IREdgeData, IRNodeData

from agents.analysis.models import ChangeScope, ImpactReport

# ────────────────────────────────────────────
# 关键词 → Agent 映射规则
# ────────────────────────────────────────────

# 每条规则：(编译后的正则, 匹配时应派遣的 Agent 列表)
_KEYWORD_RULES: list[tuple[re.Pattern[str], list[str]]] = [
    # 全量重建关键词（优先级最高，命中即返回全部 Agent）
    (
        re.compile(r"重做|重新生成|全部重来|从头开始|推翻重来"),
        ["planner", "schema", "backend", "frontend", "doc", "diagram"],
    ),
    # 全局变更（跨多个 Agent 的联动修改）
    (
        re.compile(r"登录|注册|认证|手机号|邮箱|OAuth|SSO"),
        ["schema", "backend", "frontend"],
    ),
    # 数据模型关键词
    (
        re.compile(r"数据库|表|字段|模型|实体|关系|schema|外键|索引|迁移"),
        ["schema", "backend"],
    ),
    # 后端关键词
    (
        re.compile(r"接口|API|端点|路由|中间件|认证|权限|后端|服务"),
        ["backend"],
    ),
    # 前端关键词
    (
        re.compile(
            r"页面|组件|按钮|表单|样式|CSS|界面|UI|布局|导航|侧边栏|弹窗|对话框"
        ),
        ["frontend"],
    ),
    # 文档关键词
    (
        re.compile(r"文档|README|说明|API文档"),
        ["doc"],
    ),
    # 图表关键词
    (
        re.compile(r"图表|流程图|架构图|Mermaid|ER图|时序图"),
        ["diagram"],
    ),
]

# ────────────────────────────────────────────
# 节点类型 → Agent 映射（正向）
# ────────────────────────────────────────────

# IR 节点类型到与之相关的 Agent 列表
NODE_TYPE_AGENT_MAP: dict[str, list[str]] = {
    "scope": ["intent", "contraction"],
    "task": ["planner"],
    "entity": ["schema"],
    "endpoint": ["schema", "backend"],
    "ui_page": ["frontend"],
    "ui_component": ["frontend"],
    "artifact": ["doc", "diagram", "backend", "frontend"],
    "risk": ["intent"],
    "decision": ["planner"],
}


def _build_agent_to_node_types() -> dict[str, list[str]]:
    """
    反转 NODE_TYPE_AGENT_MAP，构建 Agent → 节点类型列表的映射。

    返回值示例：{"frontend": ["ui_page", "ui_component", "artifact"], ...}
    """
    result: dict[str, list[str]] = {}
    for node_type, agents in NODE_TYPE_AGENT_MAP.items():
        for agent in agents:
            result.setdefault(agent, [])
            if node_type not in result[agent]:
                result[agent].append(node_type)
    return result


# Agent → 关联节点类型列表（模块级计算，避免重复构建）
_AGENT_NODE_TYPES: dict[str, list[str]] = _build_agent_to_node_types()


class ImpactAnalyzer:
    """
    影响分析器（纯规则匹配，不调用 LLM）。

    根据用户消息和当前 IR 图状态，判定：
    - 变更范围（FULL / PARTIAL / COSMETIC）
    - 需要执行哪些 Agent
    - 哪些 IR 节点受到影响
    """

    def analyze(
        self,
        user_message: str,
        ir_nodes: list[IRNodeData],
        ir_edges: list[IREdgeData],
    ) -> ImpactReport:
        """
        分析用户消息对 IR 图的影响。

        参数：
        - user_message: 用户输入的消息文本
        - ir_nodes: 当前 IR 图中的所有节点
        - ir_edges: 当前 IR 图中的所有边

        返回：
        - ImpactReport: 影响分析报告
        """
        # 截取用户意图摘要（前 100 字符）
        user_intent_summary = user_message[:100]

        # ── 步骤 1：冷启动检测 ──
        if not ir_nodes:
            return ImpactReport(
                change_scope=ChangeScope.FULL,
                requires_cold_start=True,
                affected_node_types=[],
                affected_node_ids=[],
                affected_agents=["intent", "contraction", "planner", "schema"],
                reasoning="IR 图为空，需要冷启动全量生成",
                user_intent_summary=user_intent_summary,
            )

        # ── 步骤 2：关键词匹配，收集 affected_agents ──
        affected_agents = self._match_keywords(user_message)

        # 无匹配时兜底回退到 planner
        if not affected_agents:
            affected_agents = ["planner"]

        # ── 步骤 3：根据 Agent 反推受影响的节点类型 ──
        affected_node_types = self._resolve_node_types(affected_agents)

        # ── 步骤 4：IR 图遍历，收集受影响节点 ID（含 1 跳邻居） ──
        affected_node_ids = self._collect_affected_ids(
            affected_node_types, ir_nodes, ir_edges
        )

        # ── 步骤 5：范围判定 ──
        change_scope = self._determine_scope(affected_agents)

        # 构建推理说明
        reasoning = (
            f"关键词匹配命中 Agent: {affected_agents}，"
            f"关联节点类型: {affected_node_types}，"
            f"受影响节点数: {len(affected_node_ids)}，"
            f"判定范围: {change_scope.value}"
        )

        return ImpactReport(
            change_scope=change_scope,
            requires_cold_start=False,
            affected_node_types=affected_node_types,
            affected_node_ids=affected_node_ids,
            affected_agents=affected_agents,
            reasoning=reasoning,
            user_intent_summary=user_intent_summary,
        )

    def _match_keywords(self, user_message: str) -> list[str]:
        """
        通过正则匹配用户消息中的关键词，收集需要派遣的 Agent。

        遍历所有关键词规则，将匹配到的 Agent 去重合并后返回。

        参数：
        - user_message: 用户输入的消息文本

        返回：
        - 去重后的 Agent 标识符列表
        """
        agents_set: set[str] = set()
        for pattern, agents in _KEYWORD_RULES:
            if pattern.search(user_message):
                agents_set.update(agents)
        return sorted(agents_set)

    def _resolve_node_types(self, affected_agents: list[str]) -> list[str]:
        """
        根据受影响的 Agent 列表，反推关联的 IR 节点类型。

        参数：
        - affected_agents: 受影响的 Agent 标识符列表

        返回：
        - 去重后的节点类型列表
        """
        node_types_set: set[str] = set()
        for agent in affected_agents:
            if agent in _AGENT_NODE_TYPES:
                node_types_set.update(_AGENT_NODE_TYPES[agent])
        return sorted(node_types_set)

    def _collect_affected_ids(
        self,
        affected_node_types: list[str],
        ir_nodes: list[IRNodeData],
        ir_edges: list[IREdgeData],
    ) -> list[UUID]:
        """
        从 IR 图中收集受影响的节点 ID。

        先找出节点类型匹配的直接命中节点，
        再沿 edges 扩展 1 跳邻居，合并去重。

        参数：
        - affected_node_types: 受影响的节点类型列表
        - ir_nodes: IR 图中的所有节点
        - ir_edges: IR 图中的所有边

        返回：
        - 受影响的节点 ID 列表（含邻居，已去重）
        """
        # 直接命中的节点 ID
        direct_ids: set[UUID] = set()
        for node in ir_nodes:
            if node.node_type in affected_node_types:
                direct_ids.add(node.id)

        # 扩展 1 跳邻居
        neighbor_ids: set[UUID] = set()
        for edge in ir_edges:
            if edge.source_node_id in direct_ids:
                neighbor_ids.add(edge.target_node_id)
            if edge.target_node_id in direct_ids:
                neighbor_ids.add(edge.source_node_id)

        # 合并直接命中和邻居
        all_ids = direct_ids | neighbor_ids
        return sorted(all_ids)

    def _determine_scope(self, affected_agents: list[str]) -> ChangeScope:
        """
        根据受影响 Agent 的数量判定变更范围。

        规则：
        - 3 种及以上 Agent → FULL（全量重建）
        - 1-2 种 Agent → PARTIAL（局部修改）
        - 0 种（理论上不会到这里）→ COSMETIC

        参数：
        - affected_agents: 受影响的 Agent 标识符列表

        返回：
        - ChangeScope 枚举值
        """
        count = len(affected_agents)
        if count >= 3:
            return ChangeScope.FULL
        if count >= 1:
            return ChangeScope.PARTIAL
        return ChangeScope.COSMETIC
