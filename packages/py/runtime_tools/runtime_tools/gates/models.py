"""
Gate 通用数据模型模块。

定义所有门禁检查共享的结构体：
- GateStepResult：单步检查结果
- GateResult：一个 Gate 的整体结果
- GateSuiteResult：所有 Gate 的汇总结果
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GateStepResult:
    """
    单步检查结果。

    记录一道具体检查（如 tsc / ruff / mermaid-validate）的执行结果。
    - step_name: 步骤名称
    - passed: 是否通过
    - output: 工具原始输出（截断至 4000 字符）
    - issues: 提取出的问题行列表
    """

    step_name: str
    passed: bool
    output: str = ""
    issues: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    """
    单个 Gate 的整体结果。

    聚合一个 Gate 下所有步骤的结果，提供便捷的通过判断。
    - gate_name: 门禁名称（frontend / backend / mermaid）
    - passed: 是否整体通过（所有步骤都通过）
    - steps: 各步骤结果列表
    - skipped: 是否因条件不满足而跳过
    - skip_reason: 跳过原因说明
    """

    gate_name: str
    passed: bool
    steps: list[GateStepResult] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def all_issues(self) -> list[str]:
        """
        收集所有步骤的问题列表。

        返回所有步骤中 issues 字段的合并列表。
        """
        result: list[str] = []
        for step in self.steps:
            result.extend(step.issues)
        return result

    def to_dict(self) -> dict:
        """
        转换为可序列化的字典。

        用于写入 IR decision/risk 节点的 props。
        """
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "issues": self.all_issues,
            "steps": [
                {
                    "step_name": s.step_name,
                    "passed": s.passed,
                    "issues": s.issues,
                }
                for s in self.steps
            ],
        }


@dataclass
class GateSuiteResult:
    """
    所有 Gate 的汇总结果。

    汇总前端、后端、Mermaid 三个 Gate 的执行结果。
    - results: 各 Gate 结果列表
    """

    results: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """
        是否所有 Gate 都通过（跳过的不计入失败）。
        """
        return all(r.passed or r.skipped for r in self.results)

    @property
    def failed_gates(self) -> list[GateResult]:
        """
        返回所有未通过的 Gate 列表。
        """
        return [r for r in self.results if not r.passed and not r.skipped]

    @property
    def all_issues(self) -> list[str]:
        """
        汇总所有 Gate 的问题列表。
        """
        issues: list[str] = []
        for r in self.results:
            for issue in r.all_issues:
                issues.append(f"[{r.gate_name}] {issue}")
        return issues

    def to_dict(self) -> dict:
        """
        转换为可序列化的字典。
        """
        return {
            "passed": self.passed,
            "failed_gates": [r.gate_name for r in self.failed_gates],
            "all_issues": self.all_issues,
            "results": [r.to_dict() for r in self.results],
        }
