"""文档与图表生成工具。

提供需求文档、设计文档、API 文档、Mermaid 图表和 SQL 生成能力。
"""

from __future__ import annotations

from agents.tools.base import tool


@tool
async def generate_document(doc_type: str, title: str, description: str) -> dict:
    """生成结构化文档。

    Args:
        doc_type: 文档类型，取值 requirement / design / api_doc / thesis_chapter
        title: 文档标题
        description: 文档内容的需求描述
    """
    return {
        "artifact_type": "document",
        "doc_type": doc_type,
        "title": title,
        "description": description,
        "content": "",
    }


@tool
async def generate_diagram(diagram_type: str, description: str) -> dict:
    """生成 Mermaid 格式的图表。

    Args:
        diagram_type: 图表类型，取值 flowchart / sequence / er / class / architecture
        description: 图表内容描述
    """
    return {
        "artifact_type": "diagram",
        "diagram_type": diagram_type,
        "format": "mermaid",
        "description": description,
        "content": "",
    }


@tool
async def generate_sql(description: str, dialect: str = "postgresql") -> dict:
    """根据自然语言描述生成 SQL 语句。

    Args:
        description: SQL 需求的自然语言描述
        dialect: SQL 方言，默认 postgresql
    """
    return {
        "artifact_type": "sql",
        "dialect": dialect,
        "description": description,
        "content": "",
    }
