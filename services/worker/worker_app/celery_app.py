import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery(
    "vibeartifact",
    broker=broker_url,
    backend=result_backend,
    # 显式列出任务模块，确保 worker 启动时加载所有任务
    include=[
        "worker_app.tasks.ping",
        "worker_app.tasks.agent_task",
        "worker_app.tasks.orchestrate",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
