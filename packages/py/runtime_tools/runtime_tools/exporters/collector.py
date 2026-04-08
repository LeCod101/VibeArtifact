"""
产物收集器模块。

从 IR 快照中收集所有产物文件（代码、文档、图表），
将其归一化为统一的 FileEntry 列表，供后续 ZIP 打包使用。

Phase 1 简化：接受已加载的节点列表（List[dict]）作为输入，
不直接操作数据库或快照存储。
"""

from __future__ import annotations

from dataclasses import dataclass

from runtime_tools.exporters.project_layout import (
    DEFAULT_LAYOUT,
    LayoutConfig,
    normalize_path,
    resolve_conflicts,
)


@dataclass
class FileEntry:
    """
    单个导出文件条目。

    表示一个待导出到 ZIP 中的文件。
    - export_path: 在 ZIP 中的导出路径（已归一化）
    - content: 文件内容（UTF-8 文本）
    """

    export_path: str
    content: str


# FileCollection 类型别名
FileCollection = list[FileEntry]

# 收集器支持的节点类型
_COLLECTIBLE_TYPES: set[str] = {"code", "doc", "diagram"}


class ArtifactCollector:
    """
    产物收集器。

    从 IR 节点列表中提取 code / doc / diagram 类型的节点，
    将其转换为 FileEntry 列表。
    """

    def __init__(self, layout: LayoutConfig | None = None) -> None:
        """
        初始化产物收集器。

        - layout: 目录布局配置，为 None 时使用默认布局
        """
        self._layout = layout or DEFAULT_LAYOUT

    def collect(self, nodes: list[dict]) -> FileCollection:
        """
        从节点列表收集所有产物文件。

        遍历所有 code / doc / diagram 类型节点，提取文件路径和内容，
        归一化路径后返回 FileCollection。

        - nodes: IR 节点的字典列表，每个节点需包含 node_type 和 props 字段
        - 返回: FileEntry 列表
        """
        entries: FileCollection = []

        for node in nodes:
            node_type = node.get("node_type", "")
            if node_type not in _COLLECTIBLE_TYPES:
                continue

            props = node.get("props", {})
            if not props:
                continue

            entry = self._extract_entry(node_type, props)
            if entry is not None:
                entries.append(entry)

        # 解决路径冲突
        if entries:
            paths = [e.export_path for e in entries]
            resolved = resolve_conflicts(paths)
            for entry, path in zip(entries, resolved):
                entry.export_path = path

        return entries

    def collect_from_artifacts(self, artifacts: list) -> FileCollection:
        """
        从 Artifact ORM 对象列表收集导出文件。

        依据 artifact_type 映射到 code / doc / diagram 等布局规则，
        与 collect 相同地在最后统一做路径冲突消解。

        - artifacts: 需具备 artifact_type、title、content、file_path、language 等属性
        - 返回: FileEntry 列表
        """
        entries: FileCollection = []

        for artifact in artifacts:
            entry = self._extract_artifact(artifact)
            if entry is not None:
                entries.append(entry)

        if entries:
            paths = [e.export_path for e in entries]
            resolved = resolve_conflicts(paths)
            for entry, path in zip(entries, resolved):
                entry.export_path = path

        return entries

    def _extract_artifact(self, artifact) -> FileEntry | None:
        """
        将单个 Artifact ORM 对象转为 FileEntry。

        content 为空时跳过；diagram 导出为含 Mermaid 代码块的 Markdown。

        - artifact: ORM 实例或具备同名属性的鸭子类型
        - 返回: FileEntry 或 None
        """
        content = getattr(artifact, "content", "") or ""
        if not content:
            return None

        artifact_type = getattr(artifact, "artifact_type", "") or ""
        file_path = getattr(artifact, "file_path", None) or ""
        title = getattr(artifact, "title", None) or "untitled"

        if artifact_type == "code":
            path = file_path or f"{title}.txt"
            export_path = normalize_path("code", path, self._layout)
            return FileEntry(export_path=export_path, content=content)

        if artifact_type in ("document", "explanation"):
            path = file_path or f"{title}.md"
            export_path = normalize_path("doc", path, self._layout)
            return FileEntry(export_path=export_path, content=content)

        if artifact_type == "diagram":
            safe_name = _sanitize_filename(title)
            export_path = normalize_path("diagram", safe_name, self._layout)
            md_content = f"# {title}\n\n```mermaid\n{content}\n```\n"
            return FileEntry(export_path=export_path, content=md_content)

        if artifact_type in ("sql", "database_schema"):
            path = file_path or f"{title}.sql"
            export_path = normalize_path("code", path, self._layout)
            return FileEntry(export_path=export_path, content=content)

        if artifact_type in ("config", "other"):
            path = file_path or f"{title}.txt"
            export_path = normalize_path("code", path, self._layout)
            return FileEntry(export_path=export_path, content=content)

        path = file_path or f"{title}.txt"
        export_path = normalize_path("code", path, self._layout)
        return FileEntry(export_path=export_path, content=content)

    def _extract_entry(self, node_type: str, props: dict) -> FileEntry | None:
        """
        从单个节点提取文件条目。

        根据节点类型分别处理 code / doc / diagram 节点。

        - node_type: 节点类型字符串
        - props: 节点属性字典
        - 返回: FileEntry 或 None（无法提取时）
        """
        if node_type == "code":
            return self._extract_code(props)
        if node_type == "doc":
            return self._extract_doc(props)
        if node_type == "diagram":
            return self._extract_diagram(props)
        return None

    def _extract_code(self, props: dict) -> FileEntry | None:
        """
        提取代码节点的文件条目。

        CodeProps 结构：path, content, language

        - props: 代码节点的属性字典
        - 返回: FileEntry 或 None
        """
        path = props.get("path", "")
        content = props.get("content", "")
        if not path or not content:
            return None

        export_path = normalize_path("code", path, self._layout)
        return FileEntry(export_path=export_path, content=content)

    def _extract_doc(self, props: dict) -> FileEntry | None:
        """
        提取文档节点的文件条目。

        DocProps 结构：path, content, format

        - props: 文档节点的属性字典
        - 返回: FileEntry 或 None
        """
        path = props.get("path", "")
        content = props.get("content", "")
        if not path or not content:
            return None

        export_path = normalize_path("doc", path, self._layout)
        return FileEntry(export_path=export_path, content=content)

    def _extract_diagram(self, props: dict) -> FileEntry | None:
        """
        提取图表节点的文件条目。

        DiagramProps 结构：name, diagram_type, content, description
        图表导出为 Markdown 文件，包含 Mermaid 代码块。

        - props: 图表节点的属性字典
        - 返回: FileEntry 或 None
        """
        name = props.get("name", "")
        diagram_content = props.get("content", "")
        if not name or not diagram_content:
            return None

        description = props.get("description", "")

        # 构建 Markdown 文件内容
        md_lines = [f"# {name}"]
        if description:
            md_lines.append("")
            md_lines.append(description)
        md_lines.append("")
        md_lines.append("```mermaid")
        md_lines.append(diagram_content)
        md_lines.append("```")
        md_lines.append("")

        md_content = "\n".join(md_lines)

        # 用图表名称作为文件名
        safe_name = _sanitize_filename(name)
        export_path = normalize_path("diagram", safe_name, self._layout)

        return FileEntry(export_path=export_path, content=md_content)


def _sanitize_filename(name: str) -> str:
    """
    清理文件名，移除不安全字符。

    将空格替换为下划线，移除路径分隔符等特殊字符。

    - name: 原始文件名
    - 返回: 清理后的安全文件名
    """
    # 替换空格和常见分隔符
    safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    # 移除其他不安全字符
    safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-", "."))
    return safe or "unnamed"
