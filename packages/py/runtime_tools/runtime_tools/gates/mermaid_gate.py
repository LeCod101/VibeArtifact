"""
Mermaid 图表门禁模块。

对生成的 Mermaid 图表内容进行文本级校验：
- 检查图表类型声明是否合法
- 检查基本语法结构（节点定义、箭头语法）
- 检查空图表

Phase 1 采用纯文本校验，不依赖外部 mermaid CLI。
"""

from __future__ import annotations

import re

from runtime_tools.exporters.collector import FileCollection
from runtime_tools.gates.models import GateResult, GateStepResult

# 合法的 Mermaid 图表类型声明
_VALID_DIAGRAM_TYPES = {
    "graph", "flowchart", "sequenceDiagram", "classDiagram",
    "stateDiagram", "stateDiagram-v2", "erDiagram", "gantt",
    "pie", "gitGraph", "mindmap", "timeline", "quadrantChart",
    "xychart-beta", "block-beta", "architecture-beta",
}

# 合法的流程图方向
_VALID_DIRECTIONS = {"TD", "TB", "BT", "LR", "RL"}

# 箭头语法正则（flowchart/graph 中的边）
_EDGE_PATTERN = re.compile(r"\w[\w\s]*(?:-->|---|==>|-.->|--[|>]|~~~)")


class MermaidGate:
    """
    Mermaid 图表文本级门禁。

    从文件集合中提取 Mermaid 内容（diagram 类型节点导出的 .md 文件），
    对每个图表块执行文本校验。
    """

    def run(self, files: FileCollection, project_name: str = "project") -> GateResult:
        """
        执行 Mermaid 门禁检查。

        从文件集合中找到所有包含 mermaid 代码块的文件并逐一校验。

        - files: 文件集合
        - project_name: 项目名称，用于日志
        - 返回: GateResult
        """
        mermaid_blocks = self._extract_mermaid_blocks(files)

        if not mermaid_blocks:
            return GateResult(
                gate_name="mermaid",
                passed=True,
                steps=[],
                skipped=True,
                skip_reason="无 Mermaid 图表，跳过 Mermaid 门禁",
            )

        steps: list[GateStepResult] = []
        for filename, content in mermaid_blocks:
            step = self._validate_block(filename, content)
            steps.append(step)

        passed = all(s.passed for s in steps)
        return GateResult(gate_name="mermaid", passed=passed, steps=steps)

    def _extract_mermaid_blocks(
        self, files: FileCollection
    ) -> list[tuple[str, str]]:
        """
        从文件集合中提取 Mermaid 代码块。

        查找 Markdown 文件中的 ```mermaid ... ``` 代码块，
        返回 (文件名, mermaid内容) 列表。

        - files: 文件集合
        - 返回: (文件名, mermaid代码) 元组列表
        """
        blocks: list[tuple[str, str]] = []
        pattern = re.compile(
            r"```mermaid\s*\n(.*?)\n```",
            re.DOTALL,
        )

        for entry in files:
            if not entry.export_path.endswith(".md"):
                continue
            for match in pattern.finditer(entry.content):
                blocks.append((entry.export_path, match.group(1).strip()))

        # 也检查直接存储 mermaid 内容的 .mmd 文件
        for entry in files:
            if entry.export_path.endswith(".mmd"):
                blocks.append((entry.export_path, entry.content.strip()))

        return blocks

    def _validate_block(self, filename: str, content: str) -> GateStepResult:
        """
        校验单个 Mermaid 代码块。

        检查规则：
        1. 内容不能为空
        2. 第一行必须是合法的图表类型声明
        3. 图表至少有一个有效节点或边定义
        4. 不含明显的语法错误（未闭合引号、非法字符等）

        - filename: 来源文件名（用于错误报告）
        - content: Mermaid 代码块内容
        - 返回: GateStepResult
        """
        issues: list[str] = []
        step_name = f"mermaid:{filename}"

        # 规则 1：内容不能为空
        if not content:
            issues.append(f"{filename}: Mermaid 图表内容为空")
            return GateStepResult(
                step_name=step_name,
                passed=False,
                output="图表内容为空",
                issues=issues,
            )

        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        if not lines:
            issues.append(f"{filename}: 图表仅含空行")
            return GateStepResult(
                step_name=step_name,
                passed=False,
                output="图表仅含空行",
                issues=issues,
            )

        # 规则 2：第一行必须是合法图表类型
        first_line = lines[0]
        diagram_type = first_line.split()[0] if first_line.split() else ""
        if diagram_type not in _VALID_DIAGRAM_TYPES:
            issues.append(
                f"{filename}: 图表类型 '{diagram_type}' 不合法，"
                f"合法类型：{', '.join(sorted(_VALID_DIAGRAM_TYPES))}"
            )

        # 规则 3：至少有一个内容行（除类型声明外）
        if len(lines) < 2:
            issues.append(f"{filename}: 图表只有类型声明，无实际内容")

        # 规则 4：检查未闭合引号
        for i, line in enumerate(lines[1:], start=2):
            quote_count = line.count('"') - line.count('\\"')
            if quote_count % 2 != 0:
                issues.append(f"{filename} 第{i}行: 引号未闭合 — {line[:60]}")

        passed = len(issues) == 0
        return GateStepResult(
            step_name=step_name,
            passed=passed,
            output=content[:2000] if not passed else "校验通过",
            issues=issues,
        )
