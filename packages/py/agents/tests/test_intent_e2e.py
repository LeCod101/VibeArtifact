"""
Intent Agent 端到端测试。

使用 MockLLMProvider 模拟 LLM 调用，验证完整流程：
user_idea → AgentRunner.run("intent", ...) → IntentOutput → ScopeDraft → CapacityReport

覆盖：
- mock LLM 返回合法 JSON → AgentRunResult 包含正确的 operations
- IntentOutput.scope_draft → CapacityCalculator → 验证报告正确
"""

import json

import pytest
from agents.capacity.calculator import CapacityCalculator
from agents.capacity.tiers import CapacityTier
from agents.configs.definitions import register_all_agents
from agents.executors.runner import AgentRunner
from agents.schemas.intent import IntentOutput
from ir_core.schema.operation_types import OperationType
from runtime_tools.llm.config import LLMConfig
from runtime_tools.llm.mock_provider import MockLLMProvider

# ============================================================
# Mock 数据
# ============================================================


def _make_intent_output_json(num_scopes: int = 3) -> str:
    """构造 IntentOutput 的 JSON 字符串。

    参数：
        num_scopes: scope 数量

    返回：
        JSON 字符串
    """
    scopes = [
        {
            "name": f"功能模块{i + 1}",
            "description": f"功能模块{i + 1}的详细描述",
            "priority": "high" if i == 0 else "medium",
            "tags": ["core"] if i == 0 else [],
        }
        for i in range(num_scopes)
    ]
    return json.dumps(
        {
            "reasoning": "基于用户需求分析，提取核心功能模块",
            "confidence": 0.9,
            "warnings": [],
            "scope_draft": {
                "product_name": "MockApp",
                "product_description": "Mock 测试应用",
                "scopes": scopes,
                "deferred_items": ["高级搜索", "数据分析"],
                "risks": ["需求范围可能扩大"],
            },
        },
        ensure_ascii=False,
    )


# ============================================================
# Intent Agent 端到端测试
# ============================================================


class TestIntentE2E:
    """Intent Agent 端到端测试 — 使用 MockLLMProvider。"""

    @pytest.mark.asyncio
    async def test_intent_mock_e2e(self, sample_agent_input):
        """mock LLM 返回合法 JSON → 验证 AgentRunResult 包含正确的 operations。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_intent_output_json(3))

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)

        # 验证 agent_id
        assert result.agent_id == "intent"

        # 验证 output 是 IntentOutput
        assert isinstance(result.output, IntentOutput)

        # 验证 scope_draft 包含 3 个 scope
        assert len(result.output.scope_draft.scopes) == 3

        # 验证 operations 包含 create_node 操作
        create_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        # 3 个 scope + 1 个 risk = 4 个 create_node
        assert len(create_ops) >= 3

        # 验证 warnings 包含延后信息
        deferred_warnings = [w for w in result.warnings if "延后" in w]
        assert len(deferred_warnings) > 0

    @pytest.mark.asyncio
    async def test_intent_capacity_integration(self, sample_agent_input):
        """IntentOutput.scope_draft → CapacityCalculator → 验证报告。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_intent_output_json(3))

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)

        # 取出 scope_draft
        output: IntentOutput = result.output
        scope_draft = output.scope_draft

        # 用 CapacityCalculator 计算
        calculator = CapacityCalculator()
        report = calculator.calculate(scope_draft)

        # 3 个 scope，无特殊 tags：
        # pages=3*3=9, api=6*2=12, db=3*4=12 → 总 33 点 → medium
        assert report.total_points == 33
        assert report.tier == CapacityTier.MEDIUM
        assert report.needs_contraction is True
        assert report.must_contract is False

    @pytest.mark.asyncio
    async def test_intent_meta_populated(self, sample_agent_input):
        """验证 meta 包含 model 和 token 信息。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_intent_output_json(2))

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)

        assert result.meta is not None
        assert result.meta.provider == "mock"
        assert result.meta.prompt_tokens > 0
        assert result.meta.completion_tokens > 0

    @pytest.mark.asyncio
    async def test_intent_with_auth_scope(self, sample_agent_input):
        """包含 auth tag 的 scope → capacity 报告中 auth_flows > 0。"""
        # 构造包含 auth tag 的输出
        output_json = json.dumps(
            {
                "reasoning": "包含认证功能",
                "confidence": 0.85,
                "warnings": [],
                "scope_draft": {
                    "product_name": "AuthApp",
                    "product_description": "带认证的应用",
                    "scopes": [
                        {
                            "name": "用户认证",
                            "description": "注册和登录",
                            "priority": "high",
                            "tags": ["auth"],
                        },
                        {
                            "name": "任务管理",
                            "description": "CRUD 任务",
                            "priority": "medium",
                            "tags": ["core"],
                        },
                    ],
                    "deferred_items": [],
                    "risks": [],
                },
            },
            ensure_ascii=False,
        )

        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)
        output: IntentOutput = result.output

        calculator = CapacityCalculator()
        report = calculator.calculate(output.scope_draft)

        # auth tag → auth_flows 应该 >= 1
        dim_map = {d.dimension.value: d for d in report.dimensions}
        assert dim_map["auth_flows"].count >= 1
