"""项目管理工具。

提供项目文件浏览、读取、搜索和导出能力。
通过 ToolContext 读取 artifacts 表数据。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from agents.tools.base import tool

if TYPE_CHECKING:
    from agents.tools.context import ToolContext


@tool
async def list_files(
    _ctx: "ToolContext | None" = None,
) -> dict:
    """列出当前项目中的所有 Artifact 文件。"""
    if _ctx is None:
        return {"files": [], "count": 0}

    from platform_data.models.artifact import Artifact

    # 每个文件只取最新版本（version_num 最大的）
    latest_version = (
        select(
            Artifact.title,
            func.max(Artifact.version_num).label("max_ver"),
        )
        .where(Artifact.project_id == _ctx.project_id)
        .group_by(Artifact.title)
        .subquery()
    )

    stmt = (
        select(Artifact)
        .join(
            latest_version,
            (Artifact.title == latest_version.c.title)
            & (Artifact.version_num == latest_version.c.max_ver),
        )
        .where(Artifact.project_id == _ctx.project_id)
        .order_by(Artifact.updated_at.desc())
    )
    result = await _ctx.db.execute(stmt)
    artifacts = result.scalars().all()

    files = [
        {
            "id": str(a.id),
            "title": a.title,
            "file_path": a.file_path or "",
            "language": a.language or "",
            "artifact_type": a.artifact_type,
            "version": a.version_num,
            "updated_at": a.updated_at.isoformat() if a.updated_at else "",
        }
        for a in artifacts
    ]

    return {"files": files, "count": len(files)}


@tool
async def read_file(
    artifact_id: str,
    _ctx: "ToolContext | None" = None,
) -> dict:
    """读取指定 Artifact 的完整内容。

    Args:
        artifact_id: Artifact ID
    """
    if _ctx is None:
        return {"error": "无法读取文件（缺少上下文）"}

    from platform_data.models.artifact import Artifact

    stmt = select(Artifact).where(Artifact.id == UUID(artifact_id))
    result = await _ctx.db.execute(stmt)
    artifact = result.scalar_one_or_none()

    if artifact is None:
        return {"error": f"未找到 Artifact: {artifact_id}"}

    return {
        "id": str(artifact.id),
        "title": artifact.title,
        "artifact_type": artifact.artifact_type,
        "language": artifact.language or "",
        "file_path": artifact.file_path or "",
        "version": artifact.version_num,
        "content": artifact.content,
    }


@tool
async def search_code(
    query: str,
    _ctx: "ToolContext | None" = None,
) -> dict:
    """在当前项目的代码和文档中搜索匹配的内容。

    Args:
        query: 搜索关键词或模式
    """
    if _ctx is None:
        return {"results": [], "count": 0}

    from platform_data.models.artifact import Artifact

    _MAX_RESULTS = 10
    _SNIPPET_LENGTH = 200

    stmt = (
        select(Artifact)
        .where(
            Artifact.project_id == _ctx.project_id,
            (Artifact.content.ilike(f"%{query}%"))
            | (Artifact.title.ilike(f"%{query}%")),
        )
        .order_by(Artifact.updated_at.desc())
        .limit(_MAX_RESULTS)
    )
    result = await _ctx.db.execute(stmt)
    artifacts = result.scalars().all()

    results = []
    for a in artifacts:
        snippet = ""
        idx = a.content.lower().find(query.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            snippet = a.content[start: start + _SNIPPET_LENGTH]
        else:
            snippet = a.content[:_SNIPPET_LENGTH]

        results.append({
            "id": str(a.id),
            "title": a.title,
            "artifact_type": a.artifact_type,
            "snippet": snippet,
        })

    return {"results": results, "count": len(results), "query": query}


@tool
async def export_project(
    export_format: str = "zip",
    _ctx: "ToolContext | None" = None,
) -> dict:
    """导出当前项目为 ZIP 包。

    Args:
        export_format: 导出格式，默认 zip
    """
    if _ctx is None:
        return {"error": "无法导出（缺少上下文）"}

    try:
        from worker_app.celery_app import celery_app
        task = celery_app.send_task(
            "tasks.export_project",
            args=[str(_ctx.project_id), export_format],
        )
        return {
            "action": "export_started",
            "task_id": task.id,
            "project_id": str(_ctx.project_id),
            "format": export_format,
        }
    except Exception as exc:
        return {
            "action": "export_started",
            "project_id": str(_ctx.project_id),
            "format": export_format,
            "warning": f"导出任务提交失败: {exc}，请稍后重试",
        }
