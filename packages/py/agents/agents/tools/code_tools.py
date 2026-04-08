"""代码生成与编辑工具。

提供代码创建、编辑、解释和审查能力。
create_file / edit_file 通过 ToolContext 直接写入 artifacts 表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from agents.tools.base import tool

if TYPE_CHECKING:
    from agents.tools.context import ToolContext


@tool
async def create_file(
    language: str,
    title: str,
    content: str,
    file_path: str = "",
    _ctx: "ToolContext | None" = None,
) -> dict:
    """创建代码文件并存储为项目 Artifact。

    Args:
        language: 编程语言，如 python / java / javascript / typescript / c / go
        title: 文件标题，如 BinaryTree.java
        content: 完整的代码内容（由 LLM 生成）
        file_path: 文件在项目中的相对路径，如 src/main/java/BinaryTree.java
    """
    if _ctx is None:
        return {"artifact_type": "code", "title": title, "content": content}

    from platform_data.models.artifact import Artifact

    artifact = Artifact(
        project_id=_ctx.project_id,
        artifact_type="code",
        title=title,
        content=content,
        file_path=file_path or None,
        language=language,
    )
    _ctx.db.add(artifact)
    await _ctx.db.flush()
    await _ctx.db.refresh(artifact)

    return {
        "artifact_type": "code",
        "artifact_id": str(artifact.id),
        "title": title,
        "language": language,
        "file_path": file_path,
        "content": content,
    }


@tool
async def edit_file(
    artifact_id: str,
    new_content: str,
    _ctx: "ToolContext | None" = None,
) -> dict:
    """编辑已有代码 Artifact，创建新版本。

    Args:
        artifact_id: 要编辑的 Artifact ID
        new_content: 修改后的完整代码内容
    """
    if _ctx is None:
        return {"artifact_type": "code_edit", "artifact_id": artifact_id}

    from platform_data.models.artifact import Artifact

    stmt = select(Artifact).where(Artifact.id == UUID(artifact_id))
    result = await _ctx.db.execute(stmt)
    original = result.scalar_one_or_none()

    if original is None:
        return {"error": f"未找到 Artifact: {artifact_id}"}

    new_artifact = Artifact(
        project_id=original.project_id,
        artifact_type=original.artifact_type,
        title=original.title,
        content=new_content,
        file_path=original.file_path,
        language=original.language,
        version_num=original.version_num + 1,
        parent_id=original.id,
    )
    _ctx.db.add(new_artifact)
    await _ctx.db.flush()
    await _ctx.db.refresh(new_artifact)

    return {
        "artifact_type": "code_edit",
        "artifact_id": str(new_artifact.id),
        "original_id": artifact_id,
        "version_num": new_artifact.version_num,
        "title": new_artifact.title,
        "content": new_content,
    }


@tool
async def explain_code(code: str, language: str) -> dict:
    """解释一段代码的逻辑和设计意图。

    Args:
        code: 待解释的代码片段
        language: 代码使用的编程语言
    """
    return {
        "artifact_type": "explanation",
        "code": code,
        "language": language,
    }


@tool
async def review_code(code: str, language: str) -> dict:
    """审查代码质量，给出改进建议。

    Args:
        code: 待审查的代码片段
        language: 代码使用的编程语言
    """
    return {
        "artifact_type": "review",
        "code": code,
        "language": language,
    }
