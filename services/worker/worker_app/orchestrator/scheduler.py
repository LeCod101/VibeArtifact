"""
DAG 调度器模块。

接收 DAG 解析器生成的分层执行计划，
将其翻译为 Celery chain + group 编排结构。

层级间串行（chain），同层内并行（group），
单 agent 直接下发为独立 task。
"""

from __future__ import annotations

from celery import chain, group
from celery.result import AsyncResult

from worker_app.orchestrator.dag import build_execution_plan


class DAGScheduler:
    """
    DAG 调度器。

    将分层执行计划翻译为 Celery 工作流并提交执行。
    """

    def schedule_run(
        self,
        run_id: str,
        execution_plan: list[list[str]],
        snapshot_id: str,
        scope_draft_json: str = "{}",
    ) -> AsyncResult:
        """
        调度一次 DAG 运行。

        将分层执行计划翻译为 Celery chain(group(...), group(...), ...)
        并提交执行。

        - run_id: 本次运行的唯一标识（job_runs.id）
        - execution_plan: 分层执行计划，List[List[str]]
        - snapshot_id: 当前 IR 快照 ID
        - scope_draft_json: 初始输入的 JSON 字符串
        返回 Celery AsyncResult，可用于查询最终状态。
        """
        # 延迟导入，避免循环依赖（task 文件中也会导入 orchestrator）
        from worker_app.tasks.agent_task import execute_agent_step

        layer_signatures = []

        for layer in execution_plan:
            if len(layer) == 1:
                # 单个 agent，直接作为 task signature
                sig = execute_agent_step.s(
                    run_id=run_id,
                    agent_id=layer[0],
                    snapshot_id=snapshot_id,
                    step_input_json=scope_draft_json,
                )
                layer_signatures.append(sig)
            else:
                # 多个 agent，组成 group 并行执行
                sigs = [
                    execute_agent_step.s(
                        run_id=run_id,
                        agent_id=agent_id,
                        snapshot_id=snapshot_id,
                        step_input_json=scope_draft_json,
                    )
                    for agent_id in sorted(layer)
                ]
                layer_signatures.append(group(sigs))

        # 将所有层级用 chain 串联
        workflow = chain(*layer_signatures)

        # 提交执行
        result = workflow.apply_async()
        return result


def schedule_from_registry(
    run_id: str,
    snapshot_id: str,
    scope_draft_json: str = "{}",
) -> AsyncResult:
    """
    便捷函数：从注册表构建执行计划并直接调度。

    - run_id: 运行 ID
    - snapshot_id: 快照 ID
    - scope_draft_json: 初始 scope_draft JSON
    返回 Celery AsyncResult。
    """
    plan = build_execution_plan()
    scheduler = DAGScheduler()
    return scheduler.schedule_run(
        run_id=run_id,
        execution_plan=plan,
        snapshot_id=snapshot_id,
        scope_draft_json=scope_draft_json,
    )
