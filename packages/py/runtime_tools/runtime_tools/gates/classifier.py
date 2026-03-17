"""
问题分类器模块。

Gate 失败后，将 GateSuiteResult 中的问题列表分析归类，
决定应该重跑哪些 Agent 来修复问题。

分类规则：
- 前端 Gate 失败 → 重跑 frontend_agent
- 后端 Gate 失败 → 重跑 backend_agent
- Mermaid Gate 失败 → 重跑 diagram_agent
- 多个 Gate 同时失败 → 返回多个 Agent
"""

from __future__ import annotations

import logging

from runtime_tools.gates.models import GateSuiteResult

logger = logging.getLogger(__name__)

# Gate 名称到负责修复的 Agent 映射
_GATE_TO_AGENT: dict[str, str] = {
    "frontend": "frontend",
    "backend": "backend",
    "mermaid": "diagram",
}


class IssueClassifier:
    """
    问题分类器。

    接收 GateSuiteResult，分析失败的 Gate，
    返回需要重跑的 Agent ID 列表和问题摘要。
    """

    def classify(self, suite: GateSuiteResult) -> ClassificationResult:
        """
        分析 Gate 结果，输出修复方案。

        - suite: 所有 Gate 的汇总结果
        - 返回: ClassificationResult，包含需要重跑的 Agent 和问题摘要
        """
        if suite.passed:
            return ClassificationResult(
                agents_to_retry=[],
                issue_summary="所有 Gate 通过，无需修复",
                issues_by_agent={},
            )

        agents_to_retry: list[str] = []
        issues_by_agent: dict[str, list[str]] = {}

        for gate_result in suite.failed_gates:
            agent_id = _GATE_TO_AGENT.get(gate_result.gate_name)
            if agent_id is None:
                logger.warning(
                    "未知 Gate 名称 '%s'，无法映射到修复 Agent",
                    gate_result.gate_name,
                )
                continue

            if agent_id not in agents_to_retry:
                agents_to_retry.append(agent_id)

            issues_by_agent[agent_id] = gate_result.all_issues

            logger.info(
                "Gate '%s' 失败，将重跑 Agent '%s'，问题数：%d",
                gate_result.gate_name,
                agent_id,
                len(gate_result.all_issues),
            )

        # 生成问题摘要
        total_issues = len(suite.all_issues)
        failed_gates = [r.gate_name for r in suite.failed_gates]
        summary = (
            f"Gate 检查失败：{', '.join(failed_gates)}，"
            f"共 {total_issues} 个问题，"
            f"计划重跑：{', '.join(agents_to_retry)}"
        )

        return ClassificationResult(
            agents_to_retry=agents_to_retry,
            issue_summary=summary,
            issues_by_agent=issues_by_agent,
        )


class ClassificationResult:
    """
    问题分类结果。

    描述 Gate 失败后的修复方案。
    - agents_to_retry: 需要重跑的 Agent ID 列表
    - issue_summary: 问题摘要字符串
    - issues_by_agent: 各 Agent 对应的具体问题列表
    """

    def __init__(
        self,
        agents_to_retry: list[str],
        issue_summary: str,
        issues_by_agent: dict[str, list[str]],
    ) -> None:
        """
        初始化分类结果。

        - agents_to_retry: 需要重跑的 Agent ID 列表
        - issue_summary: 问题摘要
        - issues_by_agent: 各 Agent 对应的问题列表
        """
        self.agents_to_retry = agents_to_retry
        self.issue_summary = issue_summary
        self.issues_by_agent = issues_by_agent

    @property
    def needs_retry(self) -> bool:
        """
        是否需要重跑 Agent。
        """
        return len(self.agents_to_retry) > 0

    def get_fix_context(self, agent_id: str) -> str:
        """
        获取特定 Agent 的修复上下文。

        将该 Agent 对应的问题列表格式化为字符串，
        注入到重跑时的 step_input 中供 Agent 参考。

        - agent_id: Agent 标识
        - 返回: 格式化的问题描述字符串
        """
        issues = self.issues_by_agent.get(agent_id, [])
        if not issues:
            return "Gate 检查失败，请修复代码质量问题"
        issues_text = "\n".join(f"- {issue}" for issue in issues[:10])
        return f"以下问题需要修复：\n{issues_text}"
