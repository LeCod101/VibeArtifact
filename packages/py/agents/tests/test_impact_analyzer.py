"""
M7 ImpactAnalyzer 单元测试。

覆盖：
- 冷启动检测（空 IR 触发）
- 关键词匹配各类 Agent（frontend/backend/schema/doc/diagram）
- 全局变更和全量重建关键词
- 变更范围判定（FULL/PARTIAL）
- 无匹配时回退到 planner
- affected_node_types 从 agents 的正确映射
- 1 跳邻居扩展
- user_intent_summary 截断
- 多关键词匹配去重
- COSMETIC scope 边界条件
"""

import pytest
from uuid import uuid4

from agents.analysis.models import ChangeScope, ImpactReport
from agents.analysis.impact_analyzer import ImpactAnalyzer, _AGENT_NODE_TYPES
from ir_core.schema.data import IRNodeData, IREdgeData


# ============================================================
# 测试辅助函数
# ============================================================


def make_test_node(node_type: str, label: str = "test") -> IRNodeData:
    """
    构造测试用 IR 节点。

    参数：
        node_type: 节点类型
        label: 节点显示标签

    返回：
        IRNodeData 实例
    """
    return IRNodeData(
        id=uuid4(),
        node_type=node_type,
        label=label,
        props={},
    )


def make_test_edge(
    source_id, target_id, edge_type: str = "references"
) -> IREdgeData:
    """
    构造测试用 IR 边。

    参数：
        source_id: 源节点 ID
        target_id: 目标节点 ID
        edge_type: 边类型

    返回：
        IREdgeData 实例
    """
    return IREdgeData(
        id=uuid4(),
        source_node_id=source_id,
        target_node_id=target_id,
        edge_type=edge_type,
    )


# ============================================================
# ImpactAnalyzer 测试
# ============================================================


class TestImpactAnalyzer:
    """ImpactAnalyzer 影响分析器测试。"""

    def setup_method(self):
        """每个测试方法执行前创建 ImpactAnalyzer 实例。"""
        self.analyzer = ImpactAnalyzer()

    # ── 冷启动检测 ──

    def test_empty_ir_triggers_cold_start(self):
        """ir_nodes 为空列表时触发冷启动，change_scope 为 FULL。"""
        report = self.analyzer.analyze(
            user_message="创建一个 Todo 应用",
            ir_nodes=[],
            ir_edges=[],
        )
        assert report.requires_cold_start is True
        assert report.change_scope == ChangeScope.FULL
        assert "intent" in report.affected_agents
        assert "contraction" in report.affected_agents
        assert "planner" in report.affected_agents
        assert "schema" in report.affected_agents

    # ── 关键词匹配测试 ──

    def test_frontend_keywords(self):
        """包含前端关键词"修改页面布局"时，affected_agents 包含 frontend。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="修改页面布局",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "frontend" in report.affected_agents
        assert report.requires_cold_start is False

    def test_backend_keywords(self):
        """包含后端关键词"添加新的API接口"时，affected_agents 包含 backend。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="添加新的API接口",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "backend" in report.affected_agents

    def test_schema_keywords(self):
        """包含数据模型关键词"新增一个数据库表"时，affected_agents 包含 schema 和 backend。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="新增一个数据库表",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "schema" in report.affected_agents
        assert "backend" in report.affected_agents

    def test_doc_keywords(self):
        """包含文档关键词"更新README文档"时，affected_agents 包含 doc。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="更新README文档",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "doc" in report.affected_agents

    def test_diagram_keywords(self):
        """包含图表关键词"重画架构图"时，affected_agents 包含 diagram。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="重画架构图",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "diagram" in report.affected_agents

    # ── 全局变更和全量重建 ──

    def test_global_change_keywords(self):
        """包含全局变更关键词"把登录改成手机号"时，涉及 schema/backend/frontend。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="把登录改成手机号",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert "schema" in report.affected_agents
        assert "backend" in report.affected_agents
        assert "frontend" in report.affected_agents

    def test_full_rebuild_keywords(self):
        """包含全量重建关键词"全部重来"时，change_scope 为 FULL。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="全部重来",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert report.change_scope == ChangeScope.FULL
        # 全量重建时包含所有主要 Agent
        assert "planner" in report.affected_agents
        assert "schema" in report.affected_agents
        assert "backend" in report.affected_agents
        assert "frontend" in report.affected_agents

    # ── 变更范围判定 ──

    def test_partial_scope(self):
        """单个关键词匹配时，change_scope 为 PARTIAL（1-2 种 Agent）。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="修改页面上的按钮",
            ir_nodes=nodes,
            ir_edges=[],
        )
        # 只匹配 frontend，1 个 Agent → PARTIAL
        assert report.change_scope == ChangeScope.PARTIAL

    # ── 无匹配回退 ──

    def test_no_match_fallback(self):
        """无任何关键词匹配时，回退到 planner，change_scope 为 PARTIAL。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="做点什么",
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert report.affected_agents == ["planner"]
        assert report.change_scope == ChangeScope.PARTIAL

    # ── 节点类型映射 ──

    def test_affected_node_types_from_agents(self):
        """affected_agents 正确映射到 affected_node_types。"""
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message="修改页面布局",
            ir_nodes=nodes,
            ir_edges=[],
        )
        # frontend Agent 对应的节点类型
        expected_types = _AGENT_NODE_TYPES.get("frontend", [])
        for nt in expected_types:
            assert nt in report.affected_node_types

    # ── 图遍历扩展邻居 ──

    def test_graph_traversal_expands_neighbors(self):
        """有 edges 时，1 跳邻居被加入 affected_node_ids。"""
        # 创建一个 ui_page 节点和一个 entity 节点，通过边连接
        ui_node = make_test_node("ui_page", "首页")
        entity_node = make_test_node("entity", "用户表")
        edge = make_test_edge(ui_node.id, entity_node.id)

        report = self.analyzer.analyze(
            user_message="修改页面布局",
            ir_nodes=[ui_node, entity_node],
            ir_edges=[edge],
        )

        # ui_page 节点被 frontend Agent 直接命中
        assert ui_node.id in report.affected_node_ids
        # entity 节点通过 1 跳邻居扩展被包含
        assert entity_node.id in report.affected_node_ids

    # ── 用户意图摘要截断 ──

    def test_user_intent_summary(self):
        """长消息被截断到 100 字符。"""
        long_message = "这是一段很长的需求描述" * 20
        nodes = [make_test_node("scope", "功能模块")]
        report = self.analyzer.analyze(
            user_message=long_message,
            ir_nodes=nodes,
            ir_edges=[],
        )
        assert len(report.user_intent_summary) <= 100

    # ── 多关键词匹配去重 ──

    def test_multiple_keyword_matches(self):
        """同时匹配多个关键词时，agents 列表去重。"""
        nodes = [make_test_node("scope", "功能模块")]
        # "添加API接口的页面布局" 同时匹配 backend 和 frontend
        report = self.analyzer.analyze(
            user_message="添加API接口的页面布局",
            ir_nodes=nodes,
            ir_edges=[],
        )
        # 确认 agents 列表中无重复
        assert len(report.affected_agents) == len(set(report.affected_agents))
        assert "backend" in report.affected_agents
        assert "frontend" in report.affected_agents

    # ── COSMETIC scope 边界 ──

    def test_cosmetic_scope(self):
        """
        _determine_scope 当 affected_agents 为空时返回 COSMETIC。

        由于 analyze() 内部会兜底到 planner（不会出现空 agents），
        此测试直接调用 _determine_scope 验证边界逻辑。
        """
        scope = self.analyzer._determine_scope([])
        assert scope == ChangeScope.COSMETIC
