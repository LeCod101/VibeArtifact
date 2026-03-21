"""
Agent 单步执行 Celery 任务。

每个 agent 步骤作为独立的 Celery task 执行：
1. 更新步骤状态为 running
2. 从快照加载 IR 节点/边，组装 AgentInput
3. 调用 AgentRunner 执行 agent
4. 将 IR 操作应用到快照，创建新快照
5. 更新步骤状态为 completed / failed

超时限制：soft_time_limit=300（5 分钟）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
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
    snapshot_id: str,
    step_input_json: str = "{}",
) -> dict:
    """
    执行单个 Agent 步骤。

    Celery task，同步入口包装异步执行逻辑。
    - self: Celery task 实例（bind=True）
    - run_id: job_run ID（字符串形式的 UUID）
    - agent_id: 要执行的 agent 标识
    - snapshot_id: 当前 IR 快照 ID
    - step_input_json: 步骤输入的 JSON 字符串
    返回执行结果字典，包含 agent_id, status, snapshot_id, output_summary。
    """
    # 在 Celery worker 中运行异步代码
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _execute_agent_step_async(
                run_id=run_id,
                agent_id=agent_id,
                snapshot_id=snapshot_id,
                step_input_json=step_input_json,
            )
        )
    finally:
        loop.close()


async def _execute_agent_step_async(
    run_id: str,
    agent_id: str,
    snapshot_id: str,
    step_input_json: str,
) -> dict:
    """
    Agent 步骤的异步执行逻辑。

    完整流程：
    1. 更新 agent_run 状态为 running
    2. 从 DB 加载项目信息和当前快照 IR 数据
    3. 调用 AgentRunner 执行 agent
    4. 将 IR 操作应用到快照，创建新快照
    5. 更新状态为 completed，记录输出和 LLM 元信息
    6. 异常时标记为 failed

    - run_id: job_run ID
    - agent_id: agent 标识
    - snapshot_id: 快照 ID
    - step_input_json: 步骤输入 JSON
    返回包含 agent_id, status, snapshot_id, output_summary 的字典。
    """
    from worker_app.orchestrator.run_manager import RunManager, RunStatus

    manager = RunManager()
    run_uuid = UUID(run_id)
    snapshot_uuid = UUID(snapshot_id)

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

        # 步骤 2：解析输入并获取项目信息
        scope_draft = _parse_input(step_input_json)

        # 从 run 记录获取 project_id
        run_status = await manager.get_run_status(run_uuid)
        project_id = UUID(run_status["project_id"])

        # 步骤 3：调用真实 AgentRunner 执行
        result = await _run_agent(
            agent_id=agent_id,
            project_id=project_id,
            snapshot_id=snapshot_uuid,
            task_description=json.dumps(scope_draft, ensure_ascii=False),
        )

        new_snapshot_id = result["new_snapshot_id"]
        output_summary = result["output_summary"]

        # 构建 update_step_status 的额外参数（LLM 元信息）
        meta_kwargs: dict = {}
        if result.get("meta"):
            meta = result["meta"]
            meta_kwargs = {
                "model": meta.get("model"),
                "provider": meta.get("provider"),
                "prompt_tokens": meta.get("prompt_tokens"),
                "completion_tokens": meta.get("completion_tokens"),
                "total_cost": meta.get("total_cost"),
                "latency_ms": meta.get("latency_ms"),
            }

        # 步骤 4：更新状态为 completed
        await manager.update_step_status(
            run_id=run_uuid,
            agent_id=agent_id,
            status=RunStatus.COMPLETED,
            output_payload=output_summary,
            **meta_kwargs,
        )

        # 发布 SSE 步骤完成事件
        duration_ms = int((time.monotonic() - start_time_ms) * 1000)
        await publish_step_complete(run_id, agent_id, duration_ms)

        logger.info(
            "Agent 步骤执行完成: run_id=%s, agent_id=%s, new_snapshot=%s",
            run_id, agent_id, new_snapshot_id,
        )

        return {
            "agent_id": agent_id,
            "status": "completed",
            "snapshot_id": str(new_snapshot_id),
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


async def _run_agent(
    agent_id: str,
    project_id: UUID,
    snapshot_id: UUID,
    task_description: str,
) -> dict:
    """
    调用真实 AgentRunner 执行 agent 并写回快照。

    完整流程：
    1. 创建 AgentRunner（复用 ChatOrchestrator 的模式）
    2. 从 DB 加载当前快照的 IR 节点/边
    3. 组装 AgentInput
    4. 调用 runner.run()
    5. 将返回的 operations 应用到 IR 快照
    6. 创建新快照保存结果
    7. 对 LLM 输出做 JSON 容错处理

    - agent_id: agent 标识
    - project_id: 项目 ID
    - snapshot_id: 当前快照 ID
    - task_description: 任务描述（scope_draft JSON 字符串）
    返回包含 new_snapshot_id, output_summary, meta 的字典。
    """
    from agents.configs.definitions import register_all_agents
    from agents.executors.runner import AgentRunner
    from agents.schemas.base import AgentInput
    from ir_core.operations.apply import apply_operations
    from runtime_tools.llm.provider import LiteLLMProvider

    from worker_app.orchestrator.snapshot_writer import SnapshotWriter

    # 创建 AgentRunner
    registry = register_all_agents()
    llm_provider = LiteLLMProvider()
    runner = AgentRunner(
        llm_provider=llm_provider,
        registry=registry,
    )

    # 从 DB 加载当前快照的 IR 数据
    writer = SnapshotWriter()
    current_nodes, current_edges = await writer.load_snapshot(snapshot_id)

    # 组装 AgentInput
    agent_input = AgentInput(
        project_id=project_id,
        snapshot_id=snapshot_id,
        ir_nodes=current_nodes,
        ir_edges=current_edges,
        conversation_context=[],
        task_description=task_description,
        extra={},
    )

    # 调用 AgentRunner 执行
    run_result = await runner.run(agent_id, agent_input)

    # 提取 LLM 元信息
    meta_dict = None
    if run_result.meta:
        meta_dict = {
            "model": run_result.meta.model,
            "provider": run_result.meta.provider,
            "prompt_tokens": run_result.meta.prompt_tokens,
            "completion_tokens": run_result.meta.completion_tokens,
            "total_cost": run_result.meta.total_cost,
            "latency_ms": run_result.meta.latency_ms,
        }

    # 将 operations 应用到当前 IR 快照
    operations = run_result.operations or []
    if operations:
        new_nodes, new_edges = apply_operations(
            current_nodes, current_edges, operations,
        )
    else:
        # 没有操作时，快照内容不变
        new_nodes, new_edges = current_nodes, current_edges

    # 创建新快照保存结果
    new_snapshot_id = await writer.write_snapshot(
        project_id=project_id,
        parent_snapshot_id=snapshot_id,
        nodes=new_nodes,
        edges=new_edges,
    )

    # 构建输出摘要
    output_summary = {
        "agent_id": agent_id,
        "snapshot_id": str(new_snapshot_id),
        "operations_count": len(operations),
        "nodes_count": len(new_nodes),
        "edges_count": len(new_edges),
        "warnings": run_result.warnings or [],
    }

    return {
        "new_snapshot_id": new_snapshot_id,
        "output_summary": output_summary,
        "meta": meta_dict,
    }
