"""
产物收集器模块。

从工作区文件（workspace_files）中收集所有产物文件（代码、文档、图表），
将其归一化为统一的 FileEntry 列表，供后续 ZIP 打包使用。

输入为已加载的文件字典列表（List[dict]，含 file_path/content/file_kind），
不直接操作数据库。
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

# 收集器支持的文件类别
_COLLECTIBLE_KINDS: set[str] = {"code", "doc", "diagram"}


class ArtifactCollector:
    """
    产物收集器。

    从工作区文件字典列表中提取 code / doc / diagram 类别的文件，
    归一化导出路径后转换为 FileEntry 列表。
    """

    def __init__(self, layout: LayoutConfig | None = None) -> None:
        """
        初始化产物收集器。

        - layout: 目录布局配置，为 None 时使用默认布局
        """
        self._layout = layout or DEFAULT_LAYOUT

    def collect(self, files: list[dict]) -> FileCollection:
        """
        从工作区文件列表收集所有产物文件。

        遍历所有 code / doc / diagram 类别文件，归一化路径后
        返回 FileCollection。

        - files: 工作区文件字典列表，每项需含 file_path/content/file_kind
        - 返回: FileEntry 列表
        """
        entries: FileCollection = []

        for f in files:
            kind = f.get("file_kind", "")
            if kind not in _COLLECTIBLE_KINDS:
                continue

            path = f.get("file_path", "")
            content = f.get("content", "")
            if not path or not content:
                continue

            export_path = normalize_path(kind, path, self._layout)
            entries.append(FileEntry(export_path=export_path, content=content))

        # 解决路径冲突
        if entries:
            paths = [e.export_path for e in entries]
            resolved = resolve_conflicts(paths)
            for entry, path in zip(entries, resolved):
                entry.export_path = path

        return entries
