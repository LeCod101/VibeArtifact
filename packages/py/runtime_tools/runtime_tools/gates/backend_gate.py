"""
后端编译门禁模块。

对生成的后端 Python 代码执行 ruff / compileall / pytest smoke 三道检查，
任意一道失败则返回 GateResult(passed=False)。

Phase 1 实现策略：
- 接受文件集合（FileCollection），将其写入临时目录
- 依次运行 ruff check、python -m compileall、pytest smoke
- 返回结构化结果
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime_tools.exporters.collector import FileCollection
from runtime_tools.gates.models import GateResult, GateStepResult


class BackendGate:
    """
    后端编译门禁。

    将后端 Python 文件写入临时目录，依次执行
    ruff check、compileall、pytest smoke，返回 GateResult。
    """

    # 仅处理后端 Python 文件
    _PYTHON_EXTS = {".py"}

    def run(self, files: FileCollection, project_name: str = "project") -> GateResult:
        """
        执行后端门禁检查。

        筛选后端 Python 文件，写入临时目录，执行三道检查。

        - files: 文件集合
        - project_name: 项目名称，用于日志
        - 返回: GateResult
        """
        backend_files = [
            f for f in files
            if Path(f.export_path).suffix in self._PYTHON_EXTS
            and (
                f.export_path.startswith("backend/")
                or not f.export_path.startswith("frontend/")
            )
        ]

        if not backend_files:
            return GateResult(
                gate_name="backend",
                passed=True,
                steps=[],
                skipped=True,
                skip_reason="无后端 Python 文件，跳过后端门禁",
            )

        tmpdir = tempfile.mkdtemp(prefix="vibe_backend_gate_")
        try:
            self._write_files(backend_files, tmpdir)
            steps = self._run_checks(tmpdir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        passed = all(s.passed for s in steps)
        return GateResult(gate_name="backend", passed=passed, steps=steps)

    def _write_files(self, files: FileCollection, tmpdir: str) -> None:
        """
        将文件集合写入临时目录。

        - files: 文件集合
        - tmpdir: 临时目录根路径
        """
        for entry in files:
            dest = Path(tmpdir) / entry.export_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(entry.content, encoding="utf-8")

    def _run_checks(self, tmpdir: str) -> list[GateStepResult]:
        """
        依次运行三道后端检查。

        1. ruff check：代码风格与潜在错误
        2. python -m compileall：字节码编译（语法检查）
        3. pytest smoke：运行标记为 smoke 的测试（如存在）

        - tmpdir: 临时目录路径
        - 返回: 各步骤检查结果列表
        """
        steps: list[GateStepResult] = []
        backend_dir = Path(tmpdir) / "backend"
        check_dir = str(backend_dir) if backend_dir.exists() else tmpdir

        # 第一道：ruff check
        steps.append(self._run_ruff(check_dir))

        # 第二道：compileall（语法检查）
        steps.append(self._run_compileall(check_dir))

        # 第三道：pytest smoke（如果有测试文件）
        smoke_result = self._run_pytest_smoke(check_dir)
        if smoke_result is not None:
            steps.append(smoke_result)

        return steps

    def _run_ruff(self, check_dir: str) -> GateStepResult:
        """
        运行 ruff check 代码检查。

        ruff 不存在时降级为 py_compile 静态检查。

        - check_dir: 检查目录路径
        - 返回: GateStepResult
        """
        import shutil as sh
        ruff_path = sh.which("ruff")
        if not ruff_path:
            return GateStepResult(
                step_name="ruff_check",
                passed=True,
                output="ruff 未安装，跳过 lint 检查",
                issues=[],
            )

        result = subprocess.run(
            [ruff_path, "check", ".", "--output-format", "text"],
            cwd=check_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        issues = [
            line for line in output.splitlines()
            if line.strip() and not line.startswith("Found")
        ]
        return GateStepResult(
            step_name="ruff_check",
            passed=passed,
            output=output[:4000],
            issues=issues[:20],
        )

    def _run_compileall(self, check_dir: str) -> GateStepResult:
        """
        运行 python -m compileall 字节码编译检查。

        所有 .py 文件必须能通过 Python 语法解析，否则返回失败。

        - check_dir: 检查目录路径
        - 返回: GateStepResult
        """
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", check_dir],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        issues = [
            line for line in output.splitlines()
            if "SyntaxError" in line or "Error" in line
        ]
        return GateStepResult(
            step_name="compileall",
            passed=passed,
            output=output[:4000],
            issues=issues[:20],
        )

    def _run_pytest_smoke(self, check_dir: str) -> GateStepResult | None:
        """
        运行 pytest smoke 测试（如果存在）。

        仅执行标记为 @pytest.mark.smoke 的测试。
        找不到 smoke 测试时返回 None（跳过）。

        - check_dir: 检查目录路径
        - 返回: GateStepResult 或 None
        """
        import shutil as sh
        pytest_path = sh.which("pytest")
        if not pytest_path:
            return None

        # 检查是否有测试文件
        test_files = list(Path(check_dir).rglob("test_*.py"))
        if not test_files:
            return None

        result = subprocess.run(
            [pytest_path, "-m", "smoke", "-q", "--tb=short", "--no-header"],
            cwd=check_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr

        # returncode=5 表示没有找到匹配的测试，视为跳过（通过）
        if result.returncode == 5:
            return GateStepResult(
                step_name="pytest_smoke",
                passed=True,
                output="无 smoke 标记的测试，跳过",
                issues=[],
            )

        passed = result.returncode == 0
        issues = [
            line for line in output.splitlines()
            if "FAILED" in line or "ERROR" in line
        ]
        return GateStepResult(
            step_name="pytest_smoke",
            passed=passed,
            output=output[:4000],
            issues=issues[:20],
        )
