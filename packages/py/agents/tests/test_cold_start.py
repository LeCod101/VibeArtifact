"""
ColdStartBootstrap 单元测试。

覆盖：
- 按顺序执行 4 个 Agent（intent/contraction/planner/schema）
- 每步高层输出被并入 upstream_outputs，供下一步参考
- agents_executed 列表正确记录
- 产物文件被累积到 files
- 单个 Agent 失败时继续执行下一个
- 所有 Agent 都失败时返回空结果 + 4 条 warnings
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from agents.analysis.cold_start import ColdStartBootstrap
from agents.configs.definitions import register_all_agents
from agents.executors.runner import AgentRunResult
from agents.schemas.contraction import ContractionDecision, ContractionOutput
from agents.schemas.high_level import (
    EndpointSpec,
    EntitySpec,
    SchemaPlan,
    ScopeDraft,
    ScopeItem,
    TaskPlan,
    TaskStep,
)
from agents.schemas.intent import IntentOutput
from agents.schemas.planner import PlannerOutput
from agents.schemas.schema_agent import SchemaOutput

# ============================================================
# 测试辅助函数
# ============================================================


def _make_scope_draft() -> ScopeDraft:
    """构造最小 ScopeDraft，供各 Agent mock 输出复用。"""
    return ScopeDraft(
        product_name="TodoApp",
        product_description="测试应用",
        scopes=[
            ScopeItem(name="任务管理", description="CRUD", priority="high", tags=[]),
        ],
    )


# 每个 Agent 对应的高层输出构造函数（生成真实类型实例，而非泛型 AgentOutput）
_OUTPUT_FACTORIES = {
    "intent": lambda: IntentOutput(
        reasoning="r", confidence=0.9, scope_draft=_make_scope_draft(),
    ),
    "contraction": lambda: ContractionOutput(
        reasoning="r", confidence=0.9, scope_draft=_make_scope_draft(),
        decision=ContractionDecision(
            retained_features=["任务管理"], deferred_features=[],
            risks=[], rationale="保留核心功能",
        ),
    ),
    "planner": lambda: PlannerOutput(
        reasoning="r", confidence=0.9,
        task_plan=TaskPlan(
            steps=[TaskStep(step_id="s1", agent_id="schema", description="设计模型")],
            estimated_complexity="small",
        ),
    ),
    "schema": lambda: SchemaOutput(
        reasoning="r", confidence=0.9,
        schema_plan=SchemaPlan(
            entities=[EntitySpec(name="Task", fields=[])],
            endpoints=[
                EndpointSpec(method="GET", path="/tasks", description="列表"),
            ],
        ),
    ),
}


def make_mock_result(agent_id: str = "test", files=None, warnings=None):
    """
    构造模拟的 AgentRunResult，output 为对应 Agent 的真实输出类型。

    参数：
        agent_id: Agent 标识
        files: 文件列表（默认空）
        warnings: 警告列表（默认空）

    返回：
        AgentRunResult 实例
    """
    output = _OUTPUT_FACTORIES[agent_id]()
    output.warnings = warnings or []
    return AgentRunResult(
        agent_id=agent_id,
        output=output,
        files=files or [],
        warnings=warnings or [],
        meta=None,
    )


# ============================================================
# ColdStartBootstrap 测试
# ============================================================


class TestColdStartBootstrap:
    """ColdStartBootstrap 冷启动引导器测试。"""

    @pytest.fixture
    def mock_runner(self):
        """创建模拟 AgentRunner。"""
        return AsyncMock()

    @pytest.fixture
    def project_id(self):
        """创建测试用项目 ID，并确保 AgentRegistry 已注册。"""
        register_all_agents()
        return uuid4()

    @pytest.mark.asyncio
    async def test_bootstrap_executes_four_agents(
        self, mock_runner, project_id
    ):
        """验证冷启动按顺序执行 intent/contraction/planner/schema 四个 Agent。"""

        async def fake_run(agent_id, agent_input):
            return make_mock_result(agent_id)

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        # 验证调用了 4 次
        assert mock_runner.run.call_count == 4

        # 验证调用顺序
        call_agent_ids = [
            call.args[0] for call in mock_runner.run.call_args_list
        ]
        assert call_agent_ids == [
            "intent", "contraction", "planner", "schema"
        ]

    @pytest.mark.asyncio
    async def test_bootstrap_accumulates_upstream_outputs(
        self, mock_runner, project_id
    ):
        """每步高层输出被并入 upstream_outputs，传给下一个 Agent。"""

        async def fake_run(agent_id, agent_input):
            # 验证前序 Agent 的输出已在 upstream_outputs 中
            expected_prior = {
                "intent": [],
                "contraction": ["intent"],
                "planner": ["intent", "contraction"],
                "schema": ["intent", "contraction", "planner"],
            }[agent_id]
            assert sorted(agent_input.upstream_outputs.keys()) == sorted(
                expected_prior
            )
            return make_mock_result(agent_id)

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        assert set(result.outputs.keys()) == {
            "intent", "contraction", "planner", "schema"
        }

    @pytest.mark.asyncio
    async def test_bootstrap_records_agents_executed(
        self, mock_runner, project_id
    ):
        """agents_executed 列表正确记录所有成功执行的 Agent。"""

        async def fake_run(agent_id, agent_input):
            return make_mock_result(agent_id)

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        assert result.agents_executed == [
            "intent", "contraction", "planner", "schema"
        ]

    @pytest.mark.asyncio
    async def test_bootstrap_accumulates_files(
        self, mock_runner, project_id
    ):
        """产物文件（如有）被累积到 result.files。"""

        async def fake_run(agent_id, agent_input):
            files = (
                [{"path": "docs/x.md", "content": "x", "kind": "doc"}]
                if agent_id == "schema"
                else []
            )
            return make_mock_result(agent_id, files=files)

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        assert len(result.files) == 1

    @pytest.mark.asyncio
    async def test_agent_failure_continues(
        self, mock_runner, project_id
    ):
        """某个 Agent 抛异常时记录 warning，继续执行下一个。"""

        call_idx = 0

        async def fake_run(agent_id, agent_input):
            """模拟 AgentRunner.run，第 2 个 Agent 抛异常。"""
            nonlocal call_idx
            call_idx += 1
            # 第 2 个 Agent (contraction) 抛异常
            if call_idx == 2:
                raise RuntimeError("LLM 调用超时")
            return make_mock_result(agent_id)

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        # contraction 失败，其他 3 个成功
        assert len(result.agents_executed) == 3
        assert "intent" in result.agents_executed
        assert "contraction" not in result.agents_executed
        assert "planner" in result.agents_executed
        assert "schema" in result.agents_executed

        # 应该有 1 条 warning
        assert len(result.warnings) == 1
        assert "contraction" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_all_agents_fail(
        self, mock_runner, project_id
    ):
        """所有 Agent 都失败时返回空结果和 4 条 warnings。"""

        mock_runner.run = AsyncMock(
            side_effect=RuntimeError("全部失败")
        )

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message="创建 Todo 应用",
        )

        assert result.outputs == {}
        assert result.files == []
        assert result.agents_executed == []
        assert len(result.warnings) == 4
