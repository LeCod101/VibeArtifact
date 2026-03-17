"""
M6 Gate 集成测试。

测试三个 Gate、问题分类器、GateRunner 的核心逻辑。
使用纯内存文件集合，不依赖外部工具链（降级路径）。
"""

from __future__ import annotations

import pytest

from runtime_tools.exporters.collector import FileEntry
from runtime_tools.gates.backend_gate import BackendGate
from runtime_tools.gates.classifier import IssueClassifier
from runtime_tools.gates.frontend_gate import FrontendGate
from runtime_tools.gates.mermaid_gate import MermaidGate
from runtime_tools.gates.models import GateResult, GateSuiteResult, GateStepResult
from runtime_tools.gates.runner import GateRunner


# ──────────────────────────────────────────────
# 测试数据
# ──────────────────────────────────────────────

def make_frontend_files(valid: bool = True) -> list[FileEntry]:
    """
    生成前端测试文件集合。

    - valid=True：括号平衡的 TSX 文件
    - valid=False：括号不平衡的 TSX 文件（触发静态扫描失败）
    """
    if valid:
        content = "export default function App() { return <div>Hello</div>; }"
    else:
        # 大括号不平衡，差值超过 3
        content = "export default function App() { { { { { return <div>Hello</div>; "
    return [
        FileEntry(export_path="frontend/app/page.tsx", content=content),
    ]


def make_backend_files(valid: bool = True) -> list[FileEntry]:
    """
    生成后端测试文件集合。

    - valid=True：合法 Python 文件
    - valid=False：语法错误 Python 文件（触发 compileall 失败）
    """
    if valid:
        content = "def hello():\n    return 'world'\n"
    else:
        content = "def hello(\n    return 'world'\n"  # 语法错误：括号未闭合
    return [
        FileEntry(export_path="backend/main.py", content=content),
    ]


def make_mermaid_files(valid: bool = True) -> list[FileEntry]:
    """
    生成 Mermaid 测试文件集合。

    - valid=True：合法 Mermaid 图表
    - valid=False：非法图表类型
    """
    if valid:
        content = "# ER 图\n\n```mermaid\nerDiagram\n    User ||--o{ Project : owns\n```\n"
    else:
        content = "# 非法图\n\n```mermaid\ninvalidType\n    A --> B\n```\n"
    return [
        FileEntry(export_path="docs/diagrams/er.md", content=content),
    ]


# ──────────────────────────────────────────────
# FrontendGate 测试
# ──────────────────────────────────────────────

class TestFrontendGate:
    """前端 Gate 测试组。"""

    def test_no_frontend_files_skipped(self):
        """无前端文件时应跳过，返回 passed=True。"""
        gate = FrontendGate()
        result = gate.run([], project_name="test")
        assert result.passed is True
        assert result.skipped is True
        assert result.gate_name == "frontend"

    def test_valid_tsx_passes(self):
        """括号平衡的 TSX 文件应通过静态扫描。"""
        gate = FrontendGate()
        result = gate.run(make_frontend_files(valid=True), project_name="test")
        assert result.gate_name == "frontend"
        # 静态扫描降级路径：无 package.json 时运行 static_scan
        # 括号平衡，应通过
        assert result.passed is True

    def test_unbalanced_braces_fails(self):
        """括号严重不平衡的 TSX 文件应静态扫描失败。"""
        gate = FrontendGate()
        result = gate.run(make_frontend_files(valid=False), project_name="test")
        assert result.gate_name == "frontend"
        assert result.passed is False
        assert len(result.all_issues) > 0


# ──────────────────────────────────────────────
# BackendGate 测试
# ──────────────────────────────────────────────

class TestBackendGate:
    """后端 Gate 测试组。"""

    def test_no_backend_files_skipped(self):
        """无 Python 文件时应跳过，返回 passed=True。"""
        gate = BackendGate()
        result = gate.run([], project_name="test")
        assert result.passed is True
        assert result.skipped is True

    def test_valid_python_passes(self):
        """合法 Python 文件应通过 compileall。"""
        gate = BackendGate()
        result = gate.run(make_backend_files(valid=True), project_name="test")
        assert result.gate_name == "backend"
        # compileall 步骤应通过
        compileall_step = next(
            (s for s in result.steps if s.step_name == "compileall"), None
        )
        assert compileall_step is not None
        assert compileall_step.passed is True

    def test_syntax_error_fails(self):
        """语法错误 Python 文件应被 compileall 捕获，Gate 失败。"""
        gate = BackendGate()
        result = gate.run(make_backend_files(valid=False), project_name="test")
        assert result.gate_name == "backend"
        assert result.passed is False


# ──────────────────────────────────────────────
# MermaidGate 测试
# ──────────────────────────────────────────────

class TestMermaidGate:
    """Mermaid Gate 测试组。"""

    def test_no_mermaid_files_skipped(self):
        """无 Mermaid 内容时应跳过。"""
        gate = MermaidGate()
        result = gate.run([], project_name="test")
        assert result.passed is True
        assert result.skipped is True

    def test_valid_mermaid_passes(self):
        """合法 erDiagram 应通过校验。"""
        gate = MermaidGate()
        result = gate.run(make_mermaid_files(valid=True), project_name="test")
        assert result.passed is True

    def test_invalid_diagram_type_fails(self):
        """非法图表类型应被检测到。"""
        gate = MermaidGate()
        result = gate.run(make_mermaid_files(valid=False), project_name="test")
        assert result.passed is False
        assert any("invalidType" in issue for issue in result.all_issues)

    def test_empty_mermaid_fails(self):
        """空 Mermaid 代码块应失败。"""
        gate = MermaidGate()
        files = [FileEntry(export_path="docs/d.md", content="```mermaid\n\n```")]
        result = gate.run(files, project_name="test")
        assert result.passed is False


# ──────────────────────────────────────────────
# GateRunner 测试
# ──────────────────────────────────────────────

class TestGateRunner:
    """Gate 统一执行器测试组。"""

    def test_all_pass_when_no_files(self):
        """无文件时三道 Gate 全部跳过，suite passed=True。"""
        runner = GateRunner()
        suite = runner.run_all([], project_name="test")
        assert suite.passed is True
        assert len(suite.results) == 3
        assert all(r.skipped for r in suite.results)

    def test_selective_gates(self):
        """可以只启用部分 Gate。"""
        runner = GateRunner(run_frontend=False, run_mermaid=False)
        suite = runner.run_all(make_backend_files(valid=True), project_name="test")
        assert len(suite.results) == 1
        assert suite.results[0].gate_name == "backend"

    def test_failed_gates_listed(self):
        """失败的 Gate 应出现在 failed_gates 列表中。"""
        runner = GateRunner(run_frontend=False, run_mermaid=False)
        suite = runner.run_all(make_backend_files(valid=False), project_name="test")
        assert not suite.passed
        assert len(suite.failed_gates) == 1
        assert suite.failed_gates[0].gate_name == "backend"


# ──────────────────────────────────────────────
# IssueClassifier 测试
# ──────────────────────────────────────────────

class TestIssueClassifier:
    """问题分类器测试组。"""

    def _make_suite(self, failed_gates: list[str]) -> GateSuiteResult:
        """
        构造包含指定失败 Gate 的 GateSuiteResult。

        - failed_gates: 失败 Gate 名称列表
        """
        results = []
        for name in ["frontend", "backend", "mermaid"]:
            passed = name not in failed_gates
            results.append(
                GateResult(
                    gate_name=name,
                    passed=passed,
                    steps=[
                        GateStepResult(
                            step_name="check",
                            passed=passed,
                            issues=[] if passed else [f"{name} 检查失败"],
                        )
                    ],
                )
            )
        return GateSuiteResult(results=results)

    def test_all_pass_no_retry(self):
        """所有 Gate 通过时，不需要重跑 Agent。"""
        suite = self._make_suite([])
        classifier = IssueClassifier()
        result = classifier.classify(suite)
        assert not result.needs_retry
        assert result.agents_to_retry == []

    def test_frontend_fail_maps_to_frontend_agent(self):
        """前端 Gate 失败应映射到 frontend Agent。"""
        suite = self._make_suite(["frontend"])
        classifier = IssueClassifier()
        result = classifier.classify(suite)
        assert result.needs_retry
        assert "frontend" in result.agents_to_retry

    def test_mermaid_fail_maps_to_diagram_agent(self):
        """Mermaid Gate 失败应映射到 diagram Agent。"""
        suite = self._make_suite(["mermaid"])
        classifier = IssueClassifier()
        result = classifier.classify(suite)
        assert "diagram" in result.agents_to_retry

    def test_multiple_gates_fail(self):
        """多个 Gate 失败时返回多个 Agent。"""
        suite = self._make_suite(["frontend", "backend"])
        classifier = IssueClassifier()
        result = classifier.classify(suite)
        assert "frontend" in result.agents_to_retry
        assert "backend" in result.agents_to_retry

    def test_fix_context_format(self):
        """get_fix_context 应返回包含问题列表的字符串。"""
        suite = self._make_suite(["backend"])
        classifier = IssueClassifier()
        result = classifier.classify(suite)
        ctx = result.get_fix_context("backend")
        assert "backend 检查失败" in ctx


# ──────────────────────────────────────────────
# GateResult to_dict 测试
# ──────────────────────────────────────────────

class TestGateModels:
    """Gate 数据模型测试组。"""

    def test_gate_result_to_dict(self):
        """GateResult.to_dict 应包含关键字段。"""
        result = GateResult(
            gate_name="backend",
            passed=False,
            steps=[
                GateStepResult(
                    step_name="ruff_check",
                    passed=False,
                    issues=["E501 line too long"],
                )
            ],
        )
        d = result.to_dict()
        assert d["gate_name"] == "backend"
        assert d["passed"] is False
        assert "E501 line too long" in d["issues"]

    def test_suite_to_dict(self):
        """GateSuiteResult.to_dict 应包含 failed_gates 列表。"""
        suite = GateSuiteResult(results=[
            GateResult(gate_name="frontend", passed=True, steps=[]),
            GateResult(
                gate_name="backend",
                passed=False,
                steps=[GateStepResult(step_name="c", passed=False, issues=["err"])],
            ),
        ])
        d = suite.to_dict()
        assert "backend" in d["failed_gates"]
        assert "frontend" not in d["failed_gates"]
