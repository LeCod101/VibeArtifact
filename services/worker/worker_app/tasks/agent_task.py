"""
Agent 单步执行 Celery 任务。

每个 agent 步骤作为独立的 Celery task 执行：
1. 更新步骤状态为 running
2. 组装 StepInput
3. 调用 AgentRunner 执行 agent
4. 产物文件写入工作区（workspace_files）
5. 更新步骤状态为 completed / failed

超时限制：soft_time_limit=300（5 分钟）
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded

from worker_app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.execute_agent_step",
    bind=True,
    soft_time_limit=300,
    max_retries=0,
    acks_late=True,
)
def execute_agent_step(
    self,
    run_id: str,
    agent_id: str,
    step_input_json: str = "{}",
) -> dict:
    """
    执行单个 Agent 步骤。

    Celery task，同步入口包装异步执行逻辑。
    - self: Celery task 实例（bind=True）
    - run_id: job_run ID（字符串形式的 UUID）
    - agent_id: 要执行的 agent 标识
    - step_input_json: 步骤输入的 JSON 字符串
    返回执行结果字典，包含 agent_id, status, output_summary。
    """
    # 在 Celery worker 中运行异步代码
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _execute_agent_step_async(
                run_id=run_id,
                agent_id=agent_id,
                step_input_json=step_input_json,
            )
        )
    finally:
        loop.close()


async def _execute_agent_step_async(
    run_id: str,
    agent_id: str,
    step_input_json: str,
) -> dict:
    """
    Agent 步骤的异步执行逻辑。

    完整流程：
    1. 更新 agent_run 状态为 running
    2. 解析 step_input
    3. 调用 AgentRunner 执行
    4. 更新状态为 completed，记录输出
    5. 异常时标记为 failed

    - run_id: job_run ID
    - agent_id: agent 标识
    - step_input_json: 步骤输入 JSON
    返回包含 agent_id, status, output_summary 的字典。
    """
    from worker_app.orchestrator.run_manager import RunManager, RunStatus

    manager = RunManager()
    run_uuid = UUID(run_id)

    # 记录执行开始时间，用于计算 duration_ms
    import time

    # 导入 SSE 事件发布函数
    from api_app.api.sse.publisher import (
        publish_step_complete,
        publish_step_failed,
        publish_step_start,
    )
    start_time_ms = time.monotonic()

    try:
        # 步骤 1：标记为 running
        await manager.update_step_status(
            run_id=run_uuid,
            agent_id=agent_id,
            status=RunStatus.RUNNING,
        )

        # 发布 SSE 步骤开始事件
        await publish_step_start(run_id, agent_id)

        logger.info(
            "Agent 步骤开始执行: run_id=%s, agent_id=%s",
            run_id, agent_id,
        )

        # 步骤 2：解析输入
        scope_draft = _parse_input(step_input_json)

        # 步骤 3：调用 Agent 执行器并写入工作区
        output_summary = await _run_agent_and_store(
            run_id=run_id,
            agent_id=agent_id,
            scope_draft=scope_draft,
        )

        # 步骤 4：更新状态为 completed
        await manager.update_step_status(
            run_id=run_uuid,
            agent_id=agent_id,
            status=RunStatus.COMPLETED,
            output_payload=output_summary,
        )

        # 发布 SSE 步骤完成事件
        duration_ms = int((time.monotonic() - start_time_ms) * 1000)
        await publish_step_complete(run_id, agent_id, duration_ms)

        logger.info(
            "Agent 步骤执行完成: run_id=%s, agent_id=%s",
            run_id, agent_id,
        )

        return {
            "agent_id": agent_id,
            "status": "completed",
            "output_summary": output_summary,
        }

    except SoftTimeLimitExceeded:
        # 超时处理
        error_msg = f"Agent '{agent_id}' 执行超时（5 分钟限制）"
        logger.error(error_msg)
        await manager.update_step_status(
            run_id=run_uuid,
            agent_id=agent_id,
            status=RunStatus.FAILED,
            error_message=error_msg,
        )
        # 发布 SSE 步骤失败事件
        await publish_step_failed(run_id, agent_id, error_msg)
        return {
            "agent_id": agent_id,
            "status": "failed",
            "error": error_msg,
        }

    except Exception as exc:
        # 通用异常处理
        error_msg = f"Agent '{agent_id}' 执行失败: {exc!s}"
        logger.exception(error_msg)
        await manager.update_step_status(
            run_id=run_uuid,
            agent_id=agent_id,
            status=RunStatus.FAILED,
            error_message=error_msg,
        )
        # 发布 SSE 步骤失败事件
        await publish_step_failed(run_id, agent_id, error_msg)
        return {
            "agent_id": agent_id,
            "status": "failed",
            "error": error_msg,
        }


def _parse_input(step_input_json: str) -> dict:
    """
    解析步骤输入 JSON。

    安全解析，JSON 无效时返回空字典。
    - step_input_json: JSON 字符串
    返回解析后的字典。
    """
    try:
        return json.loads(step_input_json)
    except (json.JSONDecodeError, TypeError):
        return {}


async def _run_agent_and_store(
    run_id: str,
    agent_id: str,
    scope_draft: dict,
) -> dict:
    """
    执行单个 Agent 并将产物文件写入工作区。

    真实分发：
    - 配对 agent（backend/frontend/doc/diagram，见 REVIEW_PAIRS）走
      ConversationGraph author↔reviewer 多轮循环，轮次记录落库
      conversation_turns，轮次事件经 SSE 发布
    - 其余单轮 agent 走 AgentRunner 一次调用

    未配置任何 LLM API Key 时退化为占位实现，保证本地/CI 无 Key
    环境仍可跑通编排全链路。

    - run_id: job_run ID
    - agent_id: agent 标识
    - scope_draft: scope_draft 数据
    返回输出摘要字典。
    """
    from runtime_tools.llm.config import LLMConfig

    llm_config = LLMConfig.from_env()
    if not llm_config.api_keys:
        logger.warning(
            "未配置任何 LLM API Key，Agent '%s' 使用占位执行", agent_id,
        )
        return _placeholder_summary(agent_id)

    from agents.configs.definitions import REVIEW_PAIRS, register_all_agents
    from agents.executors.runner import AgentRunner
    from agents.schemas.base import AgentInput
    from platform_data.repositories.review_turn_repo import (
        ReviewTurnRepository,
    )
    from platform_data.repositories.workspace_repo import WorkspaceRepository
    from runtime_tools.llm.provider import LangChainProvider

    from worker_app.orchestrator.run_manager import (
        RunManager,
        get_worker_session_factory,
    )

    # 查询 run 归属项目，构建 AgentInput
    manager = RunManager()
    run_info = await manager.get_run_status(UUID(run_id))
    project_id = UUID(run_info["project_id"])

    registry = register_all_agents()
    runner = AgentRunner(
        llm_provider=LangChainProvider(),
        registry=registry,
        llm_config=llm_config,
    )

    task_description = scope_draft.get("task_description") or json.dumps(
        scope_draft, ensure_ascii=False,
    )

    agent_input = AgentInput(
        project_id=project_id,
        run_id=UUID(run_id),
        workspace_files=[],
        upstream_outputs={},
        conversation_context=[],
        task_description=task_description,
        extra=scope_draft,
    )

    reviewer_id = REVIEW_PAIRS.get(agent_id)
    turns: list[dict] = []
    warnings: list[str] = []
    summary_extra: dict = {}

    if reviewer_id is not None:
        # ── 配对 agent：author↔reviewer 多轮循环 ──
        from agents.executors.conversation_graph import ConversationGraph

        graph = ConversationGraph(
            runner=runner,
            on_event=_make_review_event_publisher(run_id),
        )
        pair_result = await graph.run_pair(
            author_id=agent_id,
            reviewer_id=reviewer_id,
            agent_input=agent_input,
        )
        files = list(pair_result.files)
        warnings = list(pair_result.warnings)
        turns = [t.model_dump(mode="json") for t in pair_result.turns]
        summary_extra = {
            "review_rounds": pair_result.rounds,
            "review_approved": pair_result.approved,
        }
    else:
        # ── 单轮 agent ──
        result = await runner.run(agent_id, agent_input)
        files = list(result.files)
        warnings = list(result.warnings)

    # 产物文件与轮次记录写入数据库
    for f in files:
        f["agent"] = agent_id

    files_written = 0
    if files or turns:
        session_factory = get_worker_session_factory()
        async with session_factory() as session:
            if files:
                workspace_repo = WorkspaceRepository(session)
                files_written = await workspace_repo.write_files(
                    UUID(run_id), files,
                )
            if turns:
                turn_repo = ReviewTurnRepository(session)
                await turn_repo.write_turns(UUID(run_id), turns)
            await session.commit()

    logger.info(
        "Agent '%s' 执行完成: %d 个文件写入工作区, %d 条轮次记录",
        agent_id, files_written, len(turns),
    )

    return {
        "agent_id": agent_id,
        "files_written": files_written,
        "warnings": warnings,
        **summary_extra,
    }


def _make_review_event_publisher(run_id: str):
    """
    构建评审轮次事件的 SSE 发布回调。

    - run_id: job_run ID（用作 SSE 频道标识）
    返回 async (event, payload) -> None 回调。
    """
    from api_app.api.sse.publisher import publish_step_event

    async def _publish(event: str, payload: dict) -> None:
        await publish_step_event(run_id, event, payload)

    return _publish


def _placeholder_summary(agent_id: str) -> dict:
    """
    无 LLM Key 环境下的占位执行结果。

    - agent_id: agent 标识
    返回模拟的输出摘要字典。
    """
    return {
        "agent_id": agent_id,
        "placeholder": True,
        "message": f"Agent '{agent_id}' 占位执行完成（未配置 LLM API Key）",
    }
