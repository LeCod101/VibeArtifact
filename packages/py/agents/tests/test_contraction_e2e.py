"""
Contraction Agent 端到端测试。

使用 MockLLMProvider 模拟 LLM 调用，验证完整流程：
ContractionInput → AgentRunner.run("contraction", ...) → ContractionOutput

覆盖：
- mock LLM 返回合法 ContractionOutput JSON → 验证 AgentRunResult
- 收缩后的 scope_draft → CapacityCalculator → 验证容量降低
- decision 字段完整性验证
"""

import json
from uuid import uuid4

import pytest
from agents.capacity.calculator import CapacityCalculator
from agents.capacity.tiers import CapacityTier
from agents.configs.definitions import register_all_agents
from agents.executors.runner import AgentRunner
from agents.schemas.base import AgentInput
from agents.schemas.contraction import ContractionOutput
from ir_core.schema.operation_types import OperationType
from runtime_tools.llm.config import LLMConfig
from runtime_tools.llm.mock_provider import MockLLMProvider

# ============================================================
# Mock 数据
# ============================================================


def _make_contraction_output_json() -> str:
    """构造 ContractionOutput 的 JSON 字符串。

    模拟收缩 agent 裁剪后的结果：
    从 5 个模块收缩为 2 个，延后 3 个。

    返回：
        ContractionOutput 的 JSON 字符串
    """
    return json.dumps(
        {
            "reasoning": "根据容量分析，裁剪低优先级功能",
            "confidence": 0.88,
            "warnings": ["已裁剪 3 个功能"],
            "scope_draft": {
                "product_name": "收缩后App",
                "product_description": "经过 MVP 收缩的应用",
                "scopes": [
                    {
                        "name": "用户管理",
                        "description": "注册登录和个人信息",
                        "priority": "high",
                        "tags": ["auth"],
                    },
                    {
                        "name": "任务管理",
                        "description": "创建和管理待办任务",
                        "priority": "high",
                        "tags": ["core"],
                    },
                ],
                "deferred_items": ["报表分析", "团队协作", "文件上传"],
                "risks": ["收缩可能导致功能不完整"],
            },
            "decision": {
                "retained_features": ["用户管理", "任务管理"],
                "deferred_features": [
                    {"name": "报表分析", "reason": "低优先级，延后处理"},
                    {"name": "团队协作", "reason": "复杂度高，延后到 V2"},
                    {"name": "文件上传", "reason": "非核心功能，延后处理"},
                ],
                "risks": ["裁剪后功能较少，用户体验受限"],
                "rationale": "为控制 MVP 规模，保留核心功能",
            },
        },
        ensure_ascii=False,
    )


# ============================================================
# Contraction Agent 端到端测试
# ============================================================


class TestContractionE2E:
    """Contraction Agent 端到端测试 — 使用 MockLLMProvider。"""

    @pytest.mark.asyncio
    async def test_contraction_mock_e2e(self):
        """mock LLM 返回合法 JSON → 验证 AgentRunResult。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_contraction_output_json())

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        # 构造 contraction agent 的输入
        agent_input = AgentInput(
            project_id=uuid4(),
            snapshot_id=uuid4(),
            ir_nodes=[],
            ir_edges=[],
            task_description="收缩功能范围到 MVP",
        )

        result = await runner.run("contraction", agent_input)

        # 验证 agent_id
        assert result.agent_id == "contraction"

        # 验证 output 是 ContractionOutput
        assert isinstance(result.output, ContractionOutput)

        # 验证 scope_draft 包含 2 个保留的 scope
        output: ContractionOutput = result.output
        assert len(output.scope_draft.scopes) == 2

        # 验证 decision 字段完整
        assert len(output.decision.retained_features) == 2
        assert len(output.decision.deferred_features) == 3
        assert len(output.decision.risks) == 1
        assert output.decision.rationale != ""

    @pytest.mark.asyncio
    async def test_contraction_operations_generated(self):
        """验证 ContractionTranslator 生成了 IR 操作。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_contraction_output_json())

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        agent_input = AgentInput(
            project_id=uuid4(),
            snapshot_id=uuid4(),
            ir_nodes=[],
            ir_edges=[],
            task_description="收缩功能范围",
        )

        result = await runner.run("contraction", agent_input)

        # 应有 create_node 操作（scope + decision + risk）
        create_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        # 2 scope + 3 decision + 1 risk = 6
        assert len(create_ops) == 6

        # 应有 create_edge 操作（scope→decision + risk→scope）
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
        ]
        # 3 个 decision 各与第一个 scope 建边 + 1 个 risk 与第一个 scope 建边 = 4
        assert len(edge_ops) == 4

    @pytest.mark.asyncio
    async def test_contraction_capacity_reduction(self):
        """收缩后 scope_draft → CapacityCalculator → 验证容量降低。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_contraction_output_json())

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        agent_input = AgentInput(
            project_id=uuid4(),
            snapshot_id=uuid4(),
            ir_nodes=[],
            ir_edges=[],
            task_description="收缩功能范围",
        )

        result = await runner.run("contraction", agent_input)
        output: ContractionOutput = result.output

        # 计算收缩后的容量
        calculator = CapacityCalculator()
        report = calculator.calculate(output.scope_draft)

        # 2 个 scope（1 个带 auth tag）：
        # pages=2*3=6, api=4*2=8, db=2*4=8, auth=1*5=5 → 总 27 点 → small
        assert report.total_points == 27
        assert report.tier == CapacityTier.SMALL

    @pytest.mark.asyncio
    async def test_contraction_warnings_include_deferred(self):
        """warnings 包含延后功能信息。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(_make_contraction_output_json())

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        agent_input = AgentInput(
            project_id=uuid4(),
            snapshot_id=uuid4(),
            ir_nodes=[],
            ir_edges=[],
            task_description="收缩功能范围",
        )

        result = await runner.run("contraction", agent_input)

        # warnings 中应包含延后功能相关信息
        deferred_warnings = [w for w in result.warnings if "延后" in w]
        assert len(deferred_warnings) > 0
