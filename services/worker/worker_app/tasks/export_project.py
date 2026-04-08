"""项目导出任务。

从数据库读取产物，经收集器与 ZIP 打包后写入本地存储，
并回写导出记录；由 API 触发 Celery 异步执行。
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from worker_app.celery_app import celery_app

logger = logging.getLogger(__name__)

# 懒加载同步引擎，避免 import 阶段依赖环境变量
_sync_engine = None


def _get_sync_engine():
    """
    获取用于 Celery 的同步数据库引擎。

    DATABASE_URL 与 API 一致时通常为 postgresql+asyncpg，需改为 psycopg 同步驱动。
    """
    global _sync_engine
    if _sync_engine is None:
        raw_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://vibe:vibe@localhost:5432/vibeartifact",
        )
        sync_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        _sync_engine = create_engine(sync_url, pool_pre_ping=True)
    return _sync_engine


@celery_app.task(bind=True, name="tasks.export_project", max_retries=2, time_limit=300)
def export_project(
    self,
    export_id: str,
    project_id: str,
    export_format: str = "zip",
) -> dict[str, Any]:
    """
    导出项目产物为 ZIP（export_format 预留，当前仅实现 zip）。

    - export_id: artifact_exports 主键
    - project_id: 项目 UUID 字符串
    - export_format: zip / pdf（pdf 未实现）
    """
    from platform_data.models.artifact import Artifact, ArtifactExport
    from platform_data.models.project import Project
    from runtime_tools.exporters.collector import ArtifactCollector
    from runtime_tools.exporters.storage import save_zip
    from runtime_tools.exporters.zip_packer import ZipPacker

    _ = export_format

    try:
        engine = _get_sync_engine()
        export_uuid = uuid.UUID(export_id)
        project_uuid = uuid.UUID(project_id)

        with Session(engine) as db:
            project = db.execute(select(Project).where(Project.id == project_uuid)).scalar_one_or_none()
            if project is None:
                logger.error("项目不存在: %s", project_id)
                return {"status": "failed", "error": "项目不存在"}

            artifacts = db.execute(select(Artifact).where(Artifact.project_id == project_uuid)).scalars().all()

            if not artifacts:
                logger.info("项目无产物: %s", project_id)
                export_record = db.get(ArtifactExport, export_uuid)
                if export_record:
                    export_record.file_url = None
                    export_record.file_size_bytes = None
                    db.commit()
                return {"status": "completed", "files": 0}

            collector = ArtifactCollector()
            files = collector.collect_from_artifacts(list(artifacts))

            packer = ZipPacker(project.name, files)
            zip_bytes = packer.pack_to_bytes()

            save_zip(export_id, zip_bytes)

            export_record = db.get(ArtifactExport, export_uuid)
            if export_record:
                export_record.file_url = f"/api/v1/exports/{export_id}/download"
                export_record.file_size_bytes = len(zip_bytes)
                db.commit()

            logger.info(
                "导出成功: %s, %d 个文件, %d bytes",
                export_id,
                len(files),
                len(zip_bytes),
            )
            return {
                "status": "completed",
                "export_id": export_id,
                "files": len(files),
                "size": len(zip_bytes),
            }

    except Exception as exc:
        logger.exception("导出失败: %s", export_id)
        raise self.retry(exc=exc, countdown=30)
