"""
DAG 编排器集成测试模块。

测试 DAGParser、RunManager、DataPipe 的核心逻辑。
不依赖真实数据库或 Celery，通过 mock 实现无外部依赖的测试。
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from agents.configs.base import AgentConfig, ModelTier, RoleCategory
from agents.configs.registry import AgentRegistry
from pydantic import BaseModel
from worker_app.orchestrator.dag import DAGParseError, DAGParser, build_execution_plan
from worker_app.orchestrator.data_pipe import (
    CompletedStep,
    StepInput,
    assemble_step_input,
    parse_scope_draft,
)

# ============================================================
# 辅助 fixture
# ============================================================

# 最小 schema 占位类型，用于构造 AgentConfig
class _StubSchema(BaseModel):
    """测试用占位 Schema。"""
    pass


def _make_agent_config(
    agent_id: str,
    dependencies: list[str] | None = None,
) -> AgentConfig:
    """
    构造测试用 AgentConfig。

    - agent_id: agent 唯一标识
    - dependencies: 依赖的 agent_id 列表
    """
    return AgentConfig(
        agent_id=agent_id,
        name=f"Test {agent_id}",
        description=f"{agent_id} 测试配置",
        role_category=RoleCategory.INTENT_PLANNING,
        model_tier=ModelTier.REASONING,
        input_schema=_StubSchema,
        output_schema=_StubSchema,
        high_level_key="test_key",
        dependencies=dependencies or [],
    )


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置 AgentRegistry 单例。"""
    AgentRegistry.reset()
    yield
    AgentRegistry.reset()


def _build_standard_registry() -> AgentRegistry:
    """
    构建标准的 10 个 agent 注册表。

    DAG 结构：
      intent → contraction → planner → schema → backend  ┐
                                                → frontend ├→ qa → export
                                                → doc      │
                                                → diagram  ┘
    """
    registry = AgentRegistry.get_instance()
    configs = [
        _make_agent_config("intent", []),
        _make_agent_config("contraction", ["intent"]),
        _make_agent_config("planner", ["contraction"]),
        _make_agent_config("schema", ["planner"]),
        _make_agent_config("backend", ["schema"]),
        _make_agent_config("frontend", ["schema"]),
        _make_agent_config("doc", ["schema"]),
        _make_agent_config("diagram", ["schema"]),
        _make_agent_config("qa", ["backend", "frontend"]),
        _make_agent_config("export", ["qa"]),
    ]
    for cfg in configs:
        registry.register(cfg)
    return registry


# ============================================================
# DAGParser 测试
# ============================================================

class TestDAGParser:
    """DAG 解析器测试。"""

    def test_build_execution_layers(self):
        """验证标准 DAG 分层结果为 7 层。"""
        registry = _build_standard_registry()
        parser = DAGParser(registry)
        parser.build_graph()
        layers = parser.get_execution_layers()

        # 标准 DAG 应该有 7 层
        assert len(layers) == 7

        # 验证每一层的内容
        assert layers[0] == ["intent"]
        assert layers[1] == ["contraction"]
        assert layers[2] == ["planner"]
        assert layers[3] == ["schema"]
        # 第 5 层应包含 backend/frontend/doc/diagram（按字母序）
        assert sorted(layers[4]) == ["backend", "diagram", "doc", "frontend"]
        assert layers[5] == ["qa"]
        assert layers[6] == ["export"]

    def test_parallel_group(self):
        """验证 backend/frontend/doc/diagram 在同一层且可并行执行。"""
        registry = _build_standard_registry()
        parser = DAGParser(registry)
        parser.build_graph()
        layers = parser.get_execution_layers()

        # 找到包含 backend 的层
        parallel_layer = None
        for layer in layers:
            if "backend" in layer:
                parallel_layer = layer
                break

        assert parallel_layer is not None
        # 验证 4 个 agent 在同一层
        assert set(parallel_layer) == {"backend", "frontend", "doc", "diagram"}

    def test_subset_dag(self):
        """测试从指定 agent 开始的子 DAG（通过拓扑排序验证依赖顺序）。"""
        registry = _build_standard_registry()
        parser = DAGParser(registry)
        parser.build_graph()

        # 拓扑排序应该保证 planner 在 schema 之前
        topo = parser.topological_sort()
        planner_idx = topo.index("planner")
        schema_idx = topo.index("schema")
        assert planner_idx < schema_idx

        # intent 应在所有 agent 之前
        intent_idx = topo.index("intent")
        assert intent_idx == 0

        # export 应在最后
        export_idx = topo.index("export")
        assert export_idx == len(topo) - 1

    def test_cycle_detection(self):
        """如果有循环依赖，应该报错。"""
        registry = AgentRegistry.get_instance()

        # 构建一个循环依赖：A → B → C → A
        registry.register(_make_agent_config("agent_a", ["agent_c"]))
        registry.register(_make_agent_config("agent_b", ["agent_a"]))
        registry.register(_make_agent_config("agent_c", ["agent_b"]))

        parser = DAGParser(registry)
        parser.build_graph()

        # topological_sort 应检测到环并抛出异常
        with pytest.raises(DAGParseError, match="环"):
            parser.topological_sort()

    def test_cycle_detection_in_layers(self):
        """get_execution_layers 也应该检测循环依赖。"""
        registry = AgentRegistry.get_instance()

        # 构建循环：X ↔ Y
        registry.register(_make_agent_config("agent_x", ["agent_y"]))
        registry.register(_make_agent_config("agent_y", ["agent_x"]))

        parser = DAGParser(registry)
        parser.build_graph()

        with pytest.raises(DAGParseError, match="环"):
            parser.get_execution_layers()

    def test_build_execution_plan_convenience(self):
        """测试 build_execution_plan 便捷函数。"""
        registry = _build_standard_registry()
        layers = build_execution_plan(registry)
        assert len(layers) == 7
        assert layers[0] == ["intent"]

    def test_get_agent_dependencies(self):
        """测试获取 agent 的直接依赖。"""
        registry = _build_standard_registry()
        parser = DAGParser(registry)
        parser.build_graph()

        # qa 依赖 backend 和 frontend
        deps = parser.get_agent_dependencies("qa")
        assert set(deps) == {"backend", "frontend"}

        # intent 没有依赖
        deps = parser.get_agent_dependencies("intent")
        assert deps == []

    def test_get_agent_successors(self):
        """测试获取 agent 的后继。"""
        registry = _build_standard_registry()
        parser = DAGParser(registry)
        parser.build_graph()

        # schema 的后继应包含 backend, frontend, doc, diagram
        successors = parser.get_agent_successors("schema")
        assert set(successors) == {"backend", "frontend", "doc", "diagram"}

    def test_missing_dependency_raises(self):
        """依赖的 agent 不存在于注册表中应报错。"""
        registry = AgentRegistry.get_instance()
        registry.register(_make_agent_config("lonely", ["nonexistent"]))

        parser = DAGParser(registry)
        with pytest.raises(DAGParseError, match="nonexistent"):
            parser.build_graph()


# ============================================================
# RunManager 测试（mock 数据库）
# ============================================================

def _make_mock_session_factory():
    """
    构造 RunManager 测试用的 mock session 工厂。

    返回 (mock_factory, mock_session) 元组。
    mock_session 支持 async with session: + async with session.begin():
    的双层异步上下文管理器模式。
    """
    mock_session = MagicMock()

    # session 作为异步上下文管理器：async with factory() as session:
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    # session.begin() 返回异步上下文管理器
    mock_begin_cm = MagicMock()
    mock_begin_cm.__aenter__ = AsyncMock(return_value=None)
    mock_begin_cm.__aexit__ = AsyncMock(return_value=False)
    mock_session.begin.return_value = mock_begin_cm

    # session.execute 作为 coroutine
    mock_session.execute = AsyncMock()

    # session.add 作为普通方法（不是 async）
    mock_session.add = MagicMock()

    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory, mock_session


class TestRunManager:
    """RunManager 测试，通过 mock 数据库 session 验证逻辑。"""

    @pytest.mark.asyncio
    async def test_create_run(self):
        """创建 run 记录，验证返回的 UUID。"""
        from worker_app.orchestrator.run_manager import RunManager

        mock_factory, mock_session = _make_mock_session_factory()
        manager = RunManager(session_factory=mock_factory)

        project_id = uuid4()
        snapshot_id = uuid4()
        agent_ids = ["intent", "contraction", "planner"]

        result = await manager.create_run(
            project_id=project_id,
            snapshot_id=snapshot_id,
            agent_ids=agent_ids,
        )

        # 验证返回的是 UUID
        assert isinstance(result, UUID)
        # 验证 session.add 被调用了 4 次（1 个 job_run + 3 个 agent_run）
        assert mock_session.add.call_count == 4

    @pytest.mark.asyncio
    async def test_update_step_status(self):
        """更新步骤状态，验证 execute 被调用。"""
        from worker_app.orchestrator.run_manager import RunManager, RunStatus

        mock_factory, mock_session = _make_mock_session_factory()
        manager = RunManager(session_factory=mock_factory)

        run_id = uuid4()

        await manager.update_step_status(
            run_id=run_id,
            agent_id="intent",
            status=RunStatus.COMPLETED,
            output_payload={"result": "ok"},
        )

        # 验证 session.execute 被调用（UPDATE 语句）
        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_mark_run_completed(self):
        """完成状态转换，验证 execute 被调用。"""
        from worker_app.orchestrator.run_manager import RunManager

        mock_factory, mock_session = _make_mock_session_factory()
        manager = RunManager(session_factory=mock_factory)

        run_id = uuid4()

        await manager.mark_run_completed(
            run_id=run_id,
            output_payload={"total": 10},
        )

        # 验证 session.execute 被调用
        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_mark_run_started(self):
        """标记 run 为 running 状态。"""
        from worker_app.orchestrator.run_manager import RunManager

        mock_factory, mock_session = _make_mock_session_factory()
        manager = RunManager(session_factory=mock_factory)

        run_id = uuid4()
        await manager.mark_run_started(run_id=run_id)

        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_mark_run_failed(self):
        """标记 run 为 failed 状态。"""
        from worker_app.orchestrator.run_manager import RunManager

        mock_factory, mock_session = _make_mock_session_factory()
        manager = RunManager(session_factory=mock_factory)

        run_id = uuid4()
        await manager.mark_run_failed(
            run_id=run_id,
            error_message="测试错误",
        )

        assert mock_session.execute.call_count == 1


# ============================================================
# DataPipe 测试
# ============================================================

class TestDataPipe:
    """DataPipe 数据传递测试。"""

    def test_assemble_step_input(self):
        """验证输入组装正确。"""
        completed = [
            CompletedStep(
                agent_id="intent",
                status="completed",
                output_summary={"product_name": "TodoApp"},
            ),
            CompletedStep(
                agent_id="contraction",
                status="completed",
                output_summary={"mvp_scopes": 3},
            ),
        ]

        step_input = assemble_step_input(
            agent_id="planner",
            snapshot_id="snap-123",
            scope_draft={"name": "TodoApp"},
            completed_steps=completed,
        )

        assert step_input.agent_id == "planner"
        assert step_input.snapshot_id == "snap-123"
        assert step_input.scope_draft == {"name": "TodoApp"}
        assert "intent" in step_input.predecessor_outputs
        assert "contraction" in step_input.predecessor_outputs
        assert step_input.predecessor_outputs["intent"]["product_name"] == "TodoApp"

    def test_empty_predecessors(self):
        """无前置时 predecessor_outputs 应为空字典。"""
        step_input = assemble_step_input(
            agent_id="intent",
            snapshot_id="snap-001",
            scope_draft={"idea": "做一个 Todo 应用"},
        )

        assert step_input.agent_id == "intent"
        assert step_input.predecessor_outputs == {}

    def test_failed_steps_excluded(self):
        """失败的前置步骤不应出现在 predecessor_outputs 中。"""
        completed = [
            CompletedStep(
                agent_id="intent",
                status="completed",
                output_summary={"ok": True},
            ),
            CompletedStep(
                agent_id="contraction",
                status="failed",
                output_summary={"error": "失败了"},
            ),
        ]

        step_input = assemble_step_input(
            agent_id="planner",
            snapshot_id="snap-002",
            scope_draft={},
            completed_steps=completed,
        )

        # 只有 completed 状态的步骤被收集
        assert "intent" in step_input.predecessor_outputs
        assert "contraction" not in step_input.predecessor_outputs

    def test_step_input_serialization(self):
        """StepInput 序列化和反序列化。"""
        original = StepInput(
            agent_id="schema",
            snapshot_id="snap-003",
            scope_draft={"name": "test"},
            predecessor_outputs={"planner": {"steps": 7}},
        )

        json_str = original.to_json()
        restored = StepInput.from_json(json_str)

        assert restored.agent_id == original.agent_id
        assert restored.snapshot_id == original.snapshot_id
        assert restored.scope_draft == original.scope_draft
        assert restored.predecessor_outputs == original.predecessor_outputs

    def test_parse_scope_draft_valid(self):
        """解析有效的 scope_draft JSON。"""
        result = parse_scope_draft('{"name": "TestApp"}')
        assert result == {"name": "TestApp"}

    def test_parse_scope_draft_invalid(self):
        """解析无效 JSON 返回空字典。"""
        result = parse_scope_draft("not-json")
        assert result == {}

    def test_parse_scope_draft_none(self):
        """传入 None 返回空字典。"""
        result = parse_scope_draft(None)
        assert result == {}
