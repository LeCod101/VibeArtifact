"""项目管理工具。

提供项目文件浏览、读取、搜索和导出能力。
"""

from __future__ import annotations

from agents.tools.base import tool


@tool
async def list_files(project_id: str) -> dict:
    """列出项目中的所有文件。

    Args:
        project_id: 项目 ID
    """
    return {
        "action": "list_files",
        "project_id": project_id,
    }


@tool
async def read_file(artifact_id: str) -> dict:
    """读取指定 Artifact 的完整内容。

    Args:
        artifact_id: Artifact ID
    """
    return {
        "action": "read_file",
        "artifact_id": artifact_id,
    }


@tool
async def search_code(project_id: str, query: str) -> dict:
    """在项目代码中搜索匹配的内容。

    Args:
        project_id: 项目 ID
        query: 搜索关键词或模式
    """
    return {
        "action": "search_code",
        "project_id": project_id,
        "query": query,
    }


@tool
async def export_project(project_id: str, export_format: str = "zip") -> dict:
    """导出整个项目。

    Args:
        project_id: 项目 ID
        export_format: 导出格式，默认 zip
    """
    return {
        "action": "export_project",
        "project_id": project_id,
        "format": export_format,
    }
