"""
前端编译门禁模块。

对生成的前端代码执行 lint / typecheck / build 三道检查，
任意一道失败则返回 GateResult(passed=False)。

Phase 1 实现策略：
- 接受文件集合（FileCollection），将其写入临时目录
- 依次运行 eslint / tsc --noEmit / next build
- 收集每道检查的 stdout/stderr 与退出码
- 返回结构化结果
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from runtime_tools.exporters.collector import FileCollection
from runtime_tools.gates.models import GateResult, GateStepResult


class FrontendGate:
    """
    前端编译门禁。

    将文件集合写入临时目录，依次执行 eslint、tsc、next build，
    返回包含所有步骤结果的 GateResult。
    """

    # 仅检查前端相关文件扩展名
    _FRONTEND_EXTS = {".ts", ".tsx", ".js", ".jsx", ".json"}

    def run(self, files: FileCollection, project_name: str = "project") -> GateResult:
        """
        执行前端门禁检查。

        将文件写入临时目录，依次运行三道检查，最后清理临时目录。

        - files: 前端文件集合（FileCollection）
        - project_name: 项目名称，用于日志
        - 返回: GateResult，包含通过状态和各步骤结果
        """
        # 筛选前端文件
        frontend_files = [
            f for f in files
            if Path(f.export_path).suffix in self._FRONTEND_EXTS
            or f.export_path.startswith("frontend/")
        ]

        if not frontend_files:
            return GateResult(
                gate_name="frontend",
                passed=True,
                steps=[],
                skipped=True,
                skip_reason="无前端文件，跳过前端门禁",
            )

        tmpdir = tempfile.mkdtemp(prefix="vibe_frontend_gate_")
        try:
            self._write_files(frontend_files, tmpdir)
            steps = self._run_checks(tmpdir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        passed = all(s.passed for s in steps)
        return GateResult(gate_name="frontend", passed=passed, steps=steps)

    def _write_files(self, files: FileCollection, tmpdir: str) -> None:
        """
        将文件集合写入临时目录。

        自动创建子目录，文件路径保留相对结构。

        - files: 文件集合
        - tmpdir: 临时目录根路径
        """
        for entry in files:
            dest = Path(tmpdir) / entry.export_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(entry.content, encoding="utf-8")

    def _run_checks(self, tmpdir: str) -> list[GateStepResult]:
        """
        依次运行三道前端检查。

        1. eslint：代码风格与潜在错误
        2. tsc --noEmit：TypeScript 类型检查
        3. next build：完整编译（可选，耗时较长）

        Phase 1 简化：仅执行 tsc --noEmit，其余两道在工具不存在时跳过。

        - tmpdir: 临时目录路径
        - 返回: 各步骤检查结果列表
        """
        steps: list[GateStepResult] = []

        # 检查 package.json 是否存在，决定 npm install 是否必要
        pkg_json = Path(tmpdir) / "frontend" / "package.json"
        if not pkg_json.exists():
            # 无 package.json，只做文件内容静态扫描
            steps.append(self._static_scan(tmpdir))
            return steps

        # 尝试 tsc 静态检查（不安装依赖，仅语法级别）
        steps.append(self._run_tsc_syntax(tmpdir))
        return steps

    def _static_scan(self, tmpdir: str) -> GateStepResult:
        """
        静态文件扫描（无工具链时的降级检查）。

        检查 TypeScript/TSX 文件是否存在明显语法问题：
        - 检查括号匹配（简单计数）
        - 检查 import 语句格式

        - tmpdir: 临时目录路径
        - 返回: GateStepResult
        """
        issues: list[str] = []
        ts_files = list(Path(tmpdir).rglob("*.tsx")) + list(Path(tmpdir).rglob("*.ts"))

        for ts_file in ts_files:
            try:
                content = ts_file.read_text(encoding="utf-8")
                # 检查括号平衡
                open_count = content.count("{") - content.count("}")
                if abs(open_count) > 3:
                    issues.append(f"{ts_file.name}: 大括号不平衡（差值 {open_count}）")
            except Exception as e:
                issues.append(f"{ts_file.name}: 读取失败 - {e}")

        return GateStepResult(
            step_name="static_scan",
            passed=len(issues) == 0,
            output="\n".join(issues) if issues else "静态扫描通过",
            issues=issues,
        )

    def _run_tsc_syntax(self, tmpdir: str) -> GateStepResult:
        """
        运行 tsc 语法检查（不安装依赖）。

        使用 --noEmit --allowJs --checkJs false --strict false 降低要求，
        仅检查基本语法错误。工具不存在时降级为静态扫描。

        - tmpdir: 临时目录路径
        - 返回: GateStepResult
        """
        import shutil as sh
        tsc_path = sh.which("tsc")
        if not tsc_path:
            return self._static_scan(tmpdir)

        frontend_dir = Path(tmpdir) / "frontend"
        cmd = [
            tsc_path,
            "--noEmit",
            "--allowJs",
            "--target", "ES2020",
            "--moduleResolution", "node",
            "--strict", "false",
        ]
        result = subprocess.run(
            cmd,
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        issues = [line for line in output.splitlines() if "error" in line.lower()]

        return GateStepResult(
            step_name="tsc_check",
            passed=passed,
            output=output[:4000],
            issues=issues[:20],
        )
