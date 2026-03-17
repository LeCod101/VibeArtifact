"""
Gate 统一执行器模块。

接收 FileCollection，依次运行前端、后端、Mermaid 三道 Gate，
汇总结果为 GateSuiteResult，供编排器决策是否继续。
"""

from __future__ import annotations

import logging

from runtime_tools.exporters.collector import FileCollection
from runtime_tools.gates.backend_gate import BackendGate
from runtime_tools.gates.frontend_gate import FrontendGate
from runtime_tools.gates.mermaid_gate import MermaidGate
from runtime_tools.gates.models import GateSuiteResult

logger = logging.getLogger(__name__)


class GateRunner:
    """
    Gate 统一执行器。

    按顺序运行前端、后端、Mermaid 三道门禁，
    返回汇总的 GateSuiteResult。
    """

    def __init__(
        self,
        run_frontend: bool = True,
        run_backend: bool = True,
        run_mermaid: bool = True,
    ) -> None:
        """
        初始化 Gate 执行器。

        - run_frontend: 是否执行前端 Gate
        - run_backend: 是否执行后端 Gate
        - run_mermaid: 是否执行 Mermaid Gate
        """
        self._run_frontend = run_frontend
        self._run_backend = run_backend
        self._run_mermaid = run_mermaid

    def run_all(self, files: FileCollection, project_name: str = "project") -> GateSuiteResult:
        """
        执行所有启用的 Gate 检查。

        按顺序运行各 Gate，遇到失败不提前退出（收集完整结果）。

        - files: 待检查的文件集合
        - project_name: 项目名称，用于日志
        - 返回: GateSuiteResult，包含所有 Gate 的结果
        """
        suite = GateSuiteResult()

        if self._run_frontend:
            logger.info("[Gate] 运行前端 Gate: %s", project_name)
            result = FrontendGate().run(files, project_name)
            suite.results.append(result)
            logger.info(
                "[Gate] 前端 Gate %s: passed=%s",
                project_name, result.passed,
            )

        if self._run_backend:
            logger.info("[Gate] 运行后端 Gate: %s", project_name)
            result = BackendGate().run(files, project_name)
            suite.results.append(result)
            logger.info(
                "[Gate] 后端 Gate %s: passed=%s",
                project_name, result.passed,
            )

        if self._run_mermaid:
            logger.info("[Gate] 运行 Mermaid Gate: %s", project_name)
            result = MermaidGate().run(files, project_name)
            suite.results.append(result)
            logger.info(
                "[Gate] Mermaid Gate %s: passed=%s",
                project_name, result.passed,
            )

        logger.info(
            "[Gate] 所有 Gate 完成: passed=%s, 失败 Gate=%s",
            suite.passed,
            [r.gate_name for r in suite.failed_gates],
        )
        return suite
