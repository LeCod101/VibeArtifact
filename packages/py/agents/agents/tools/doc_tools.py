"""文档与图表生成工具。

提供文档、Mermaid 图表和 SQL 创建能力。
通过 ToolContext 直接写入 artifacts 表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.tools.base import tool

if TYPE_CHECKING:
    from agents.tools.context import ToolContext


@tool
async def create_document(
    doc_type: str,
    title: str,
    content: str,
    _ctx: "ToolContext | None" = None,
) -> dict:
    """创建结构化文档并存储为项目 Artifact。

    Args:
        doc_type: 文档类型，取值 requirement / design / api_doc / thesis_chapter
        title: 文档标题
        content: 完整的 Markdown 文档内容（由 LLM 生成）
    """
    if _ctx is None:
        return {"artifact_type": "document", "title": title, "content": content}

    from platform_data.models.artifact import Artifact

    artifact = Artifact(
        project_id=_ctx.project_id,
        artifact_type="document",
        title=title,
        content=content,
        language=doc_type,
    )
    _ctx.db.add(artifact)
    await _ctx.db.flush()
    await _ctx.db.refresh(artifact)

    return {
        "artifact_type": "document",
        "artifact_id": str(artifact.id),
        "doc_type": doc_type,
        "title": title,
        "content": content,
    }


@tool
async def create_diagram(
    diagram_type: str,
    title: str,
    content: str,
    _ctx: "ToolContext | None" = None,
) -> dict:
    """创建 Mermaid 格式的图表并存储为项目 Artifact。

    Args:
        diagram_type: 图表类型，取值 flowchart / sequence / er / class / architecture
        title: 图表标题
        content: 完整的 Mermaid 语法图表代码（由 LLM 生成）
    """
    if _ctx is None:
        return {"artifact_type": "diagram", "title": title, "content": content}

    from platform_data.models.artifact import Artifact

    artifact = Artifact(
        project_id=_ctx.project_id,
        artifact_type="diagram",
        title=title,
        content=content,
        language=diagram_type,
    )
    _ctx.db.add(artifact)
    await _ctx.db.flush()
    await _ctx.db.refresh(artifact)

    return {
        "artifact_type": "diagram",
        "artifact_id": str(artifact.id),
        "diagram_type": diagram_type,
        "title": title,
        "content": content,
    }


@tool
async def create_sql(
    title: str,
    content: str,
    dialect: str = "postgresql",
    _ctx: "ToolContext | None" = None,
) -> dict:
    """根据需求创建 SQL 语句并存储为项目 Artifact。

    Args:
        title: SQL 文件标题，如 "建表脚本"
        content: 完整的 SQL 语句（由 LLM 生成）
        dialect: SQL 方言，默认 postgresql
    """
    if _ctx is None:
        return {"artifact_type": "database_schema", "title": title, "content": content}

    from platform_data.models.artifact import Artifact

    artifact = Artifact(
        project_id=_ctx.project_id,
        artifact_type="database_schema",
        title=title,
        content=content,
        language=dialect,
    )
    _ctx.db.add(artifact)
    await _ctx.db.flush()
    await _ctx.db.refresh(artifact)

    return {
        "artifact_type": "database_schema",
        "artifact_id": str(artifact.id),
        "dialect": dialect,
        "title": title,
        "content": content,
    }
