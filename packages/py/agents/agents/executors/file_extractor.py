"""
Agent 输出文件提取器模块。

从 Agent 的高层输出（BackendPlan/FrontendPlan/DocPlan/DiagramPlan）
直接提取工作区文件字典，取代旧 Translator → IROperation 链路。

非产物型 Agent（intent/contraction/planner/schema/qa/export）不产生文件，
其高层输出通过 AgentInput.upstream_outputs 传递给下游 Agent 作上下文。
"""

from __future__ import annotations

from pydantic import BaseModel

from agents.schemas.high_level import (
    BackendPlan,
    DiagramPlan,
    DocPlan,
    FrontendPlan,
)

# Agent → 文件类别 映射（产物型 Agent）
_AGENT_FILE_KINDS: dict[str, str] = {
    "backend": "code",
    "frontend": "code",
    "doc": "doc",
    "diagram": "diagram",
}


def extract_files(agent_id: str, high_level: BaseModel) -> list[dict]:
    """
    从 Agent 高层输出提取工作区文件字典列表。

    - backend / frontend / doc: 提取 plan.files（FileSpec 列表）
    - diagram: 提取 plan.diagrams 并包装为 Mermaid Markdown
    - 其他 Agent: 返回空列表（无文件产物）

    - agent_id: Agent 唯一标识
    - high_level: Agent 的高层输出实例
    - 返回: [{"path": ..., "content": ..., "kind": ...}, ...]
    """
    kind = _AGENT_FILE_KINDS.get(agent_id)
    if kind is None:
        return []

    if agent_id == "diagram":
        if not isinstance(high_level, DiagramPlan):
            return []
        return _extract_diagrams(high_level)

    if not isinstance(high_level, (BackendPlan, FrontendPlan, DocPlan)):
        return []

    files: list[dict] = []
    for spec in high_level.files:
        if not spec.path or not spec.content:
            continue
        files.append({
            "path": spec.path,
            "content": spec.content,
            "kind": kind,
        })
    return files


def _extract_diagrams(plan: DiagramPlan) -> list[dict]:
    """
    提取图表计划为 Markdown 文件字典列表。

    每个图表包装为含 Mermaid 代码块的 Markdown 文件，
    文件名由图表标题清理生成。

    - plan: DiagramPlan 实例
    - 返回: 文件字典列表
    """
    files: list[dict] = []
    for diagram in plan.diagrams:
        if not diagram.title or not diagram.mermaid_code:
            continue

        md_lines = [
            f"# {diagram.title}",
            "",
            "```mermaid",
            diagram.mermaid_code,
            "```",
            "",
        ]

        files.append({
            "path": sanitize_filename(diagram.title),
            "content": "\n".join(md_lines),
            "kind": "diagram",
        })
    return files


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除不安全字符。

    将空格替换为下划线，移除路径分隔符等特殊字符。

    - name: 原始文件名
    - 返回: 清理后的安全文件名
    """
    safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-", "."))
    return safe or "unnamed"
