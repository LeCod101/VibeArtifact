"""
一问一答模式编排器。

职责：
1. 接收用户消息
2. 加载当前快照（调用方传入 ir_nodes/ir_edges）
3. 执行影响分析（ImpactAnalyzer）
4. 分支：冷启动 or 局部修改
5. 执行目标 Agent（AgentRunner）
6. Apply 变更到快照（纯内存计算，不写 DB）
7. 生成助手回复文本
8. 返回变更摘要

Phase 1 不做 DB 持久化快照，调用方在 API 层负责写库。
"""

from __future__ import annotations

import asyncio
import logging
import time
from uuid import UUID

from agents.analysis import (
    AgentSelector,
    ChangeSummary,
    ColdStartBootstrap,
    ImpactAnalyzer,
    ImpactReport,
)
from agents.schemas.base import AgentInput
from ir_core.operations.apply import ApplyError, apply_operations
from ir_core.schema.data import IREdgeData, IRNodeData
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
# 节点类型中文映射（用于 affected_areas）
# ──────────────────────────────────────────────

NODE_TYPE_CN: dict[str, str] = {
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

    包含助手回复、变更摘要、新快照 ID、影响报告和总成本。
    - assistant_message: 回复给用户的助手消息文本
    - change_summary: 变更摘要（返回给前端展示）
    - new_snapshot_id: 新快照 ID（Phase 1 由调用方设置）
    - impact_report: 影响分析报告
    - cost_total: 本次编排的总 LLM 费用（美元）
    """

    assistant_message: str
    change_summary: ChangeSummary
    new_snapshot_id: UUID | None = None
    impact_report: ImpactReport
    cost_total: float = 0.0


class ChatOrchestrator:
    """
    一问一答模式编排器。

    接收用户消息，通过影响分析判定变更路径（冷启动/局部修改），
    调用 AgentRunner 执行目标 Agent，将结果应用到 IR 快照，
    最终生成变更摘要和助手回复。

    设计要点：
    - 不直接操作数据库（Phase 1），只做内存计算
    - SSE 事件驱动前端实时反馈
    - redis 参数可选，为 None 时跳过 SSE 发布
    """

    def __init__(self, db_session=None, user_id: UUID | None = None) -> None:
        """
        初始化编排器。

        参数:
            db_session: 数据库会话
            user_id: 当前用户 ID（用于加载用户 API Key 和模型偏好）
        """
        self._db_session = db_session
        self._user_id = user_id

    async def handle_message(
        self,
        project_id: UUID,
        conversation_id: UUID,
        branch_id: UUID,
        snapshot_id: UUID | None,
        user_message: str,
        ir_nodes: list[IRNodeData],
        ir_edges: list[IREdgeData],
        conversation_context: list | None = None,
        redis=None,
    ) -> ChatOrchestratorResult:
        """
        处理用户消息，执行完整的编排流程。

        流程：
        1. SSE: analysis_start
        2. 影响分析（ImpactAnalyzer）
        3. SSE: analysis_done
        4. 判断路径：冷启动 or 局部修改
        5. 执行 Agent 链
        6. SSE: apply_done
        7. 生成变更摘要
        8. 生成助手回复
        9. SSE: complete
        10. 返回 ChatOrchestratorResult

        参数:
            project_id: 项目 ID
            conversation_id: 会话 ID
            branch_id: 分支 ID
            snapshot_id: 当前快照 ID（可为 None）
            user_message: 用户输入的消息文本
            ir_nodes: 当前 IR 图中的所有节点
            ir_edges: 当前 IR 图中的所有边
            conversation_context: 对话上下文消息列表（可选）
            redis: Redis 连接（可选，为空则不发 SSE）

        返回:
            ChatOrchestratorResult
        """
        conv_id_str = str(conversation_id)

        if conversation_context is None:
            conversation_context = []

        try:
            return await self._execute(
                project_id=project_id,
                conversation_id=conversation_id,
                conv_id_str=conv_id_str,
                branch_id=branch_id,
                snapshot_id=snapshot_id,
                user_message=user_message,
                ir_nodes=ir_nodes,
                ir_edges=ir_edges,
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
                    affected_node_types=[],
                    affected_node_ids=[],
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
        snapshot_id: UUID | None,
        user_message: str,
        ir_nodes: list[IRNodeData],
        ir_edges: list[IREdgeData],
        conversation_context: list,
        redis,
    ) -> ChatOrchestratorResult:
        """
        编排核心执行逻辑（从 handle_message 中拆出，便于统一异常捕获）。

        参数同 handle_message，额外传入 conv_id_str 避免重复转换。
        """
        # ── 步骤 0a: 预加载用户 LLM 配置 ──
        self._user_config = None
        if self._user_id is not None and self._db_session is not None:
            try:
                from runtime_tools.llm.config import LLMConfig

                from api_app.application.services.settings_service import SettingsService

                svc = SettingsService(self._db_session)
                user_keys = await svc.get_user_api_keys_decrypted(self._user_id)
                pref = await svc.get_model_preference(self._user_id)
                self._user_config = LLMConfig.from_user(
                    user_api_keys=user_keys,
                    reasoning_model=pref.reasoning_model,
                    generation_model=pref.generation_model,
                )
            except Exception as exc:
                logger.warning("加载用户 LLM 配置失败，回退环境变量: %s", exc)

        # ── 步骤 0b: 验证 snapshot_id 与 branch 的 head_snapshot_id 一致 ──
        # 如果不一致，说明有其他操作修改了分支头（如回滚），记录警告
        # Phase 1 不阻断执行，只记录日志
        if self._db_session is not None and snapshot_id is not None:
            try:
                from platform_data.repositories.branch_repo import BranchRepository

                branch_repo = BranchRepository(self._db_session)
                branch = await branch_repo.get_by_id(branch_id)
                if branch is not None and branch.head_snapshot_id != snapshot_id:
                    logger.warning(
                        "快照一致性检查: branch.head_snapshot_id=%s != "
                        "传入 snapshot_id=%s, conversation=%s, branch=%s"
                        "（可能发生了回滚）",
                        branch.head_snapshot_id,
                        snapshot_id,
                        conv_id_str,
                        branch_id,
                    )
            except Exception as exc:
                # Phase 1 不阻断执行，仅记录异常
                logger.debug(
                    "快照一致性检查异常（不影响执行）: %s", exc
                )

        # ── 步骤 1: SSE 通知分析开始 ──
        await publish_chat_analysis_start(conv_id_str, redis=redis)

        # ── 步骤 2: 影响分析 ──
        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(user_message, ir_nodes, ir_edges)

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
        total_operations = 0
        agents_executed: list[str] = []
        all_warnings: list[str] = []

        # 用于最终结果的节点/边
        new_nodes: list[IRNodeData]
        new_edges: list[IREdgeData]

        if report.requires_cold_start:
            # ── 冷启动路径 ──
            new_nodes, new_edges, cost, ops_count, executed, warnings = (
                await self._run_cold_start(
                    project_id=project_id,
                    snapshot_id=snapshot_id,
                    user_message=user_message,
                    conv_id_str=conv_id_str,
                    redis=redis,
                )
            )
            total_cost += cost
            total_operations += ops_count
            agents_executed.extend(executed)
            all_warnings.extend(warnings)
        else:
            # ── 局部修改路径 ──
            new_nodes, new_edges, cost, ops_count, executed, warnings = (
                await self._run_incremental(
                    project_id=project_id,
                    snapshot_id=snapshot_id,
                    user_message=user_message,
                    ir_nodes=ir_nodes,
                    ir_edges=ir_edges,
                    conversation_context=conversation_context,
                    report=report,
                    conv_id_str=conv_id_str,
                    redis=redis,
                )
            )
            total_cost += cost
            total_operations += ops_count
            agents_executed.extend(executed)
            all_warnings.extend(warnings)

        # ── 步骤 5: SSE 通知 apply 完成 ──
        # Phase 1 不实际写 DB，只通知前端
        await publish_chat_apply_done(
            conv_id_str,
            new_snapshot_id=str(snapshot_id) if snapshot_id else "",
            operations_count=total_operations,
            redis=redis,
        )

        # ── 步骤 6: 生成变更摘要 ──
        affected_areas = self._translate_node_types(report.affected_node_types)
        change_summary = ChangeSummary(
            summary=self._build_summary_text(report, agents_executed, total_operations),
            affected_areas=affected_areas,
            operations_count=total_operations,
            agents_executed=agents_executed,
            warnings=all_warnings,
        )

        # ── 步骤 7: 生成助手回复文本 ──
        assistant_message = self._build_assistant_reply(
            report=report,
            change_summary=change_summary,
            agents_executed=agents_executed,
        )

        # ── 步骤 7.5: 检查是否需要压缩和决策抽取（不阻塞主流程） ──
        await self._try_compress_and_extract(
            branch_id=branch_id,
            conversation_id=conversation_id,
            project_id=project_id,
            snapshot_id=snapshot_id,
        )

        # ── 步骤 8: SSE 通知全部完成 ──
        await publish_chat_complete(
            conv_id_str,
            change_summary=change_summary.model_dump(mode="json"),
            redis=redis,
        )

        logger.info(
            "编排完成: conversation_id=%s, agents=%s, operations=%d, cost=%.4f",
            conv_id_str,
            agents_executed,
            total_operations,
            total_cost,
        )

        return ChatOrchestratorResult(
            assistant_message=assistant_message,
            change_summary=change_summary,
            impact_report=report,
            cost_total=total_cost,
        )

    async def _try_compress_and_extract(
        self,
        branch_id: UUID,
        conversation_id: UUID,
        project_id: UUID,
        snapshot_id: UUID | None,
    ) -> None:
        """尝试对当前分支做对话压缩和决策抽取。

        压缩或抽取失败不影响主流程，仅记录警告日志。

        参数:
            branch_id: 分支 ID
            conversation_id: 会话 ID
            project_id: 项目 ID
            snapshot_id: 当前快照 ID
        """
        try:
            from agents.analysis.decision_extractor import DecisionExtractor
            from agents.analysis.summary_generator import SummaryGenerator

            if self._db_session is None:
                return

            summary_gen = SummaryGenerator()
            summary = await summary_gen.compress_branch(
                db=self._db_session,
                branch_id=branch_id,
                conversation_id=conversation_id,
            )

            # 如果生成了 summary，触发决策抽取
            if summary is not None:
                extractor = DecisionExtractor()
                # 加载要抽取决策的消息
                from api_app.application.services.message_service import MessageService

                msg_service = MessageService(self._db_session)
                all_messages = await msg_service.list_by_branch(
                    branch_id, limit=100,
                )

                decisions = await extractor.extract_decisions(all_messages)
                if decisions and snapshot_id:
                    await extractor.write_to_ir(
                        db=self._db_session,
                        project_id=project_id,
                        snapshot_id=snapshot_id,
                        decisions=decisions,
                    )

                logger.info(
                    "对话压缩完成: conversation_id=%s, 决策数=%d",
                    conversation_id,
                    len(decisions),
                )
        except Exception as exc:
            # 压缩失败不影响主流程
            logger.warning("对话压缩/决策抽取失败: %s", exc)

    async def _run_cold_start(
        self,
        project_id: UUID,
        snapshot_id: UUID | None,
        user_message: str,
        conv_id_str: str,
        redis,
    ) -> tuple[list[IRNodeData], list[IREdgeData], float, int, list[str], list[str]]:
        """
        执行冷启动路径。

        创建 AgentRunner 实例，执行 ColdStartBootstrap。

        参数:
            project_id: 项目 ID
            snapshot_id: 快照 ID（可为 None，冷启动时使用占位 UUID）
            user_message: 用户消息
            conv_id_str: 会话 ID 字符串（用于 SSE）
            redis: Redis 连接

        返回:
            (new_nodes, new_edges, cost, operations_count, agents_executed, warnings)
        """
        from uuid import uuid4

        runner = self._create_agent_runner()

        # 冷启动需要一个 snapshot_id，如果调用方未传则生成占位 ID
        effective_snapshot_id = snapshot_id or uuid4()

        # SSE 通知冷启动的各个 Agent 阶段
        bootstrap = ColdStartBootstrap(runner=runner)

        # 逐步发布 SSE（ColdStartBootstrap 内部不发 SSE，我们在外面包一层）
        for agent_id in ColdStartBootstrap.COLD_START_AGENTS:
            await publish_chat_agent_start(conv_id_str, agent_id, redis=redis)

        start_time = time.monotonic()
        result = await bootstrap.bootstrap(
            project_id=project_id,
            snapshot_id=effective_snapshot_id,
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

        return (
            result.ir_nodes,
            result.ir_edges,
            0.0,
            result.operations_applied,
            result.agents_executed,
            result.warnings,
        )

    async def _run_incremental(
        self,
        project_id: UUID,
        snapshot_id: UUID | None,
        user_message: str,
        ir_nodes: list[IRNodeData],
        ir_edges: list[IREdgeData],
        conversation_context: list,
        report: ImpactReport,
        conv_id_str: str,
        redis,
    ) -> tuple[list[IRNodeData], list[IREdgeData], float, int, list[str], list[str]]:
        """
        执行局部修改路径。

        根据影响报告生成分层执行计划，逐层执行 Agent。

        参数:
            project_id: 项目 ID
            snapshot_id: 快照 ID
            user_message: 用户消息
            ir_nodes: 当前节点列表
            ir_edges: 当前边列表
            conversation_context: 对话上下文
            report: 影响分析报告
            conv_id_str: 会话 ID 字符串
            redis: Redis 连接

        返回:
            (new_nodes, new_edges, cost, operations_count, agents_executed, warnings)
        """
        from uuid import uuid4

        runner = self._create_agent_runner()
        selector = AgentSelector()

        # 生成分层执行计划
        execution_plan = selector.select(report)
        logger.info(
            "执行计划: %s (共 %d 层)",
            execution_plan,
            len(execution_plan),
        )

        current_nodes = list(ir_nodes)
        current_edges = list(ir_edges)
        total_cost = 0.0
        total_operations = 0
        agents_executed: list[str] = []
        all_warnings: list[str] = []

        effective_snapshot_id = snapshot_id or uuid4()

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
                snapshot_id=effective_snapshot_id,
                current_nodes=current_nodes,
                current_edges=current_edges,
                conversation_context=conversation_context,
                user_message=user_message,
                conv_id_str=conv_id_str,
                redis=redis,
            )

            # 处理每个 Agent 的结果（按层内顺序 apply，保证一致性）
            for agent_id, agent_result in layer_results:
                agents_executed.append(agent_id)

                if agent_result.warnings:
                    all_warnings.extend(agent_result.warnings)

                # 累加成本
                if agent_result.meta:
                    total_cost += agent_result.meta.total_cost

                # 如果有操作，应用到当前 IR
                if agent_result.operations:
                    try:
                        current_nodes, current_edges = apply_operations(
                            current_nodes,
                            current_edges,
                            agent_result.operations,
                        )
                        total_operations += len(agent_result.operations)
                    except ApplyError as exc:
                        warning_msg = f"{agent_id} 操作应用失败: {exc}"
                        logger.warning(warning_msg)
                        all_warnings.append(warning_msg)

        return (
            current_nodes,
            current_edges,
            total_cost,
            total_operations,
            agents_executed,
            all_warnings,
        )

    async def _execute_layer(
        self,
        runner,
        layer: list[str],
        project_id: UUID,
        snapshot_id: UUID,
        current_nodes: list[IRNodeData],
        current_edges: list[IREdgeData],
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
            snapshot_id: 快照 ID
            current_nodes: 当前节点列表
            current_edges: 当前边列表
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
                snapshot_id=snapshot_id,
                ir_nodes=current_nodes,
                ir_edges=current_edges,
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
                    operations=[],
                    warnings=[f"Agent {layer[i]} 执行异常: {result!s}"],
                )
                processed.append((layer[i], mock_result))
            else:
                processed.append(result)

        return processed

    def _create_agent_runner(self):
        """
        创建 AgentRunner 实例。

        如果有 user_id 和 db_session，则从数据库加载用户 API Key 和模型偏好，
        使用 LLMConfig.from_user() 构建配置；否则回退到环境变量。

        返回:
            AgentRunner 实例
        """
        from agents.configs.definitions import register_all_agents
        from agents.executors.runner import AgentRunner
        from runtime_tools.llm.config import LLMConfig
        from runtime_tools.llm.provider import LiteLLMProvider

        # 确保 Agent 已注册
        registry = register_all_agents()

        # 尝试加载用户配置
        config = None
        if self._user_id is not None and self._db_session is not None:
            try:
                # 注意：这里是同步上下文内调用，使用 run_sync 模式
                # 由于 _create_agent_runner 在 async 方法中被调用后立即使用，
                # 用户密钥已在 handle_message 开头预加载到 self._user_config
                config = self._user_config
            except AttributeError:
                pass

        if config is None:
            config = LLMConfig.from_env()

        # 创建 LLM Provider 和 Runner
        llm_provider = LiteLLMProvider(config=config)
        return AgentRunner(
            llm_provider=llm_provider,
            registry=registry,
        )

    @staticmethod
    def _translate_node_types(node_types: list[str]) -> list[str]:
        """
        将节点类型列表翻译为中文名称。

        参数:
            node_types: 节点类型英文标识列表

        返回:
            中文名称列表（未知类型保留原文）
        """
        return [
            NODE_TYPE_CN.get(nt, nt)
            for nt in node_types
        ]

    @staticmethod
    def _build_summary_text(
        report: ImpactReport,
        agents_executed: list[str],
        operations_count: int,
    ) -> str:
        """
        根据影响报告和执行结果生成一句话摘要。

        参数:
            report: 影响分析报告
            agents_executed: 实际执行的 Agent 列表
            operations_count: 操作总数

        返回:
            变更摘要文本
        """
        if report.requires_cold_start:
            return (
                f"冷启动完成：执行了 {len(agents_executed)} 个 Agent，"
                f"共 {operations_count} 个操作，建立了基础 IR 结构"
            )

        # 将 affected_node_types 翻译为中文
        areas_cn = [
            NODE_TYPE_CN.get(nt, nt)
            for nt in report.affected_node_types
        ]
        areas_text = "、".join(areas_cn) if areas_cn else "相关模块"

        return (
            f"已更新 {areas_text}：执行了 {len(agents_executed)} 个 Agent，"
            f"共 {operations_count} 个操作"
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
