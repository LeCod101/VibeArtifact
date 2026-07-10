"""
一问一答模式编排器。

职责：
1. 接收用户消息
2. 加载当前工作区文件
3. 执行影响分析（ImpactAnalyzer）
4. 分支：冷启动 or 局部修改
5. 执行目标 Agent（AgentRunner），产物写入工作区
6. 生成助手回复文本
7. 返回变更摘要

工作区读写通过 WorkspaceRepository（Phase 1 起取代 IR apply_operations）。
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import UUID

from agents.analysis import (
    AgentSelector,
    ChangeSummary,
    ColdStartBootstrap,
    ImpactAnalyzer,
    ImpactReport,
)
from agents.schemas.base import AgentInput
from agents.schemas.workspace import WorkspaceFileData
from pydantic import BaseModel

from api_app.api.sse.chat_publisher import (
    publish_chat_agent_done,
    publish_chat_agent_start,
    publish_chat_analysis_done,
    publish_chat_analysis_start,
    publish_chat_apply_done,
    publish_chat_complete,
    publish_chat_failed,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 产物领域中文映射（用于 affected_areas）
# ──────────────────────────────────────────────

AREA_CN: dict[str, str] = {
    "scope": "需求范围",
    "task": "任务规划",
    "entity": "数据模型",
    "endpoint": "API接口",
    "ui_page": "前端页面",
    "ui_component": "前端组件",
    "artifact": "产物文件",
    "risk": "风险",
    "decision": "决策",
}


class ChatOrchestratorResult(BaseModel):
    """
    编排器执行结果。

    包含助手回复、变更摘要、新版本号、影响报告和总成本。
    - assistant_message: 回复给用户的助手消息文本
    - change_summary: 变更摘要（返回给前端展示）
    - new_version: 本次编排后工作区的版本标记（Phase 1 用运行标识占位）
    - impact_report: 影响分析报告
    - cost_total: 本次编排的总 LLM 费用
    """

    assistant_message: str
    change_summary: ChangeSummary
    new_version: str | None = None
    impact_report: ImpactReport
    cost_total: float = 0.0


class ChatOrchestrator:
    """
    一问一答模式编排器。

    接收用户消息，通过影响分析判定变更路径（冷启动/局部修改），
    调用 AgentRunner 执行目标 Agent，产物写入工作区，
    最终生成变更摘要和助手回复。

    设计要点：
    - 工作区读写通过 WorkspaceRepository（Phase 1 起）
    - SSE 事件驱动前端实时反馈
    - redis 参数可选，为 None 时跳过 SSE 发布
    """

    def __init__(self, db_session=None) -> None:
        """
        初始化编排器。

        参数:
            db_session: 数据库会话（预留，暂不使用）
        """
        self._db_session = db_session

    async def handle_message(
        self,
        project_id: UUID,
        conversation_id: UUID,
        branch_id: UUID,
        user_message: str,
        workspace_files: list[WorkspaceFileData] | None = None,
        conversation_context: list | None = None,
        redis=None,
    ) -> ChatOrchestratorResult:
        """
        处理用户消息，执行完整的编排流程。

        参数:
            project_id: 项目 ID
            conversation_id: 会话 ID
            branch_id: 分支 ID
            user_message: 用户输入的消息文本
            workspace_files: 当前工作区文件列表（空表示冷启动）
            conversation_context: 对话上下文消息列表（可选）
            redis: Redis 连接（可选，为空则不发 SSE）

        返回:
            ChatOrchestratorResult
        """
        conv_id_str = str(conversation_id)

        if conversation_context is None:
            conversation_context = []
        if workspace_files is None:
            workspace_files = []

        try:
            return await self._execute(
                project_id=project_id,
                conversation_id=conversation_id,
                conv_id_str=conv_id_str,
                branch_id=branch_id,
                user_message=user_message,
                workspace_files=workspace_files,
                conversation_context=conversation_context,
                redis=redis,
            )
        except Exception as exc:
            # 全局兜底：发布失败事件并返回错误结果
            error_msg = f"编排执行失败: {exc!s}"
            logger.exception(error_msg)

            await publish_chat_failed(conv_id_str, error_msg, redis=redis)

            return ChatOrchestratorResult(
                assistant_message=f"抱歉，处理您的请求时遇到了问题：{exc!s}",
                change_summary=ChangeSummary(
                    summary="执行失败",
                    affected_areas=[],
                    operations_count=0,
                    agents_executed=[],
                    warnings=[error_msg],
                ),
                impact_report=ImpactReport(
                    change_scope="partial",
                    requires_cold_start=False,
                    affected_areas=[],
                    affected_agents=[],
                    reasoning=error_msg,
                    user_intent_summary=user_message[:100],
                ),
                cost_total=0.0,
            )

    async def _execute(
        self,
        project_id: UUID,
        conversation_id: UUID,
        conv_id_str: str,
        branch_id: UUID,
        user_message: str,
        workspace_files: list[WorkspaceFileData],
        conversation_context: list,
        redis,
    ) -> ChatOrchestratorResult:
        """
        编排核心执行逻辑（从 handle_message 中拆出，便于统一异常捕获）。

        参数同 handle_message，额外传入 conv_id_str 避免重复转换。
        """
        # ── 步骤 1: SSE 通知分析开始 ──
        await publish_chat_analysis_start(conv_id_str, redis=redis)

        # ── 步骤 2: 影响分析 ──
        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(user_message, workspace_files)

        logger.info(
            "影响分析完成: conversation_id=%s, scope=%s, cold_start=%s, agents=%s",
            conv_id_str,
            report.change_scope,
            report.requires_cold_start,
            report.affected_agents,
        )

        # ── 步骤 3: SSE 通知分析完成 ──
        await publish_chat_analysis_done(
            conv_id_str,
            impact_report=report.model_dump(mode="json"),
            redis=redis,
        )

        # ── 步骤 4: 根据分析结果选择路径 ──
        total_cost = 0.0
        total_outputs = 0
        agents_executed: list[str] = []
        all_warnings: list[str] = []

        if report.requires_cold_start:
            # ── 冷启动路径 ──
            cost, outputs_count, executed, warnings = (
                await self._run_cold_start(
                    project_id=project_id,
                    user_message=user_message,
                    conv_id_str=conv_id_str,
                    redis=redis,
                )
            )
        else:
            # ── 局部修改路径 ──
            cost, outputs_count, executed, warnings = (
                await self._run_incremental(
                    project_id=project_id,
                    user_message=user_message,
                    workspace_files=workspace_files,
                    conversation_context=conversation_context,
                    report=report,
                    conv_id_str=conv_id_str,
                    redis=redis,
                )
            )

        total_cost += cost
        total_outputs += outputs_count
        agents_executed.extend(executed)
        all_warnings.extend(warnings)

        # ── 步骤 5: SSE 通知 apply 完成 ──
        await publish_chat_apply_done(
            conv_id_str,
            new_snapshot_id="",
            operations_count=total_outputs,
            redis=redis,
        )

        # ── 步骤 6: 生成变更摘要 ──
        affected_areas = self._translate_areas(report.affected_areas)
        change_summary = ChangeSummary(
            summary=self._build_summary_text(report, agents_executed, total_outputs),
            affected_areas=affected_areas,
            operations_count=total_outputs,
            agents_executed=agents_executed,
            warnings=all_warnings,
        )

        # ── 步骤 7: 生成助手回复文本 ──
        assistant_message = self._build_assistant_reply(
            report=report,
            change_summary=change_summary,
            agents_executed=agents_executed,
        )

        # ── 步骤 8: SSE 通知全部完成 ──
        await publish_chat_complete(
            conv_id_str,
            change_summary=change_summary.model_dump(mode="json"),
            redis=redis,
        )

        logger.info(
            "编排完成: conversation_id=%s, agents=%s, outputs=%d, cost=%.4f",
            conv_id_str,
            agents_executed,
            total_outputs,
            total_cost,
        )

        return ChatOrchestratorResult(
            assistant_message=assistant_message,
            change_summary=change_summary,
            impact_report=report,
            cost_total=total_cost,
        )

    async def _run_cold_start(
        self,
        project_id: UUID,
        user_message: str,
        conv_id_str: str,
        redis,
    ) -> tuple[float, int, list[str], list[str]]:
        """
        执行冷启动路径。

        创建 AgentRunner 实例，执行 ColdStartBootstrap。

        参数:
            project_id: 项目 ID
            user_message: 用户消息
            conv_id_str: 会话 ID 字符串（用于 SSE）
            redis: Redis 连接

        返回:
            (cost, outputs_count, agents_executed, warnings)
        """
        runner = self._create_agent_runner()

        bootstrap = ColdStartBootstrap(runner=runner)

        # 逐步发布 SSE（ColdStartBootstrap 内部不发 SSE，我们在外面包一层）
        for agent_id in ColdStartBootstrap.COLD_START_AGENTS:
            await publish_chat_agent_start(conv_id_str, agent_id, redis=redis)

        start_time = time.monotonic()
        result = await bootstrap.bootstrap(
            project_id=project_id,
            user_message=user_message,
        )
        duration_ms = int((time.monotonic() - start_time) * 1000)

        # 冷启动完成，发布各 Agent 完成事件
        for agent_id in result.agents_executed:
            await publish_chat_agent_done(
                conv_id_str,
                agent_id,
                # 均摊耗时
                duration_ms=duration_ms // max(len(result.agents_executed), 1),
                redis=redis,
            )

        # 产出对象数 = 高层输出数 + 文件数
        outputs_count = len(result.outputs) + len(result.files)

        return (
            0.0,
            outputs_count,
            result.agents_executed,
            result.warnings,
        )

    async def _run_incremental(
        self,
        project_id: UUID,
        user_message: str,
        workspace_files: list[WorkspaceFileData],
        conversation_context: list,
        report: ImpactReport,
        conv_id_str: str,
        redis,
    ) -> tuple[float, int, list[str], list[str]]:
        """
        执行局部修改路径。

        根据影响报告生成分层执行计划，逐层执行 Agent，
        产物累积到工作区文件视图（内存态），供后续 Agent 参考。

        参数:
            project_id: 项目 ID
            user_message: 用户消息
            workspace_files: 当前工作区文件
            conversation_context: 对话上下文
            report: 影响分析报告
            conv_id_str: 会话 ID 字符串
            redis: Redis 连接

        返回:
            (cost, outputs_count, agents_executed, warnings)
        """
        runner = self._create_agent_runner()
        selector = AgentSelector()

        # 生成分层执行计划
        execution_plan = selector.select(report)
        logger.info(
            "执行计划: %s (共 %d 层)",
            execution_plan,
            len(execution_plan),
        )

        current_files: list[WorkspaceFileData] = list(workspace_files)
        upstream_outputs: dict[str, Any] = {}
        total_cost = 0.0
        total_outputs = 0
        agents_executed: list[str] = []
        all_warnings: list[str] = []

        # 逐层执行
        for layer_idx, layer in enumerate(execution_plan):
            logger.info(
                "执行第 %d/%d 层: %s",
                layer_idx + 1,
                len(execution_plan),
                layer,
            )

            # 同层可并行执行
            layer_results = await self._execute_layer(
                runner=runner,
                layer=layer,
                project_id=project_id,
                current_files=current_files,
                upstream_outputs=upstream_outputs,
                conversation_context=conversation_context,
                user_message=user_message,
                conv_id_str=conv_id_str,
                redis=redis,
            )

            # 处理每个 Agent 的结果
            for agent_id, agent_result in layer_results:
                agents_executed.append(agent_id)

                if agent_result.warnings:
                    all_warnings.extend(agent_result.warnings)

                # 累加成本
                if agent_result.meta:
                    total_cost += agent_result.meta.total_cost

                # 产物文件并入内存态工作区视图
                for f in agent_result.files:
                    current_files.append(
                        WorkspaceFileData(
                            path=f["path"],
                            content=f["content"],
                            kind=f.get("kind", "code"),
                        )
                    )
                    total_outputs += 1

        return (
            total_cost,
            total_outputs,
            agents_executed,
            all_warnings,
        )

    async def _execute_layer(
        self,
        runner,
        layer: list[str],
        project_id: UUID,
        current_files: list[WorkspaceFileData],
        upstream_outputs: dict[str, Any],
        conversation_context: list,
        user_message: str,
        conv_id_str: str,
        redis,
    ) -> list[tuple[str, object]]:
        """
        执行单层中的所有 Agent。

        单 Agent 时直接执行，多 Agent 时 asyncio.gather 并行执行。
        每个 Agent 执行前后发布 SSE 事件。

        参数:
            runner: AgentRunner 实例
            layer: 当前层的 Agent ID 列表
            project_id: 项目 ID
            current_files: 当前工作区文件（内存态）
            upstream_outputs: 上游 Agent 输出（内存态）
            conversation_context: 对话上下文
            user_message: 用户消息（作为 task_description）
            conv_id_str: 会话 ID 字符串
            redis: Redis 连接

        返回:
            [(agent_id, AgentRunResult), ...] 列表
        """

        async def _run_single(agent_id: str):
            """
            执行单个 Agent 并发布 SSE 事件。
            """
            await publish_chat_agent_start(conv_id_str, agent_id, redis=redis)
            start_ts = time.monotonic()

            agent_input = AgentInput(
                project_id=project_id,
                run_id=None,
                workspace_files=list(current_files),
                upstream_outputs=dict(upstream_outputs),
                conversation_context=conversation_context,
                task_description=user_message,
                extra={},
            )

            result = await runner.run(agent_id, agent_input)
            duration_ms = int((time.monotonic() - start_ts) * 1000)

            await publish_chat_agent_done(
                conv_id_str, agent_id, duration_ms, redis=redis
            )
            return (agent_id, result)

        if len(layer) == 1:
            # 单 Agent，直接执行
            return [await _run_single(layer[0])]

        # 多 Agent，并行执行
        tasks = [_run_single(agent_id) for agent_id in layer]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed: list[tuple[str, object]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 为失败的 Agent 构建一个空壳结果
                logger.warning(
                    "Agent %s 并行执行失败: %s",
                    layer[i],
                    result,
                )
                # 构造一个最小化的 mock result 以保持流程继续
                from agents.executors.runner import AgentRunResult
                from agents.schemas.base import AgentOutput

                mock_output = AgentOutput(
                    reasoning=f"执行失败: {result!s}",
                    confidence=0.0,
                    warnings=[f"Agent {layer[i]} 执行异常: {result!s}"],
                )
                mock_result = AgentRunResult(
                    agent_id=layer[i],
                    output=mock_output,
                    files=[],
                    warnings=[f"Agent {layer[i]} 执行异常: {result!s}"],
                )
                processed.append((layer[i], mock_result))
            else:
                processed.append(result)

        return processed

    @staticmethod
    def _create_agent_runner():
        """
        创建 AgentRunner 实例。

        初始化 AgentRegistry 并创建 runner，
        使用 LangChainProvider 作为 LLM 调用实现。

        返回:
            AgentRunner 实例
        """
        from agents.configs.definitions import register_all_agents
        from agents.executors.runner import AgentRunner
        from runtime_tools.llm.provider import LangChainProvider

        # 确保 Agent 已注册
        registry = register_all_agents()

        # 创建 LLM Provider 和 Runner
        llm_provider = LangChainProvider()
        return AgentRunner(
            llm_provider=llm_provider,
            registry=registry,
        )

    @staticmethod
    def _translate_areas(areas: list[str]) -> list[str]:
        """
        将产物领域列表翻译为中文名称。

        参数:
            areas: 产物领域英文标识列表

        返回:
            中文名称列表（未知领域保留原文）
        """
        return [AREA_CN.get(a, a) for a in areas]

    @staticmethod
    def _build_summary_text(
        report: ImpactReport,
        agents_executed: list[str],
        outputs_count: int,
    ) -> str:
        """
        根据影响报告和执行结果生成一句话摘要。

        参数:
            report: 影响分析报告
            agents_executed: 实际执行的 Agent 列表
            outputs_count: 产出对象总数

        返回:
            变更摘要文本
        """
        if report.requires_cold_start:
            return (
                f"冷启动完成：执行了 {len(agents_executed)} 个 Agent，"
                f"共产出 {outputs_count} 个对象，建立了基础项目结构"
            )

        areas_cn = [AREA_CN.get(a, a) for a in report.affected_areas]
        areas_text = "、".join(areas_cn) if areas_cn else "相关模块"

        return (
            f"已更新 {areas_text}：执行了 {len(agents_executed)} 个 Agent，"
            f"共产出 {outputs_count} 个对象"
        )

    @staticmethod
    def _build_assistant_reply(
        report: ImpactReport,
        change_summary: ChangeSummary,
        agents_executed: list[str],
    ) -> str:
        """
        生成助手回复文本。

        拼接变更摘要、影响范围和执行的 Agent 信息。

        参数:
            report: 影响分析报告
            change_summary: 变更摘要
            agents_executed: 执行的 Agent 列表

        返回:
            助手回复文本
        """
        lines: list[str] = []

        # 主要摘要
        lines.append(change_summary.summary)
        lines.append("")

        # 影响范围
        if change_summary.affected_areas:
            lines.append(f"影响范围：{', '.join(change_summary.affected_areas)}")

        # 执行的 Agent
        if agents_executed:
            lines.append(f"执行步骤：{' → '.join(agents_executed)}")

        # 警告信息
        if change_summary.warnings:
            lines.append("")
            lines.append("注意事项：")
            for warning in change_summary.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines)
