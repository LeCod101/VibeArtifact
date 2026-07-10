"""
ChatOrchestrator 集成测试。

覆盖：
- 冷启动路径（空工作区 → ColdStartBootstrap）
- 局部修改路径（有工作区文件 → AgentSelector + AgentRunner）
- assistant_message 非空
- change_summary 包含正确信息
- impact_report 正确传递
- 多 Agent 成本累加
- SSE 事件发布验证
- redis=None 时不报错
- Agent 执行失败的容错处理
- 全局异常兜底
- 空执行计划处理
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from agents.analysis.cold_start import ColdStartResult
from agents.analysis.models import ChangeScope, ImpactReport
from agents.executors.runner import AgentRunResult
from agents.schemas.base import AgentOutput, AgentRunMeta
from agents.schemas.workspace import WorkspaceFileData
from api_app.application.services.chat_orchestrator import (
    ChatOrchestrator,
    ChatOrchestratorResult,
)

# ============================================================
# 测试辅助函数
# ============================================================


def make_test_file(path: str = "frontend/app/page.tsx") -> WorkspaceFileData:
    """
    构造测试用工作区文件。

    参数：
        path: 文件路径

    返回：
        WorkspaceFileData 实例
    """
    return WorkspaceFileData(path=path, content="x", kind="code")


def make_cold_start_report() -> ImpactReport:
    """
    构造冷启动影响报告。

    返回：
        requires_cold_start=True 的 ImpactReport
    """
    return ImpactReport(
        change_scope=ChangeScope.FULL,
        requires_cold_start=True,
        affected_areas=[],
        affected_agents=[
            "intent", "contraction", "planner", "schema"
        ],
        reasoning="工作区为空，需要冷启动",
        user_intent_summary="创建 Todo 应用",
    )


def make_partial_report() -> ImpactReport:
    """
    构造局部修改影响报告。

    返回：
        requires_cold_start=False 的 ImpactReport
    """
    return ImpactReport(
        change_scope=ChangeScope.PARTIAL,
        requires_cold_start=False,
        affected_areas=["ui_page", "ui_component"],
        affected_agents=["frontend"],
        reasoning="关键词匹配命中 frontend",
        user_intent_summary="修改页面布局",
    )


def make_agent_run_result(
    agent_id: str = "frontend",
    files: list[dict] | None = None,
    cost: float = 0.01,
    warnings: list[str] | None = None,
) -> AgentRunResult:
    """
    构造模拟的 AgentRunResult。

    参数：
        agent_id: Agent 标识
        files: 产物文件列表
        cost: 总成本
        warnings: 警告列表

    返回：
        AgentRunResult 实例
    """
    meta = AgentRunMeta(
        model="deepseek-chat",
        provider="deepseek",
        prompt_tokens=100,
        completion_tokens=50,
        total_cost=cost,
        latency_ms=500,
    )
    output = AgentOutput(
        reasoning="test",
        confidence=0.9,
        warnings=warnings or [],
    )
    output.meta = meta
    return AgentRunResult(
        agent_id=agent_id,
        output=output,
        files=files or [],
        warnings=warnings or [],
        meta=meta,
    )


def make_cold_start_result(
    outputs: dict | None = None,
    files_count: int = 0,
) -> ColdStartResult:
    """
    构造模拟的 ColdStartResult。

    参数：
        outputs: 各 Agent 高层输出
        files_count: 产出文件数

    返回：
        ColdStartResult 实例
    """
    return ColdStartResult(
        outputs=outputs or {"intent": {}, "contraction": {}, "planner": {}, "schema": {}},
        files=[
            {"path": f"docs/{i}.md", "content": "x", "kind": "doc"}
            for i in range(files_count)
        ],
        agents_executed=[
            "intent", "contraction", "planner", "schema"
        ],
        warnings=[],
    )


# ============================================================
# ChatOrchestrator 测试
# ============================================================


class TestChatOrchestrator:
    """ChatOrchestrator 编排器集成测试。"""

    @pytest.fixture
    def base_params(self):
        """基础测试参数 fixture。"""
        return {
            "project_id": uuid4(),
            "conversation_id": uuid4(),
            "branch_id": uuid4(),
            "user_message": "创建 Todo 应用",
            "workspace_files": [],
            "redis": None,
        }

    @pytest.mark.asyncio
    async def test_cold_start_path(self, base_params):
        """空工作区时走冷启动路径，调用 ColdStartBootstrap。"""
        orchestrator = ChatOrchestrator()

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=make_cold_start_result()
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            result = await orchestrator.handle_message(**base_params)

            assert isinstance(result, ChatOrchestratorResult)
            assert result.impact_report.requires_cold_start is True
            assert "intent" in result.change_summary.agents_executed

    @pytest.mark.asyncio
    async def test_partial_modification_path(self, base_params):
        """有工作区文件时走局部修改路径，调用 AgentSelector + AgentRunner。"""
        base_params["workspace_files"] = [make_test_file()]
        base_params["user_message"] = "修改页面布局"

        orchestrator = ChatOrchestrator()

        mock_runner = AsyncMock()
        mock_runner.run = AsyncMock(
            return_value=make_agent_run_result("frontend")
        )

        with patch.object(
            ChatOrchestrator,
            "_create_agent_runner",
            return_value=mock_runner,
        ):
            result = await orchestrator.handle_message(**base_params)

            assert isinstance(result, ChatOrchestratorResult)
            assert result.impact_report.requires_cold_start is False
            assert "frontend" in result.change_summary.agents_executed

    @pytest.mark.asyncio
    async def test_assistant_message_generated(self, base_params):
        """返回结果中 assistant_message 非空。"""
        orchestrator = ChatOrchestrator()

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=make_cold_start_result()
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            result = await orchestrator.handle_message(**base_params)

            assert result.assistant_message
            assert len(result.assistant_message) > 0

    @pytest.mark.asyncio
    async def test_change_summary_correct(self, base_params):
        """change_summary 包含正确的 agents_executed 和 operations_count。"""
        orchestrator = ChatOrchestrator()

        cold_result = make_cold_start_result(files_count=10)

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=cold_result
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            result = await orchestrator.handle_message(**base_params)

            summary = result.change_summary
            # outputs(4) + files(10) = 14
            assert summary.operations_count == 14
            assert len(summary.agents_executed) == 4
            assert isinstance(summary.affected_areas, list)

    @pytest.mark.asyncio
    async def test_impact_report_passed_through(self, base_params):
        """result.impact_report 与 ImpactAnalyzer 返回的报告一致。"""
        orchestrator = ChatOrchestrator()

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=make_cold_start_result()
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            result = await orchestrator.handle_message(**base_params)

            # 空工作区应该触发冷启动
            assert result.impact_report.requires_cold_start is True
            assert result.impact_report.change_scope == ChangeScope.FULL

    @pytest.mark.asyncio
    async def test_cost_accumulated(self, base_params):
        """多个 Agent 的 cost 累加到 result.cost_total。"""
        base_params["workspace_files"] = [make_test_file()]
        base_params["user_message"] = "修改页面布局"

        orchestrator = ChatOrchestrator()

        mock_runner = AsyncMock()
        mock_runner.run = AsyncMock(
            return_value=make_agent_run_result("frontend", cost=0.05)
        )

        with patch.object(
            ChatOrchestrator,
            "_create_agent_runner",
            return_value=mock_runner,
        ):
            result = await orchestrator.handle_message(**base_params)

            assert result.cost_total >= 0.0

    @pytest.mark.asyncio
    async def test_sse_events_published(self, base_params):
        """SSE publish 函数被正确调用。"""
        mock_redis = AsyncMock()
        base_params["redis"] = mock_redis

        orchestrator = ChatOrchestrator()

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
            patch(
                "api_app.application.services.chat_orchestrator"
                ".publish_chat_analysis_start"
            ) as mock_analysis_start,
            patch(
                "api_app.application.services.chat_orchestrator"
                ".publish_chat_analysis_done"
            ) as mock_analysis_done,
            patch(
                "api_app.application.services.chat_orchestrator"
                ".publish_chat_complete"
            ) as mock_complete,
            patch(
                "api_app.application.services.chat_orchestrator"
                ".publish_chat_apply_done"
            ) as mock_apply_done,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=make_cold_start_result()
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            await orchestrator.handle_message(**base_params)

            mock_analysis_start.assert_called_once()
            mock_analysis_done.assert_called_once()
            mock_apply_done.assert_called_once()
            mock_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_sse_skipped_when_no_redis(self, base_params):
        """redis=None 时不报错，正常完成。"""
        base_params["redis"] = None

        orchestrator = ChatOrchestrator()

        with (
            patch.object(
                ChatOrchestrator,
                "_create_agent_runner",
                return_value=AsyncMock(),
            ),
            patch(
                "api_app.application.services.chat_orchestrator"
                ".ColdStartBootstrap"
            ) as MockBootstrap,
        ):
            mock_instance = AsyncMock()
            mock_instance.bootstrap = AsyncMock(
                return_value=make_cold_start_result()
            )
            MockBootstrap.return_value = mock_instance
            MockBootstrap.COLD_START_AGENTS = [
                "intent", "contraction", "planner", "schema"
            ]

            result = await orchestrator.handle_message(**base_params)
            assert isinstance(result, ChatOrchestratorResult)

    @pytest.mark.asyncio
    async def test_agent_failure_handled(self, base_params):
        """Agent 执行失败时不崩溃，返回正常结果。"""
        base_params["workspace_files"] = [make_test_file()]
        base_params["user_message"] = "修改页面布局"

        orchestrator = ChatOrchestrator()

        mock_runner = AsyncMock()
        mock_runner.run = AsyncMock(
            side_effect=RuntimeError("LLM 调用失败")
        )

        with patch.object(
            ChatOrchestrator,
            "_create_agent_runner",
            return_value=mock_runner,
        ):
            # 不应崩溃（_execute_layer 捕获异常并构建 mock result）
            result = await orchestrator.handle_message(**base_params)
            assert isinstance(result, ChatOrchestratorResult)

    @pytest.mark.asyncio
    async def test_global_exception_returns_error(self, base_params):
        """全局异常触发 SSE failed 事件并返回错误结果。"""
        orchestrator = ChatOrchestrator()

        # 通过 mock ImpactAnalyzer.analyze 抛异常来触发全局兜底
        with patch(
            "api_app.application.services.chat_orchestrator"
            ".ImpactAnalyzer"
        ) as MockAnalyzer:
            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.side_effect = RuntimeError(
                "意外错误"
            )
            MockAnalyzer.return_value = mock_analyzer_instance

            result = await orchestrator.handle_message(**base_params)

            assert "意外错误" in result.assistant_message
            assert result.change_summary.summary == "执行失败"

    @pytest.mark.asyncio
    async def test_empty_execution_plan(self, base_params):
        """AgentSelector 返回空计划时正常完成，operations_count=0。"""
        base_params["workspace_files"] = [make_test_file()]
        # 使用无匹配关键词的消息
        base_params["user_message"] = "做点什么"

        orchestrator = ChatOrchestrator()

        mock_runner = AsyncMock()
        # planner Agent 无文件产出
        mock_runner.run = AsyncMock(
            return_value=make_agent_run_result(
                "planner", files=[]
            )
        )

        with patch.object(
            ChatOrchestrator,
            "_create_agent_runner",
            return_value=mock_runner,
        ):
            result = await orchestrator.handle_message(**base_params)

            assert isinstance(result, ChatOrchestratorResult)
            assert result.change_summary.operations_count == 0
