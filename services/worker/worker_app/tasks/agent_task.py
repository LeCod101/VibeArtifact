"""
Agent 单步执行 Celery 任务。

每个 agent 步骤作为独立的 Celery task 执行：
1. 更新步骤状态为 running
2. 组装 StepInput
3. 调用 AgentRunner 执行 agent
4. Translator 写入 IR
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
    返回执行结果字典，包含 agent_id, status, output_summary。
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
    2. 解析 step_input
    3. 调用 AgentRunner 执行
    4. 更新状态为 completed，记录输出
    5. 异常时标记为 failed

    - run_id: job_run ID
    - agent_id: agent 标识
    - snapshot_id: 快照 ID
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

        # 步骤 3：调用 Agent 执行器
        # Phase 1 占位实现 —— 实际的 AgentRunner 调用在 M5 阶段 2 接入
        # 当前直接返回模拟结果
        output_summary = await _run_agent_placeholder(
            agent_id=agent_id,
            snapshot_id=snapshot_id,
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


async def _run_agent_placeholder(
    agent_id: str,
    snapshot_id: str,
    scope_draft: dict,
) -> dict:
    """
    Agent 执行占位实现。

    Phase 1 阶段的桩函数，返回模拟结果。
    M5 阶段 2 将替换为真正的 AgentRunner 调用：
    1. 从 AgentRegistry 获取 AgentConfig
    2. 组装 AgentInput
    3. 调用 AgentRunner.run()
    4. 通过 Translator 写入 IR 快照

    - agent_id: agent 标识
    - snapshot_id: 快照 ID
    - scope_draft: scope_draft 数据
    返回模拟的输出摘要字典。
    """
    return {
        "agent_id": agent_id,
        "snapshot_id": snapshot_id,
        "placeholder": True,
        "message": f"Agent '{agent_id}' 占位执行完成，等待 M5 阶段 2 接入真实执行器",
    }
