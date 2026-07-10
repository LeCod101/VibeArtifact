"""
M6 RepairLoop 集成测试。

使用 mock 替换 Agent 重跑和数据库操作，
验证修复回路的完整逻辑。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from runtime_tools.gates.models import GateResult, GateStepResult, GateSuiteResult
from runtime_tools.gates.repair_loop import RepairLoop, RepairResult

# ──────────────────────────────────────────────
# 辅助工具
# ──────────────────────────────────────────────

def make_passed_suite() -> GateSuiteResult:
    """构造全部通过的 GateSuiteResult。"""
    return GateSuiteResult(results=[
        GateResult(gate_name="frontend", passed=True, steps=[]),
        GateResult(gate_name="backend", passed=True, steps=[]),
        GateResult(gate_name="mermaid", passed=True, steps=[]),
    ])


def make_failed_suite(gate_name: str = "backend") -> GateSuiteResult:
    """构造指定 Gate 失败的 GateSuiteResult。"""
    results = []
    for name in ["frontend", "backend", "mermaid"]:
        passed = name != gate_name
        results.append(GateResult(
            gate_name=name,
            passed=passed,
            steps=[GateStepResult(
                step_name="check",
                passed=passed,
                issues=[] if passed else [f"{name} 检查失败"],
            )],
        ))
    return GateSuiteResult(results=results)


def make_files() -> list[dict]:
    """构造最小工作区文件列表（code + doc）。"""
    return [
        {
            "file_path": "backend/main.py",
            "content": "def hello(): pass",
            "file_kind": "code",
        },
        {
            "file_path": "README.md",
            "content": "# Project",
            "file_kind": "doc",
        },
    ]


# ──────────────────────────────────────────────
# RepairLoop 测试
# ──────────────────────────────────────────────

class TestRepairLoop:
    """RepairLoop 修复回路测试组。"""

    @pytest.fixture
    def run_id(self):
        """生成测试用 run_id。"""
        return uuid4()

    @pytest.fixture
    def mock_manager(self):
        """构造 mock RunManager。"""
        manager = MagicMock()
        manager.mark_run_needs_attention = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_gate_all_pass_no_repair(self, run_id, mock_manager):
        """Gate 全部通过时不触发修复，直接返回 passed=True。"""
        loop = RepairLoop(manager=mock_manager, run_id=run_id)

        with patch.object(
            loop._gate_runner, "run_all", return_value=make_passed_suite()
        ), patch.object(
            loop, "load_workspace_files", new_callable=AsyncMock, return_value=make_files()
        ):
            result = await loop.run_gates_and_repair(
                scope_draft_json="{}",
            )

        assert result.passed is True
        assert result.repaired is False
        assert result.retry_count == 0
        assert result.needs_attention is False
        mock_manager.mark_run_needs_attention.assert_not_called()

    @pytest.mark.asyncio
    async def test_gate_fail_then_repair_success(self, run_id, mock_manager):
        """Gate 失败 → 重跑后 Gate 通过 → passed=True，repaired=True。"""
        loop = RepairLoop(manager=mock_manager, run_id=run_id)

        # 第一轮失败，第二轮通过
        suite_call_count = 0

        def gate_side_effect(files, project_name=""):
            nonlocal suite_call_count
            suite_call_count += 1
            if suite_call_count == 1:
                return make_failed_suite("backend")
            return make_passed_suite()

        with patch.object(
            loop._gate_runner, "run_all", side_effect=gate_side_effect
        ), patch.object(
            loop, "load_workspace_files", new_callable=AsyncMock, return_value=make_files()
        ), patch(
            "runtime_tools.gates.repair_loop.RepairLoop._retry_agents",
            new_callable=AsyncMock,
            return_value=make_files(),
        ):
            result = await loop.run_gates_and_repair(
                scope_draft_json="{}",
            )

        assert result.passed is True
        assert result.repaired is True
        assert result.retry_count == 1
        assert result.needs_attention is False

    @pytest.mark.asyncio
    async def test_gate_fail_repair_fail_needs_attention(
        self, run_id, mock_manager
    ):
        """Gate 失败 → 重跑后 Gate 仍失败 → needs_attention=True。"""
        loop = RepairLoop(manager=mock_manager, run_id=run_id)

        with patch.object(
            loop._gate_runner, "run_all", return_value=make_failed_suite("backend")
        ), patch.object(
            loop, "load_workspace_files", new_callable=AsyncMock, return_value=make_files()
        ), patch(
            "runtime_tools.gates.repair_loop.RepairLoop._retry_agents",
            new_callable=AsyncMock,
            return_value=make_files(),
        ), patch(
            "runtime_tools.gates.repair_loop.RepairLoop._mark_needs_attention",
            new_callable=AsyncMock,
        ) as mock_mark:
            result = await loop.run_gates_and_repair(
                scope_draft_json="{}",
            )

        assert result.passed is False
        assert result.needs_attention is True
        assert result.retry_count == 1
        mock_mark.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_agent_mapping_needs_attention(self, run_id, mock_manager):
        """Gate 失败但无法映射到 Agent 时，直接 needs_attention。"""
        loop = RepairLoop(manager=mock_manager, run_id=run_id)

        # 构造一个无法映射的 Gate 失败（用未知 gate 名称）
        unknown_suite = GateSuiteResult(results=[
            GateResult(
                gate_name="unknown_gate",
                passed=False,
                steps=[GateStepResult(step_name="x", passed=False, issues=["err"])],
            )
        ])

        with patch.object(
            loop._gate_runner, "run_all", return_value=unknown_suite
        ), patch.object(
            loop, "load_workspace_files", new_callable=AsyncMock, return_value=make_files()
        ), patch(
            "runtime_tools.gates.repair_loop.RepairLoop._mark_needs_attention",
            new_callable=AsyncMock,
        ) as mock_mark:
            result = await loop.run_gates_and_repair(
                scope_draft_json="{}",
            )

        assert result.passed is False
        assert result.needs_attention is True
        assert result.retry_count == 0
        mock_mark.assert_called_once()

    def test_repair_result_attributes(self, run_id, mock_manager):
        """RepairResult 属性访问正确。"""
        suite = make_passed_suite()
        result = RepairResult(
            passed=True,
            repaired=False,
            gate_suite=suite,
            retry_count=0,
        )
        assert result.passed is True
        assert result.needs_attention is False
        assert result.classification is None
