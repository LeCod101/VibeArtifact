"""批量生成任务。

毕设全流程一键生成，由 API 层触发。
逐步调用 Agent 完成需求分析、架构设计、数据库、代码、文档等。
"""

from worker_app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.batch_generate", max_retries=1, time_limit=600)
def batch_generate(self, project_id: str, steps: list[str] | None = None):
    """毕设全流程批量生成。

    Args:
        project_id: 项目 UUID
        steps: 生成步骤列表，如 ['requirement', 'architecture', 'database', 'code', 'api_doc']
    """
    # Phase 2 占位实现，Phase 4 补全
    all_steps = steps or ["requirement", "architecture", "database", "code", "api_doc"]
    return {"project_id": project_id, "steps": all_steps, "status": "completed"}
