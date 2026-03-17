"""
DAG 编排 Celery 任务。

顶层编排任务，负责：
1. 初始化 AgentRegistry
2. 解析 DAG 生成执行计划
3. 创建 run 记录
4. 按层级调度 agent_task
5. 等待所有层级完成
6. 标记 run 为完成或失败

超时限制：soft_time_limit=1800（30 分钟）
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
    name="tasks.run_delegated_dag",
    bind=True,
    soft_time_limit=1800,
    max_retries=0,
    acks_late=True,
)
def run_delegated_dag(
    self,
    run_id: str | None = None,
    project_id: str = "",
    snapshot_id: str = "",
    scope_draft_json: str = "{}",
) -> dict:
    """
    执行完整的 DAG 编排。

    Celery task，同步入口包装异步执行逻辑。
    - self: Celery task 实例（bind=True）
    - run_id: 预创建的 run ID（可选，为 None 时自动创建）
    - project_id: 项目 ID
    - snapshot_id: 快照 ID
    - scope_draft_json: 初始 scope_draft JSON
    返回执行结果字典。
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            _run_delegated_dag_async(
                run_id=run_id,
                project_id=project_id,
                snapshot_id=snapshot_id,
                scope_draft_json=scope_draft_json,
            )
        )
    finally:
        loop.close()


async def _run_delegated_dag_async(
    run_id: str | None,
    project_id: str,
    snapshot_id: str,
    scope_draft_json: str,
) -> dict:
    """
    DAG 编排的异步执行逻辑。

    完整流程：
    1. 初始化 AgentRegistry
    2. 构建执行计划（分层 DAG）
    3. 创建 run 记录（如果未预创建）
    4. 标记 run 为 running
    5. 按层级逐层调度 agent 执行
    6. 所有层完成后标记 run 为 completed
    7. 任何异常标记 run 为 failed

    - run_id: 预创建的 run ID
    - project_id: 项目 ID
    - snapshot_id: 快照 ID
    - scope_draft_json: 初始 scope_draft JSON
    返回最终执行结果字典。
    """
    from agents.configs.definitions import register_all_agents

    from worker_app.orchestrator.dag import build_execution_plan
    from worker_app.orchestrator.run_manager import RunManager

    manager = RunManager()

    # 预初始化 run_uuid，防止异常分支中出现 UnboundLocalError
    run_uuid: UUID | None = None

    try:
        # 步骤 1：初始化 AgentRegistry
        registry = register_all_agents()

        # 步骤 2：构建执行计划
        execution_plan = build_execution_plan(registry)
        all_agent_ids = [
            agent_id
            for layer in execution_plan
            for agent_id in layer
        ]

        logger.info(
            "DAG 执行计划: %s (共 %d 层, %d 个 agent)",
            execution_plan,
            len(execution_plan),
            len(all_agent_ids),
        )

        # 步骤 3：创建 run 记录
        project_uuid = UUID(project_id)
        snapshot_uuid = UUID(snapshot_id)

        if run_id is None:
            scope_draft = _parse_json(scope_draft_json)
            created_run_id = await manager.create_run(
                project_id=project_uuid,
                snapshot_id=snapshot_uuid,
                agent_ids=all_agent_ids,
                input_payload=scope_draft,
            )
            run_uuid = created_run_id
        else:
            run_uuid = UUID(run_id)

        # 步骤 4：标记为 running
        await manager.mark_run_started(run_uuid)

        # 步骤 5：按层级逐层执行
        completed_results: list[dict] = []

        for layer_idx, layer in enumerate(execution_plan):
            logger.info(
                "执行第 %d/%d 层: %s",
                layer_idx + 1,
                len(execution_plan),
                layer,
            )

            # 调度当前层级的 agent
            layer_results = await _execute_layer(
                run_id=str(run_uuid),
                layer=layer,
                snapshot_id=snapshot_id,
                scope_draft_json=scope_draft_json,
            )

            # 检查是否有失败的步骤
            for result in layer_results:
                if result.get("status") == "failed":
                    error_msg = (
                        f"第 {layer_idx + 1} 层 "
                        f"agent '{result.get('agent_id')}' 执行失败: "
                        f"{result.get('error', '未知错误')}"
                    )
                    logger.error(error_msg)
                    await manager.mark_run_failed(run_uuid, error_msg)
                    return {
                        "run_id": str(run_uuid),
                        "status": "failed",
                        "error": error_msg,
                        "completed_layers": layer_idx,
                        "results": completed_results,
                    }

            completed_results.extend(layer_results)

        # 步骤 6：Gate 检查 + 修复回路（M6 新增）
        # 从数据库加载最新快照节点，运行三道门禁
        from api_app.api.sse.publisher import publish_needs_attention
        from runtime_tools.gates.repair_loop import RepairLoop

        repair_loop = RepairLoop(manager=manager, run_id=run_uuid)
        repair_result = await repair_loop.run_gates_and_repair(
            snapshot_id=snapshot_id,
            scope_draft_json=scope_draft_json,
            project_name=str(run_uuid),
        )

        if repair_result.needs_attention:
            # Gate 失败且修复无效，推送 SSE 通知并终止
            logger.warning(
                "Gate 检查失败且修复无效，标记 needs_attention: run_id=%s",
                str(run_uuid),
            )
            await publish_needs_attention(
                run_id=str(run_uuid),
                gate_result=repair_result.gate_suite.to_dict(),
            )
            return {
                "run_id": str(run_uuid),
                "status": "needs_attention",
                "gate_result": repair_result.gate_suite.to_dict(),
                "results": completed_results,
            }

        # 步骤 7：标记完成
        await manager.mark_run_completed(
            run_uuid,
            output_payload={
                "total_agents": len(all_agent_ids),
                "total_layers": len(execution_plan),
                "gate_passed": True,
                "gate_repaired": repair_result.repaired,
            },
        )

        logger.info(
            "DAG 编排完成: run_id=%s, 共 %d 层 %d 个 agent",
            str(run_uuid),
            len(execution_plan),
            len(all_agent_ids),
        )

        return {
            "run_id": str(run_uuid),
            "status": "completed",
            "total_layers": len(execution_plan),
            "total_agents": len(all_agent_ids),
            "results": completed_results,
        }

    except SoftTimeLimitExceeded:
        error_msg = "DAG 编排超时（30 分钟限制）"
        logger.error(error_msg)
        # 优先使用已赋值的 run_uuid，其次尝试解析传入的 run_id
        target_id = run_uuid if run_uuid is not None else (UUID(run_id) if run_id else None)
        if target_id is not None:
            await manager.mark_run_failed(target_id, error_msg)
        return {"status": "failed", "error": error_msg}

    except Exception as exc:
        error_msg = f"DAG 编排失败: {exc!s}"
        logger.exception(error_msg)
        # 优先使用已赋值的 run_uuid，其次尝试解析传入的 run_id
        target_id = run_uuid if run_uuid is not None else (UUID(run_id) if run_id else None)
        if target_id is not None:
            await manager.mark_run_failed(target_id, error_msg)
        return {"status": "failed", "error": error_msg}


async def _execute_layer(
    run_id: str,
    layer: list[str],
    snapshot_id: str,
    scope_draft_json: str,
) -> list[dict]:
    """
    执行一个层级中的所有 agent。

    对于单 agent 层，直接调用 execute_agent_step。
    对于多 agent 层，使用 asyncio.gather 并行调用。

    Phase 1 简化实现：直接调用异步执行函数，不经过 Celery 消息队列。
    M5 阶段 2 将改为通过 Celery group 分发到多 worker。

    - run_id: job_run ID
    - layer: 当前层级的 agent_id 列表
    - snapshot_id: 快照 ID
    - scope_draft_json: scope_draft JSON
    返回每个 agent 的执行结果列表。
    """
    from worker_app.tasks.agent_task import _execute_agent_step_async

    if len(layer) == 1:
        # 单 agent，直接执行
        result = await _execute_agent_step_async(
            run_id=run_id,
            agent_id=layer[0],
            snapshot_id=snapshot_id,
            step_input_json=scope_draft_json,
        )
        return [result]

    # 多 agent，并行执行
    tasks = [
        _execute_agent_step_async(
            run_id=run_id,
            agent_id=agent_id,
            snapshot_id=snapshot_id,
            step_input_json=scope_draft_json,
        )
        for agent_id in layer
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 将异常转换为失败结果
    processed: list[dict] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append({
                "agent_id": layer[i],
                "status": "failed",
                "error": str(result),
            })
        else:
            processed.append(result)

    return processed


def _parse_json(json_str: str) -> dict:
    """
    安全解析 JSON 字符串。

    解析失败时返回空字典。
    - json_str: JSON 字符串
    返回解析后的字典。
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}
