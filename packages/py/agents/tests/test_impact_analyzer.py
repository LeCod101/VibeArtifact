"""
ImpactAnalyzer 单元测试。

覆盖：
- 冷启动检测（空工作区触发）
- 关键词匹配各类 Agent（frontend/backend/schema/doc/diagram）
- 全局变更和全量重建关键词
- 变更范围判定（FULL/PARTIAL）
- 无匹配时回退到 planner
- affected_agents 到 affected_areas 的正确映射
- user_intent_summary 截断
- 多关键词匹配去重
- COSMETIC scope 边界条件
"""

from agents.analysis.impact_analyzer import AGENT_AREA_MAP, ImpactAnalyzer
from agents.analysis.models import ChangeScope
from agents.schemas.workspace import WorkspaceFileData

# ============================================================
# 测试辅助函数
# ============================================================


def make_test_file(path: str = "backend/main.py") -> WorkspaceFileData:
    """
    构造测试用工作区文件。

    参数：
        path: 文件路径

    返回：
        WorkspaceFileData 实例
    """
    return WorkspaceFileData(path=path, content="x", kind="code")


# ============================================================
# ImpactAnalyzer 测试
# ============================================================


class TestImpactAnalyzer:
    """ImpactAnalyzer 影响分析器测试。"""

    def setup_method(self):
        """每个测试方法执行前创建 ImpactAnalyzer 实例。"""
        self.analyzer = ImpactAnalyzer()

    # ── 冷启动检测 ──

    def test_empty_workspace_triggers_cold_start(self):
        """workspace_files 为空列表时触发冷启动，change_scope 为 FULL。"""
        report = self.analyzer.analyze(
            user_message="创建一个 Todo 应用",
            workspace_files=[],
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
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="修改页面布局",
            workspace_files=files,
        )
        assert "frontend" in report.affected_agents
        assert report.requires_cold_start is False

    def test_backend_keywords(self):
        """包含后端关键词"添加新的API接口"时，affected_agents 包含 backend。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="添加新的API接口",
            workspace_files=files,
        )
        assert "backend" in report.affected_agents

    def test_schema_keywords(self):
        """包含数据模型关键词"新增一个数据库表"时，affected_agents 包含 schema 和 backend。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="新增一个数据库表",
            workspace_files=files,
        )
        assert "schema" in report.affected_agents
        assert "backend" in report.affected_agents

    def test_doc_keywords(self):
        """包含文档关键词"更新README文档"时，affected_agents 包含 doc。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="更新README文档",
            workspace_files=files,
        )
        assert "doc" in report.affected_agents

    def test_diagram_keywords(self):
        """包含图表关键词"重画架构图"时，affected_agents 包含 diagram。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="重画架构图",
            workspace_files=files,
        )
        assert "diagram" in report.affected_agents

    # ── 全局变更和全量重建 ──

    def test_global_change_keywords(self):
        """包含全局变更关键词"把登录改成手机号"时，涉及 schema/backend/frontend。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="把登录改成手机号",
            workspace_files=files,
        )
        assert "schema" in report.affected_agents
        assert "backend" in report.affected_agents
        assert "frontend" in report.affected_agents

    def test_full_rebuild_keywords(self):
        """包含全量重建关键词"全部重来"时，change_scope 为 FULL。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="全部重来",
            workspace_files=files,
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
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="修改页面上的按钮",
            workspace_files=files,
        )
        # 只匹配 frontend，1 个 Agent → PARTIAL
        assert report.change_scope == ChangeScope.PARTIAL

    # ── 无匹配回退 ──

    def test_no_match_fallback(self):
        """无任何关键词匹配时，回退到 planner，change_scope 为 PARTIAL。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="做点什么",
            workspace_files=files,
        )
        assert report.affected_agents == ["planner"]
        assert report.change_scope == ChangeScope.PARTIAL

    # ── 产物领域映射 ──

    def test_affected_areas_from_agents(self):
        """affected_agents 正确映射到 affected_areas。"""
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message="修改页面布局",
            workspace_files=files,
        )
        # frontend Agent 对应的产物领域
        expected_areas = AGENT_AREA_MAP.get("frontend", [])
        for area in expected_areas:
            assert area in report.affected_areas

    # ── 用户意图摘要截断 ──

    def test_user_intent_summary(self):
        """长消息被截断到 100 字符。"""
        long_message = "这是一段很长的需求描述" * 20
        files = [make_test_file()]
        report = self.analyzer.analyze(
            user_message=long_message,
            workspace_files=files,
        )
        assert len(report.user_intent_summary) <= 100

    # ── 多关键词匹配去重 ──

    def test_multiple_keyword_matches(self):
        """同时匹配多个关键词时，agents 列表去重。"""
        files = [make_test_file()]
        # "添加API接口的页面布局" 同时匹配 backend 和 frontend
        report = self.analyzer.analyze(
            user_message="添加API接口的页面布局",
            workspace_files=files,
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
