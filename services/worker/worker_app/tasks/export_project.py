"""项目导出任务。

异步将项目产物打包为 ZIP 或 PDF 格式，
由 API 层触发，完成后通过 Redis 通知前端。
"""

from worker_app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.export_project", max_retries=2, time_limit=300)
def export_project(self, project_id: str, export_format: str = "zip"):
    """导出项目为 zip/pdf。

    Args:
        project_id: 项目 UUID
        export_format: 导出格式，zip 或 pdf
    """
    # Phase 2 占位实现，Phase 4 补全
    return {"project_id": project_id, "format": export_format, "status": "completed"}
