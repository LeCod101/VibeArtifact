"""代码生成与编辑工具。

提供代码生成、编辑、解释和审查能力。
工具函数的返回结果会作为 Artifact 存储。
"""

from __future__ import annotations

from agents.tools.base import tool


@tool
async def generate_code(language: str, title: str, description: str, framework: str = "") -> dict:
    """生成指定语言的代码框架。

    Args:
        language: 编程语言，如 python / java / javascript / typescript
        title: 代码文件标题
        description: 功能需求描述，Agent 将据此生成代码
        framework: 可选的框架名称，如 flask / spring / react
    """
    return {
        "artifact_type": "code",
        "title": title,
        "language": language,
        "framework": framework,
        "description": description,
        "content": "",
    }


@tool
async def edit_code(artifact_id: str, instructions: str) -> dict:
    """编辑已有代码 Artifact。

    Args:
        artifact_id: 要编辑的 Artifact ID
        instructions: 编辑指令，描述需要修改的内容
    """
    return {
        "artifact_type": "code_edit",
        "artifact_id": artifact_id,
        "instructions": instructions,
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
