"""
M8 SummaryGenerator + DecisionExtractor 单元测试。

覆盖：
- SummaryGenerator: 压缩阈值判断、基本摘要生成、增量摘要、截断
- DecisionExtractor: 空消息、技术选型、功能范围、多条决策
- DecisionRecord: 字段校验
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from agents.analysis.decision_extractor import DecisionExtractor, DecisionRecord
from agents.analysis.summary_generator import SummaryGenerator

# ============================================================
# 测试辅助函数
# ============================================================


def make_msg(role: str, content: str) -> SimpleNamespace:
    """构造测试用消息对象。

    参数:
        role: 消息角色（"user" / "assistant"）
        content: 消息文本内容

    返回:
        SimpleNamespace 模拟消息对象
    """
    return SimpleNamespace(
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def make_conversation(rounds: int) -> list[SimpleNamespace]:
    """构造指定轮数的模拟对话消息列表。

    每轮包含一条 user 消息和一条 assistant 消息。

    参数:
        rounds: 对话轮数

    返回:
        消息列表
    """
    messages = []
    for i in range(rounds):
        messages.append(make_msg("user", f"用户第{i+1}轮消息"))
        messages.append(
            make_msg("assistant", f"助手第{i+1}轮回复摘要\n详细内容第{i+1}轮...")
        )
    return messages


# ============================================================
# SummaryGenerator 测试
# ============================================================


class TestSummaryGenerator:
    """SummaryGenerator 对话摘要生成器测试。"""

    def setup_method(self):
        """每个测试方法前创建 SummaryGenerator 实例。"""
        self.gen = SummaryGenerator()

    @pytest.mark.asyncio
    async def test_should_compress_below_threshold(self):
        """消息数少于阈值（10 轮），不需要压缩。"""
        messages = make_conversation(8)
        result = await self.gen.should_compress(messages)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_compress_above_threshold(self):
        """消息数超过阈值（10 轮），需要压缩。"""
        messages = make_conversation(12)
        result = await self.gen.should_compress(messages)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_compress_exact_threshold(self):
        """消息数恰好等于阈值（10 轮），不需要压缩。"""
        messages = make_conversation(10)
        result = await self.gen.should_compress(messages)
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_summary_basic(self):
        """基本摘要生成：提取 assistant 消息的第一行。"""
        messages = [
            make_msg("user", "创建 Todo 应用"),
            make_msg("assistant", "已创建 Todo 基础结构\n包含增删改查功能"),
            make_msg("user", "添加用户认证"),
            make_msg("assistant", "已添加 JWT 认证\n支持登录注册"),
        ]
        summary = await self.gen.generate_summary(messages)

        assert "已创建 Todo 基础结构" in summary
        assert "已添加 JWT 认证" in summary
        # 不应包含详细内容
        assert "包含增删改查功能" not in summary

    @pytest.mark.asyncio
    async def test_generate_summary_with_existing(self):
        """增量摘要：包含旧 summary 内容。"""
        existing = "之前的摘要内容"
        messages = [
            make_msg("assistant", "新一轮的变更\n详细说明"),
        ]
        summary = await self.gen.generate_summary(messages, existing_summary=existing)

        assert summary.startswith("之前的摘要内容")
        assert "新一轮的变更" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_truncation(self):
        """超长摘要截断到 MAX_SUMMARY_LENGTH 字符。"""
        # 构造大量消息使摘要超长
        messages = []
        for i in range(200):
            messages.append(
                make_msg("assistant", f"这是一段非常长的助手回复摘要第{i}轮内容信息")
            )
        summary = await self.gen.generate_summary(messages)

        assert len(summary) <= SummaryGenerator.MAX_SUMMARY_LENGTH
        assert summary.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_summary_empty_messages(self):
        """空消息列表生成空摘要。"""
        summary = await self.gen.generate_summary([])
        assert summary == ""

    @pytest.mark.asyncio
    async def test_generate_summary_user_only_messages(self):
        """只有 user 消息时，摘要为空（只提取 assistant 消息）。"""
        messages = [
            make_msg("user", "问题1"),
            make_msg("user", "问题2"),
        ]
        summary = await self.gen.generate_summary(messages)
        assert summary == ""


# ============================================================
# DecisionExtractor 测试
# ============================================================


class TestDecisionExtractor:
    """DecisionExtractor 决策抽取器测试。"""

    def setup_method(self):
        """每个测试方法前创建 DecisionExtractor 实例。"""
        self.extractor = DecisionExtractor()

    @pytest.mark.asyncio
    async def test_extract_decisions_empty(self):
        """空消息列表无决策。"""
        decisions = await self.extractor.extract_decisions([])
        assert decisions == []

    @pytest.mark.asyncio
    async def test_extract_decisions_no_keywords(self):
        """不含决策关键词的消息不产生决策。"""
        messages = [
            make_msg("user", "你好，请帮我看看"),
            make_msg("assistant", "好的，请问有什么需要？"),
        ]
        decisions = await self.extractor.extract_decisions(messages)
        assert decisions == []

    @pytest.mark.asyncio
    async def test_extract_decisions_tech_choice(self):
        """技术选型决策：包含 "采用" 关键词。"""
        messages = [
            make_msg("user", "我要采用PostgreSQL作为数据库"),
            make_msg("assistant", "好的，已配置 PostgreSQL"),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 1
        assert decisions[0].decision_type == "tech_choice"
        assert "PostgreSQL" in decisions[0].description

    @pytest.mark.asyncio
    async def test_extract_decisions_feature_scope(self):
        """功能范围决策：包含 "去掉" 关键词。"""
        messages = [
            make_msg("user", "去掉用户注册功能，只保留登录"),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 1
        assert decisions[0].decision_type == "feature_scope"

    @pytest.mark.asyncio
    async def test_extract_decisions_priority(self):
        """优先级决策：包含 "优先" 关键词。"""
        messages = [
            make_msg("user", "优先完成支付模块"),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 1
        assert decisions[0].decision_type == "priority"

    @pytest.mark.asyncio
    async def test_extract_decisions_architecture(self):
        """架构决策：包含 "拆分" 关键词。"""
        messages = [
            make_msg("user", "把用户模块拆分为认证和用户管理两个子模块"),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 1
        assert decisions[0].decision_type == "architecture"

    @pytest.mark.asyncio
    async def test_extract_decisions_multiple(self):
        """多条消息产生多条决策。"""
        messages = [
            make_msg("user", "采用 Redis 作为缓存"),
            make_msg("assistant", "好的"),
            make_msg("user", "去掉图片上传功能"),
            make_msg("assistant", "已移除"),
            make_msg("user", "优先做首页"),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 3
        types = [d.decision_type for d in decisions]
        assert "tech_choice" in types
        assert "feature_scope" in types
        assert "priority" in types

    @pytest.mark.asyncio
    async def test_extract_decisions_assistant_ignored(self):
        """只从 user 消息中抽取决策，忽略 assistant 消息。"""
        messages = [
            make_msg("assistant", "建议采用 MongoDB"),
            make_msg("user", "你好，能帮我看看项目吗？"),
        ]
        decisions = await self.extractor.extract_decisions(messages)
        assert decisions == []

    @pytest.mark.asyncio
    async def test_extract_decisions_title_truncation(self):
        """长消息标题截断到 50 字符加省略号。"""
        long_content = "采用" + "一段非常长的技术描述内容" * 10
        messages = [
            make_msg("user", long_content),
        ]
        decisions = await self.extractor.extract_decisions(messages)

        assert len(decisions) == 1
        assert len(decisions[0].title) <= DecisionExtractor.TITLE_MAX_LENGTH + 3
        assert decisions[0].title.endswith("...")

    @pytest.mark.asyncio
    async def test_write_to_ir_returns_operations(self):
        """write_to_ir 返回正确的 IROperation payload 列表。"""
        from uuid import uuid4

        decisions = [
            DecisionRecord(
                decision_type="tech_choice",
                title="采用 PostgreSQL",
                description="数据库选择 PostgreSQL",
                rationale="用户明确指定",
                affected_nodes=[],
                timestamp=datetime.now(timezone.utc),
            ),
        ]

        # 不需要真实 db，write_to_ir 在 Phase 1 只构造 payload
        operations = await self.extractor.write_to_ir(
            db=None,
            project_id=uuid4(),
            snapshot_id=uuid4(),
            decisions=decisions,
        )

        assert len(operations) == 1
        assert operations[0]["operation_type"] == "create_node"
        assert operations[0]["node_type"] == "decision"
        assert operations[0]["label"] == "采用 PostgreSQL"
        assert operations[0]["props"]["status"] == "accepted"


# ============================================================
# DecisionRecord 模型测试
# ============================================================


class TestDecisionRecord:
    """DecisionRecord 数据模型测试。"""

    def test_decision_record_schema(self):
        """DecisionRecord 字段校验：所有必填字段正确。"""
        record = DecisionRecord(
            decision_type="tech_choice",
            title="选择 PostgreSQL",
            description="使用 PostgreSQL 作为主数据库",
            rationale="稳定可靠，社区活跃",
            affected_nodes=["node-1", "node-2"],
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        assert record.decision_type == "tech_choice"
        assert record.title == "选择 PostgreSQL"
        assert len(record.affected_nodes) == 2
        assert record.timestamp.year == 2025

    def test_decision_record_defaults(self):
        """DecisionRecord 默认值：affected_nodes 默认为空列表。"""
        record = DecisionRecord(
            decision_type="priority",
            title="先做首页",
            description="优先完成首页",
            rationale="用户要求",
            timestamp=datetime.now(timezone.utc),
        )
        assert record.affected_nodes == []
