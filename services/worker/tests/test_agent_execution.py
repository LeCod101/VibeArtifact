"""
M10 Agent 真实执行闭环集成测试。

测试覆盖：
1. AgentRunner 真实调用（mock LLM）
2. 快照写入和链路
3. IR 操作应用
4. JSON 修复容错
5. Agent 失败不阻断
6. 产物收集和 ZIP 打包
7. 完整 DAG mock 执行

注意：部分测试需要 celery 依赖（worker_app 模块），
这些测试在无 celery 环境下会被跳过。
"""

from __future__ import annotations

import importlib
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ──────────────────────────────────────────────
# 检测 celery 是否可用
# ──────────────────────────────────────────────

try:
    import celery  # noqa: F401
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False

# celery 不可用时跳过需要 worker_app 的测试
requires_celery = pytest.mark.skipif(
    not HAS_CELERY,
    reason="需要 celery 依赖才能导入 worker_app 模块",
)


# ──────────────────────────────────────────────
# 测试数据
# ──────────────────────────────────────────────

SAMPLE_PROJECT_ID = uuid4()
SAMPLE_SNAPSHOT_ID = uuid4()


# ──────────────────────────────────────────────
# 测试 5：JSON 解析错误容错（无外部依赖）
# ──────────────────────────────────────────────


class TestJsonParseErrorHandled:
    """验证 LLM 输出非 JSON 时的容错。"""

    def test_json_repair_markdown_block(self):
        """修复 Markdown 代码块包裹的 JSON。"""
        from agents.executors.json_repair import repair_llm_json

        raw = '```json\n{"key": "value"}\n```'
        result = repair_llm_json(raw)
        assert json.loads(result) == {"key": "value"}

    def test_json_repair_extra_text(self):
        """修复前后有多余文本的 JSON。"""
        from agents.executors.json_repair import repair_llm_json

        raw = 'Sure, here is the JSON:\n{"key": "value"}\nHope this helps!'
        result = repair_llm_json(raw)
        assert json.loads(result) == {"key": "value"}

    def test_json_repair_trailing_comma(self):
        """修复尾部多余逗号。"""
        from agents.executors.json_repair import repair_llm_json

        raw = '{"items": [1, 2, 3,]}'
        result = repair_llm_json(raw)
        assert json.loads(result) == {"items": [1, 2, 3]}

    def test_json_repair_valid_passthrough(self):
        """合法 JSON 直接通过。"""
        from agents.executors.json_repair import repair_llm_json

        raw = '{"key": "value"}'
        result = repair_llm_json(raw)
        assert result == raw

    def test_json_repair_unfixable_raises(self):
        """无法修复的文本抛出 JSONDecodeError。"""
        from agents.executors.json_repair import repair_llm_json

        with pytest.raises(json.JSONDecodeError):
            repair_llm_json("this is not json at all")

    def test_json_repair_nested_code_block(self):
        """修复嵌套 markdown 代码块。"""
        from agents.executors.json_repair import repair_llm_json

        raw = '```\n{"nested": {"a": 1}}\n```'
        result = repair_llm_json(raw)
        assert json.loads(result) == {"nested": {"a": 1}}

    def test_json_repair_array(self):
        """修复数组类型 JSON。"""
        from agents.executors.json_repair import repair_llm_json

        raw = 'Here is the result:\n[1, 2, 3]\nDone.'
        result = repair_llm_json(raw)
        assert json.loads(result) == [1, 2, 3]


# ──────────────────────────────────────────────
# 测试 7：产物收集（无外部依赖）
# ──────────────────────────────────────────────


class TestExportCollectsArtifacts:
    """验证 ArtifactCollector 能从 IR 节点收集产物。"""

    def test_collector_extracts_code_nodes(self):
        """code 类型节点被正确收集。"""
        from runtime_tools.exporters.collector import ArtifactCollector

        nodes = [
            {
                "node_type": "code",
                "label": "main.py",
                "props": {
                    "path": "backend/main.py",
                    "content": "print('hello')",
                    "language": "python",
                },
            },
            {
                "node_type": "entity",
                "label": "User",
                "props": {"name": "User"},
            },
        ]

        collector = ArtifactCollector()
        files = collector.collect(nodes)

        # 只有 code 节点被收集
        assert len(files) == 1
        assert files[0].export_path == "backend/main.py"
        assert files[0].content == "print('hello')"

    def test_collector_extracts_doc_nodes(self):
        """doc 类型节点被正确收集。"""
        from runtime_tools.exporters.collector import ArtifactCollector

        nodes = [
            {
                "node_type": "doc",
                "label": "README",
                "props": {
                    "path": "README.md",
                    "content": "# Hello",
                    "format": "markdown",
                },
            },
        ]

        collector = ArtifactCollector()
        files = collector.collect(nodes)

        assert len(files) == 1
        assert files[0].export_path == "README.md"


# ──────────────────────────────────────────────
# 测试 8：ZIP 包含实际文件（无外部依赖）
# ──────────────────────────────────────────────


class TestZipHasFiles:
    """验证 ZIP 包含实际文件内容。"""

    def test_zip_contains_files(self):
        """ZipPacker 生成的 ZIP 包含指定文件。"""
        import io
        import zipfile

        from runtime_tools.exporters.collector import FileEntry
        from runtime_tools.exporters.zip_packer import ZipPacker

        files = [
            FileEntry(
                export_path="src/main.py",
                content="print('hello world')",
            ),
            FileEntry(
                export_path="README.md",
                content="# Test Project",
            ),
        ]

        packer = ZipPacker(project_name="test_project", files=files)
        zip_bytes = packer.pack_to_bytes()

        # 验证 ZIP 内容
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            assert "test_project/src/main.py" in names
            assert "test_project/README.md" in names

            # 验证文件内容
            main_content = zf.read("test_project/src/main.py").decode("utf-8")
            assert main_content == "print('hello world')"

    def test_zip_empty_collection(self):
        """空文件列表生成空 ZIP。"""
        import io
        import zipfile

        from runtime_tools.exporters.zip_packer import ZipPacker

        packer = ZipPacker(project_name="empty", files=[])
        zip_bytes = packer.pack_to_bytes()

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert len(zf.namelist()) == 0


# ──────────────────────────────────────────────
# 测试 3：IR 操作正确应用（无外部依赖）
# ──────────────────────────────────────────────


class TestIROperationsApplied:
    """验证 apply_operations 正确应用 IR 操作。"""

    def test_create_node_operation(self):
        """create_node 操作正确添加节点。"""
        from ir_core.operations.apply import apply_operations

        node_id = str(uuid4())
        # 使用 scope 节点类型，props 需要符合 ScopeProps 验证
        ops = [
            {
                "operation_type": "create_node",
                "node_id": node_id,
                "node_type": "scope",
                "label": "待办事项管理",
                "props": {
                    "name": "待办事项管理",
                    "description": "创建、编辑、删除待办事项",
                    "priority": "high",
                    "tags": ["crud"],
                },
            }
        ]

        new_nodes, new_edges = apply_operations([], [], ops)
        assert len(new_nodes) == 1
        assert new_nodes[0].label == "待办事项管理"
        assert str(new_nodes[0].id) == node_id

    def test_create_and_link_nodes(self):
        """创建节点并用边连接。"""
        from ir_core.operations.apply import apply_operations

        node_a = str(uuid4())
        node_b = str(uuid4())
        edge_id = str(uuid4())

        ops = [
            {
                "operation_type": "create_node",
                "node_id": node_a,
                "node_type": "scope",
                "label": "用户管理",
                "props": {
                    "name": "用户管理",
                    "description": "用户注册、登录",
                    "priority": "high",
                    "tags": ["auth"],
                },
            },
            {
                "operation_type": "create_node",
                "node_id": node_b,
                "node_type": "scope",
                "label": "内容管理",
                "props": {
                    "name": "内容管理",
                    "description": "发布、编辑文章",
                    "priority": "medium",
                    "tags": ["crud"],
                },
            },
            {
                "operation_type": "create_edge",
                "edge_id": edge_id,
                "edge_type": "references",
                "source_node_id": node_b,
                "target_node_id": node_a,
                "props": {},
            },
        ]

        new_nodes, new_edges = apply_operations([], [], ops)
        assert len(new_nodes) == 2
        assert len(new_edges) == 1
        assert str(new_edges[0].source_node_id) == node_b
        assert str(new_edges[0].target_node_id) == node_a


# ──────────────────────────────────────────────
# 以下测试需要 celery 依赖
# ──────────────────────────────────────────────


@requires_celery
class TestAgentRunnerCalled:
    """验证 _run_agent 调用了真实的 AgentRunner.run()。"""

    @pytest.mark.asyncio
    async def test_agent_runner_called(self):
        """验证 _run_agent 函数创建 AgentRunner 并调用 run()。"""
        from agents.executors.runner import AgentRunResult
        from agents.schemas.base import AgentRunMeta

        # 构造模拟的 AgentRunResult
        mock_result = MagicMock(spec=AgentRunResult)
        mock_result.operations = [
            {
                "operation_type": "create_node",
                "node_id": str(uuid4()),
                "node_type": "entity",
                "label": "Todo",
                "props": {"name": "Todo"},
            }
        ]
        mock_result.warnings = []
        mock_result.meta = AgentRunMeta(
            model="mock-model",
            provider="mock",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.001,
            latency_ms=500.0,
        )

        # Mock 所有外部依赖
        mock_writer = AsyncMock()
        mock_writer.load_snapshot.return_value = ([], [])
        mock_writer.write_snapshot.return_value = uuid4()

        mock_runner = AsyncMock()
        mock_runner.run.return_value = mock_result

        with patch(
            "worker_app.tasks.agent_task.SnapshotWriter",
            return_value=mock_writer,
        ), patch(
            "worker_app.tasks.agent_task.AgentRunner",
            return_value=mock_runner,
        ), patch(
            "worker_app.tasks.agent_task.LiteLLMProvider",
        ), patch(
            "worker_app.tasks.agent_task.register_all_agents",
        ):
            from worker_app.tasks.agent_task import _run_agent

            result = await _run_agent(
                agent_id="schema",
                project_id=SAMPLE_PROJECT_ID,
                snapshot_id=SAMPLE_SNAPSHOT_ID,
                task_description="{}",
            )

        # 验证 AgentRunner.run 被调用
        mock_runner.run.assert_called_once()
        assert result["new_snapshot_id"] is not None
        assert result["output_summary"]["operations_count"] == 1


@requires_celery
class TestSnapshotWritten:
    """验证 Agent 执行后新快照写入 DB。"""

    @pytest.mark.asyncio
    async def test_snapshot_written_after_agent(self):
        """Agent 执行后 SnapshotWriter.write_snapshot 被调用。"""
        from agents.executors.runner import AgentRunResult

        mock_result = MagicMock(spec=AgentRunResult)
        mock_result.operations = []
        mock_result.warnings = []
        mock_result.meta = None

        new_snap_id = uuid4()
        mock_writer = AsyncMock()
        mock_writer.load_snapshot.return_value = ([], [])
        mock_writer.write_snapshot.return_value = new_snap_id

        mock_runner = AsyncMock()
        mock_runner.run.return_value = mock_result

        with patch(
            "worker_app.tasks.agent_task.SnapshotWriter",
            return_value=mock_writer,
        ), patch(
            "worker_app.tasks.agent_task.AgentRunner",
            return_value=mock_runner,
        ), patch(
            "worker_app.tasks.agent_task.LiteLLMProvider",
        ), patch(
            "worker_app.tasks.agent_task.register_all_agents",
        ):
            from worker_app.tasks.agent_task import _run_agent

            result = await _run_agent(
                agent_id="intent",
                project_id=SAMPLE_PROJECT_ID,
                snapshot_id=SAMPLE_SNAPSHOT_ID,
                task_description="{}",
            )

        # 验证 write_snapshot 被调用且参数正确
        mock_writer.write_snapshot.assert_called_once()
        call_kwargs = mock_writer.write_snapshot.call_args
        assert call_kwargs.kwargs["project_id"] == SAMPLE_PROJECT_ID
        assert call_kwargs.kwargs["parent_snapshot_id"] == SAMPLE_SNAPSHOT_ID
        assert result["new_snapshot_id"] == new_snap_id


@requires_celery
class TestSnapshotChain:
    """验证多层执行后快照链正确。"""

    @pytest.mark.asyncio
    async def test_snapshot_chain_through_layers(self):
        """_execute_layer 返回更新后的 snapshot_id。"""
        snap1 = uuid4()
        snap2 = uuid4()

        with patch(
            "worker_app.tasks.orchestrate._execute_agent_step_async",
        ) as mock_exec:
            mock_exec.side_effect = [
                {
                    "agent_id": "layer1_agent",
                    "status": "completed",
                    "snapshot_id": str(snap1),
                    "output_summary": {},
                },
                {
                    "agent_id": "layer2_agent",
                    "status": "completed",
                    "snapshot_id": str(snap2),
                    "output_summary": {},
                },
            ]

            from worker_app.tasks.orchestrate import _execute_layer

            # 第一层
            results1, new_snap1 = await _execute_layer(
                run_id=str(uuid4()),
                layer=["layer1_agent"],
                snapshot_id=str(SAMPLE_SNAPSHOT_ID),
                scope_draft_json="{}",
            )
            assert new_snap1 == str(snap1)

            # 第二层使用第一层的输出快照
            results2, new_snap2 = await _execute_layer(
                run_id=str(uuid4()),
                layer=["layer2_agent"],
                snapshot_id=new_snap1,
                scope_draft_json="{}",
            )
            assert new_snap2 == str(snap2)

            # 验证第二层使用了第一层的快照
            second_call = mock_exec.call_args_list[1]
            assert second_call.kwargs["snapshot_id"] == str(snap1)


@requires_celery
class TestAgentFailureDoesntBlock:
    """验证单 Agent 失败不阻断整个层。"""

    @pytest.mark.asyncio
    async def test_parallel_layer_partial_failure(self):
        """并行层中一个 Agent 失败，其他仍然成功。"""
        with patch(
            "worker_app.tasks.orchestrate._execute_agent_step_async",
        ) as mock_exec:
            mock_exec.side_effect = [
                {
                    "agent_id": "backend",
                    "status": "completed",
                    "snapshot_id": str(uuid4()),
                    "output_summary": {},
                },
                Exception("LLM 调用失败"),
            ]

            from worker_app.tasks.orchestrate import _execute_layer

            results, _ = await _execute_layer(
                run_id=str(uuid4()),
                layer=["backend", "frontend"],
                snapshot_id=str(SAMPLE_SNAPSHOT_ID),
                scope_draft_json="{}",
            )

        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "failed"
        assert "LLM 调用失败" in results[1]["error"]


@requires_celery
class TestCollectAndPackArtifacts:
    """验证 _collect_and_pack_artifacts 端到端。"""

    @pytest.mark.asyncio
    async def test_collect_and_pack_with_nodes(self, tmp_path):
        """有产物节点时生成 ZIP。"""
        from ir_core.schema.data import IRNodeData

        code_node = IRNodeData(
            id=uuid4(),
            node_type="code",
            label="app.py",
            props={
                "path": "app.py",
                "content": "from fastapi import FastAPI",
                "language": "python",
            },
        )

        mock_writer = AsyncMock()
        mock_writer.load_snapshot.return_value = ([code_node], [])

        with patch(
            "worker_app.tasks.orchestrate.SnapshotWriter",
            return_value=mock_writer,
        ), patch.dict(
            "os.environ",
            {"ARTIFACT_OUTPUT_DIR": str(tmp_path)},
        ):
            from worker_app.tasks.orchestrate import _collect_and_pack_artifacts

            result = await _collect_and_pack_artifacts(
                snapshot_id=str(SAMPLE_SNAPSHOT_ID),
                project_name="test_proj",
            )

        assert result is not None
        assert result.endswith(".zip")

    @pytest.mark.asyncio
    async def test_collect_and_pack_empty(self):
        """无产物节点时返回 None。"""
        from ir_core.schema.data import IRNodeData

        entity_node = IRNodeData(
            id=uuid4(),
            node_type="entity",
            label="User",
            props={"name": "User"},
        )

        mock_writer = AsyncMock()
        mock_writer.load_snapshot.return_value = ([entity_node], [])

        with patch(
            "worker_app.tasks.orchestrate.SnapshotWriter",
            return_value=mock_writer,
        ):
            from worker_app.tasks.orchestrate import _collect_and_pack_artifacts

            result = await _collect_and_pack_artifacts(
                snapshot_id=str(SAMPLE_SNAPSHOT_ID),
                project_name="empty_proj",
            )

        assert result is None


@requires_celery
class TestFullDagMock:
    """验证完整 DAG 用 Mock 跑通。"""

    @pytest.mark.asyncio
    async def test_full_dag_layers_propagate_snapshot(self):
        """完整 DAG 多层执行，snapshot_id 在层间正确传递。"""
        snapshots = [uuid4() for _ in range(4)]
        call_count = 0

        async def mock_step(run_id, agent_id, snapshot_id, step_input_json):
            """模拟 agent 步骤执行，每次返回新快照。"""
            nonlocal call_count
            idx = min(call_count, len(snapshots) - 1)
            call_count += 1
            return {
                "agent_id": agent_id,
                "status": "completed",
                "snapshot_id": str(snapshots[idx]),
                "output_summary": {"agent_id": agent_id},
            }

        with patch(
            "worker_app.tasks.orchestrate._execute_agent_step_async",
            side_effect=mock_step,
        ):
            from worker_app.tasks.orchestrate import _execute_layer

            # 模拟 4 层 DAG
            layers = [["intent"], ["contraction"], ["planner"], ["schema"]]
            current_snap = str(SAMPLE_SNAPSHOT_ID)

            for i, layer in enumerate(layers):
                results, new_snap = await _execute_layer(
                    run_id=str(uuid4()),
                    layer=layer,
                    snapshot_id=current_snap,
                    scope_draft_json="{}",
                )
                assert results[0]["status"] == "completed"
                assert new_snap is not None
                current_snap = new_snap

            # 最终快照应该是最后一个
            assert current_snap == str(snapshots[3])
            assert call_count == 4
