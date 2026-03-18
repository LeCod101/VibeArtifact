"""
M7 ColdStartBootstrap 单元测试。

覆盖：
- 按顺序执行 4 个 Agent（intent/contraction/planner/schema）
- 每步 operations 被 apply 到下一步输入
- 最终 ir_nodes 包含所有 Agent 产出的节点
- agents_executed 列表正确记录
- operations_applied 计数正确
- 单个 Agent 失败时继续执行下一个
- 所有 Agent 都失败时返回空结果 + 4 条 warnings
- apply_operations 抛 ApplyError 时记录 warning 并继续
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from agents.analysis.cold_start import ColdStartBootstrap
from agents.executors.runner import AgentRunResult
from agents.schemas.base import AgentOutput
from ir_core.operations.apply import ApplyError
from ir_core.schema.data import IRNodeData
from ir_core.validators.result import ValidationResult

# ============================================================
# 测试辅助函数
# ============================================================


def make_mock_result(operations=None, warnings=None):
    """
    构造模拟的 AgentRunResult。

    参数：
        operations: 操作列表（默认空）
        warnings: 警告列表（默认空）

    返回：
        AgentRunResult 实例
    """
    output = AgentOutput(
        reasoning="test reasoning",
        confidence=0.9,
        warnings=warnings or [],
    )
    return AgentRunResult(
        agent_id="test",
        output=output,
        operations=operations or [],
        warnings=warnings or [],
        meta=None,
    )


def make_fake_operations(count: int = 2) -> list[dict]:
    """
    构造假操作列表（用于计数验证，不用于实际 apply）。

    参数：
        count: 操作数量

    返回：
        操作字典列表
    """
    return [
        {
            "operation_type": "create_node",
            "node_type": "scope",
            "label": f"node_{i}",
        }
        for i in range(count)
    ]


def make_test_nodes(count: int = 1) -> list[IRNodeData]:
    """
    构造测试用节点列表。

    参数：
        count: 节点数量

    返回：
        IRNodeData 列表
    """
    return [
        IRNodeData(
            id=uuid4(),
            node_type="scope",
            label=f"node_{i}",
            props={},
        )
        for i in range(count)
    ]


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
    def project_ids(self):
        """创建测试用项目 ID 和快照 ID。"""
        return uuid4(), uuid4()

    @pytest.mark.asyncio
    async def test_bootstrap_executes_four_agents(
        self, mock_runner, project_ids
    ):
        """验证冷启动按顺序执行 intent/contraction/planner/schema 四个 Agent。"""
        project_id, snapshot_id = project_ids

        # 所有 Agent 返回无操作的结果
        mock_runner.run = AsyncMock(return_value=make_mock_result())

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        await bootstrap.bootstrap(
            project_id=project_id,
            snapshot_id=snapshot_id,
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
    async def test_bootstrap_applies_operations_sequentially(
        self, mock_runner, project_ids
    ):
        """每步 operations 被 apply_operations 应用到下一步输入。"""
        project_id, snapshot_id = project_ids

        ops_per_agent = [
            make_fake_operations(2),
            make_fake_operations(1),
            make_fake_operations(3),
            make_fake_operations(1),
        ]

        call_count = 0

        async def fake_run(agent_id, agent_input):
            """模拟 AgentRunner.run，每次返回预设的操作数。"""
            nonlocal call_count
            result = make_mock_result(operations=ops_per_agent[call_count])
            call_count += 1
            return result

        mock_runner.run = AsyncMock(side_effect=fake_run)

        # mock apply_operations 让它返回逐渐增多的节点
        with patch(
            "agents.analysis.cold_start.apply_operations"
        ) as mock_apply:
            mock_apply.side_effect = [
                (make_test_nodes(2), []),
                (make_test_nodes(3), []),
                (make_test_nodes(6), []),
                (make_test_nodes(7), []),
            ]

            bootstrap = ColdStartBootstrap(runner=mock_runner)
            await bootstrap.bootstrap(
                project_id=project_id,
                snapshot_id=snapshot_id,
                user_message="创建 Todo 应用",
            )

            # apply_operations 被调用了 4 次（每个 Agent 各一次）
            assert mock_apply.call_count == 4

    @pytest.mark.asyncio
    async def test_bootstrap_returns_accumulated_nodes(
        self, mock_runner, project_ids
    ):
        """最终 ir_nodes 包含所有 Agent 产出的节点。"""
        project_id, snapshot_id = project_ids

        final_nodes = make_test_nodes(5)

        # 前 3 个 Agent 无操作，最后一个有操作
        call_idx = 0

        async def fake_run(agent_id, agent_input):
            """模拟 AgentRunner.run，仅最后一个 Agent 返回操作。"""
            nonlocal call_idx
            if call_idx == 3:
                result = make_mock_result(operations=make_fake_operations(1))
            else:
                result = make_mock_result()
            call_idx += 1
            return result

        mock_runner.run = AsyncMock(side_effect=fake_run)

        with patch(
            "agents.analysis.cold_start.apply_operations"
        ) as mock_apply:
            mock_apply.return_value = (final_nodes, [])

            bootstrap = ColdStartBootstrap(runner=mock_runner)
            result = await bootstrap.bootstrap(
                project_id=project_id,
                snapshot_id=snapshot_id,
                user_message="创建 Todo 应用",
            )

            assert len(result.ir_nodes) == 5

    @pytest.mark.asyncio
    async def test_bootstrap_records_agents_executed(
        self, mock_runner, project_ids
    ):
        """agents_executed 列表正确记录所有成功执行的 Agent。"""
        project_id, snapshot_id = project_ids

        mock_runner.run = AsyncMock(return_value=make_mock_result())

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            snapshot_id=snapshot_id,
            user_message="创建 Todo 应用",
        )

        assert result.agents_executed == [
            "intent", "contraction", "planner", "schema"
        ]

    @pytest.mark.asyncio
    async def test_bootstrap_counts_operations(
        self, mock_runner, project_ids
    ):
        """operations_applied 正确计数所有 Agent 产生的操作。"""
        project_id, snapshot_id = project_ids

        # 4 个 Agent 分别产生 2, 1, 3, 1 = 7 个操作
        ops_counts = [2, 1, 3, 1]
        call_idx = 0

        async def fake_run(agent_id, agent_input):
            """模拟 AgentRunner.run，按预设数量返回操作。"""
            nonlocal call_idx
            result = make_mock_result(
                operations=make_fake_operations(ops_counts[call_idx])
            )
            call_idx += 1
            return result

        mock_runner.run = AsyncMock(side_effect=fake_run)

        with patch(
            "agents.analysis.cold_start.apply_operations"
        ) as mock_apply:
            mock_apply.return_value = ([], [])

            bootstrap = ColdStartBootstrap(runner=mock_runner)
            result = await bootstrap.bootstrap(
                project_id=project_id,
                snapshot_id=snapshot_id,
                user_message="创建 Todo 应用",
            )

            assert result.operations_applied == 7

    @pytest.mark.asyncio
    async def test_agent_failure_continues(
        self, mock_runner, project_ids
    ):
        """某个 Agent 抛异常时记录 warning，继续执行下一个。"""
        project_id, snapshot_id = project_ids

        call_idx = 0

        async def fake_run(agent_id, agent_input):
            """模拟 AgentRunner.run，第 2 个 Agent 抛异常。"""
            nonlocal call_idx
            call_idx += 1
            # 第 2 个 Agent (contraction) 抛异常
            if call_idx == 2:
                raise RuntimeError("LLM 调用超时")
            return make_mock_result()

        mock_runner.run = AsyncMock(side_effect=fake_run)

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            snapshot_id=snapshot_id,
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
        self, mock_runner, project_ids
    ):
        """所有 Agent 都失败时返回空结果和 4 条 warnings。"""
        project_id, snapshot_id = project_ids

        mock_runner.run = AsyncMock(
            side_effect=RuntimeError("全部失败")
        )

        bootstrap = ColdStartBootstrap(runner=mock_runner)
        result = await bootstrap.bootstrap(
            project_id=project_id,
            snapshot_id=snapshot_id,
            user_message="创建 Todo 应用",
        )

        assert result.ir_nodes == []
        assert result.ir_edges == []
        assert result.agents_executed == []
        assert result.operations_applied == 0
        assert len(result.warnings) == 4

    @pytest.mark.asyncio
    async def test_apply_error_recorded_as_warning(
        self, mock_runner, project_ids
    ):
        """apply_operations 抛 ApplyError 时记录 warning 并继续执行。"""
        project_id, snapshot_id = project_ids

        # 所有 Agent 都返回有操作的结果
        mock_runner.run = AsyncMock(
            return_value=make_mock_result(
                operations=make_fake_operations(1)
            )
        )

        with patch(
            "agents.analysis.cold_start.apply_operations"
        ) as mock_apply:
            # 第一次 apply 抛 ApplyError，后续正常
            validation_result = ValidationResult.fail(["校验失败"])
            mock_apply.side_effect = [
                ApplyError("节点校验失败", validation_result),
                (make_test_nodes(1), []),
                (make_test_nodes(2), []),
                (make_test_nodes(3), []),
            ]

            bootstrap = ColdStartBootstrap(runner=mock_runner)
            result = await bootstrap.bootstrap(
                project_id=project_id,
                snapshot_id=snapshot_id,
                user_message="创建 Todo 应用",
            )

            # 第一个 Agent (intent) 的 apply 失败，记录 warning
            apply_warnings = [
                w for w in result.warnings if "应用失败" in w
            ]
            assert len(apply_warnings) == 1
            assert "intent" in apply_warnings[0]

            # intent 的 apply 失败导致它不计入 agents_executed
            # 其余 3 个 Agent 正常执行
            assert len(result.agents_executed) == 3
            assert "intent" not in result.agents_executed
