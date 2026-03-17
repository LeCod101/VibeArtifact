"""
Gate 修复回路模块。

Gate 检查失败后，根据 IssueClassifier 的分类结果，
对相关 Agent 发起单次重跑，尝试自动修复问题。

修复策略：
1. Gate 失败 → IssueClassifier 分类 → 确定需要重跑的 Agent
2. 对每个需要重跑的 Agent 注入修复上下文，重新执行
3. 重跑后再次运行 Gate 验证
4. 验证通过 → 继续流程
5. 验证失败 → 标记 run 为 needs_attention，写入 risk 节点，停止重试

最大重试次数：1（Phase 1，M6 规格）
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from runtime_tools.exporters.collector import ArtifactCollector
from runtime_tools.gates.classifier import ClassificationResult, IssueClassifier
from runtime_tools.gates.models import GateSuiteResult
from runtime_tools.gates.runner import GateRunner

logger = logging.getLogger(__name__)

# Phase 1 最大自动修复次数
MAX_RETRY_COUNT = 1


class RepairLoop:
    """
    Gate 修复回路。

    协调 Gate 检查、问题分类、Agent 重跑、结果验证的完整修复流程。
    """

    def __init__(self, manager, run_id: UUID) -> None:
        """
        初始化修复回路。

        - manager: RunManager 实例，用于状态更新
        - run_id: 当前 job_run ID
        """
        self._manager = manager
        self._run_id = run_id
        self._classifier = IssueClassifier()
        self._gate_runner = GateRunner()

    async def run_gates_and_repair(
        self,
        snapshot_id: str,
        scope_draft_json: str,
        project_name: str = "project",
    ) -> RepairResult:
        """
        执行 Gate 检查，失败时触发一次修复重跑。

        完整流程：
        1. 从数据库加载最新快照节点
        2. 运行所有 Gate
        3. 通过 → 返回成功
        4. 失败 → 分类问题 → 重跑相关 Agent → 再次 Gate
        5. 再次失败 → 标记 needs_attention

        - snapshot_id: 当前快照 ID
        - scope_draft_json: 原始 scope_draft JSON（用于重跑上下文）
        - project_name: 项目名称，用于日志
        - 返回: RepairResult
        """
        collector = ArtifactCollector()

        # 从数据库加载最新快照节点
        nodes = await self.load_snapshot_nodes(snapshot_id)
        files = collector.collect(nodes)

        # 第一轮 Gate 检查
        logger.info("[修复回路] 开始第一轮 Gate 检查: run_id=%s", self._run_id)
        suite = self._gate_runner.run_all(files, project_name)

        if suite.passed:
            logger.info("[修复回路] Gate 全部通过，无需修复")
            return RepairResult(
                passed=True,
                repaired=False,
                gate_suite=suite,
                retry_count=0,
            )

        # 分析问题，确定需要重跑的 Agent
        classification = self._classifier.classify(suite)
        logger.info(
            "[修复回路] Gate 失败，分类结果: %s",
            classification.issue_summary,
        )

        if not classification.needs_retry:
            logger.warning("[修复回路] 无法映射到修复 Agent，标记 needs_attention")
            await self._mark_needs_attention(suite, classification)
            return RepairResult(
                passed=False,
                repaired=False,
                gate_suite=suite,
                retry_count=0,
                needs_attention=True,
                classification=classification,
            )

        # 单次修复重跑
        logger.info(
            "[修复回路] 开始修复重跑，目标 Agent: %s",
            classification.agents_to_retry,
        )
        repaired_nodes = await self._retry_agents(
            agents=classification.agents_to_retry,
            classification=classification,
            snapshot_id=snapshot_id,
            scope_draft_json=scope_draft_json,
        )

        # 第二轮 Gate 验证
        logger.info("[修复回路] 重跑完成，开始第二轮 Gate 验证")
        repaired_files = collector.collect(repaired_nodes)
        suite2 = self._gate_runner.run_all(repaired_files, project_name)

        if suite2.passed:
            logger.info("[修复回路] 修复成功，第二轮 Gate 通过")
            return RepairResult(
                passed=True,
                repaired=True,
                gate_suite=suite2,
                retry_count=1,
            )

        # 修复后仍失败 → needs_attention
        logger.warning("[修复回路] 修复后 Gate 仍失败，标记 needs_attention")
        classification2 = self._classifier.classify(suite2)
        await self._mark_needs_attention(suite2, classification2)

        return RepairResult(
            passed=False,
            repaired=True,
            gate_suite=suite2,
            retry_count=1,
            needs_attention=True,
            classification=classification2,
        )

    async def _retry_agents(
        self,
        agents: list[str],
        classification: ClassificationResult,
        snapshot_id: str,
        scope_draft_json: str,
    ) -> list[dict]:
        """
        对需要修复的 Agent 发起重跑。

        将修复上下文注入 step_input，调用 agent_task 重新执行。
        重跑结果写入 IR 快照后，返回更新后的节点列表。

        - agents: 需要重跑的 Agent ID 列表
        - classification: 问题分类结果（提供修复上下文）
        - snapshot_id: 当前快照 ID
        - scope_draft_json: 原始 scope_draft JSON
        - 返回: 重跑后的 IR 节点列表
        """
        from worker_app.tasks.agent_task import _execute_agent_step_async

        run_id_str = str(self._run_id)

        for agent_id in agents:
            fix_context = classification.get_fix_context(agent_id)

            # 将修复上下文注入 step_input
            try:
                base_input = json.loads(scope_draft_json)
            except (json.JSONDecodeError, TypeError):
                base_input = {}

            base_input["fix_context"] = fix_context
            base_input["is_repair"] = True
            fix_input_json = json.dumps(base_input, ensure_ascii=False)

            logger.info(
                "[修复回路] 重跑 Agent '%s': run_id=%s",
                agent_id, run_id_str,
            )

            await _execute_agent_step_async(
                run_id=run_id_str,
                agent_id=agent_id,
                snapshot_id=snapshot_id,
                step_input_json=fix_input_json,
            )

        # 重新从数据库加载最新快照节点
        return await self.load_snapshot_nodes(snapshot_id)

    async def load_snapshot_nodes(self, snapshot_id: str) -> list[dict]:
        """
        从数据库加载指定快照的所有 IR 节点。

        Phase 1 简化：直接查询 ir_nodes 表。

        - snapshot_id: 快照 ID
        - 返回: IR 节点字典列表
        """
        from sqlalchemy import text
        from worker_app.orchestrator.run_manager import (
            get_worker_session_factory,
        )

        session_factory = get_worker_session_factory()
        async with session_factory() as session:
            result = await session.execute(
                text(
                    "SELECT node_type, props, label FROM ir_nodes "
                    "WHERE snapshot_id = :sid"
                ),
                {"sid": snapshot_id},
            )
            rows = result.fetchall()
            return [
                {
                    "node_type": row[0],
                    "props": row[1] or {},
                    "label": row[2],
                }
                for row in rows
            ]

    async def _mark_needs_attention(
        self,
        suite: GateSuiteResult,
        classification: ClassificationResult,
    ) -> None:
        """
        将 run 标记为 needs_attention 状态。

        更新 job_run 状态，记录 Gate 失败的详细信息。

        - suite: Gate 汇总结果
        - classification: 问题分类结果
        """
        from worker_app.orchestrator.run_manager import RunManager

        manager = RunManager()
        await manager.mark_run_needs_attention(
            run_id=self._run_id,
            error_message=classification.issue_summary,
            gate_result=suite.to_dict(),
        )
        logger.info(
            "[修复回路] run %s 已标记为 needs_attention",
            self._run_id,
        )


class RepairResult:
    """
    修复回路执行结果。

    - passed: 最终 Gate 是否通过
    - repaired: 是否触发了修复重跑
    - gate_suite: 最终的 Gate 汇总结果
    - retry_count: 实际重跑次数
    - needs_attention: 是否需要人工介入
    - classification: 问题分类结果（失败时有值）
    """

    def __init__(
        self,
        passed: bool,
        repaired: bool,
        gate_suite: GateSuiteResult,
        retry_count: int,
        needs_attention: bool = False,
        classification: ClassificationResult | None = None,
    ) -> None:
        """
        初始化修复结果。
        """
        self.passed = passed
        self.repaired = repaired
        self.gate_suite = gate_suite
        self.retry_count = retry_count
        self.needs_attention = needs_attention
        self.classification = classification
