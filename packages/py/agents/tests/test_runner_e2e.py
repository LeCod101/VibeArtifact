"""
AgentRunner 端到端测试模块。

使用 MockLLMProvider 跑通 intent_agent 的完整流程：
MockLLM -> prompt 拼装 -> LLM 调用 -> 响应解析 -> Translator 翻译 -> 结果返回
"""

import pytest
from agents.configs.definitions import register_all_agents
from agents.executors.runner import AgentRunner
from agents.schemas.intent import IntentOutput
from runtime_tools.cost.tracker import CostTracker
from runtime_tools.llm.config import LLMConfig
from runtime_tools.llm.mock_provider import MockLLMProvider


class TestRunnerIntentE2E:
    """AgentRunner + IntentAgent 端到端测试。"""

    @pytest.mark.asyncio
    async def test_runner_intent_agent_e2e(
        self, sample_agent_input, mock_intent_output_json
    ):
        """端到端测试：MockLLM -> intent_agent -> Translator -> 结果。"""
        # 准备
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)
        cost_tracker = CostTracker()

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
            cost_tracker=cost_tracker,
        )

        # 执行
        result = await runner.run("intent", sample_agent_input)

        # 验证 agent_id
        assert result.agent_id == "intent"

    @pytest.mark.asyncio
    async def test_output_is_intent_output(
        self, sample_agent_input, mock_intent_output_json
    ):
        """AgentRunResult.output 是 IntentOutput 实例。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)
        assert isinstance(result.output, IntentOutput)

    @pytest.mark.asyncio
    async def test_operations_not_empty(
        self, sample_agent_input, mock_intent_output_json
    ):
        """AgentRunResult.operations 不为空（包含 scope 节点创建操作）。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)
        assert len(result.operations) > 0

    @pytest.mark.asyncio
    async def test_meta_contains_model_info(
        self, sample_agent_input, mock_intent_output_json
    ):
        """AgentRunResult.meta 包含 model、prompt_tokens 等。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)
        assert result.meta is not None
        assert result.meta.prompt_tokens > 0
        assert result.meta.model != ""

    @pytest.mark.asyncio
    async def test_cost_tracker_records_call(
        self, sample_agent_input, mock_intent_output_json
    ):
        """CostTracker 记录了调用信息。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)
        cost_tracker = CostTracker()

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
            cost_tracker=cost_tracker,
        )

        await runner.run("intent", sample_agent_input)

        # 验证成本记录
        assert cost_tracker.get_total_cost() > 0
        assert len(cost_tracker.get_records()) == 1

    @pytest.mark.asyncio
    async def test_llm_messages_contain_system_and_user(
        self, sample_agent_input, mock_intent_output_json
    ):
        """LLM 调用时的 messages 包含 system + user。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        await runner.run("intent", sample_agent_input)

        # 验证 LLM 调用历史
        assert len(mock_provider._call_history) == 1
        call = mock_provider._call_history[0]
        roles = [m.role for m in call.messages]
        assert "system" in roles
        assert "user" in roles

    @pytest.mark.asyncio
    async def test_warnings_include_deferred_items(
        self, sample_agent_input, mock_intent_output_json
    ):
        """mock_intent_output 包含 deferred_items，warnings 中应有延后提示。"""
        register_all_agents()
        mock_provider = MockLLMProvider()
        mock_provider.set_response(mock_intent_output_json)

        runner = AgentRunner(
            llm_provider=mock_provider,
            llm_config=LLMConfig(),
        )

        result = await runner.run("intent", sample_agent_input)

        # mock 数据中有 deferred_items: ["团队协作", "日历集成"]
        # translator 应该将其作为 warning
        deferred_warnings = [w for w in result.warnings if "延后" in w]
        assert len(deferred_warnings) > 0
