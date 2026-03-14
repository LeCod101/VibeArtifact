"""
ZIP 打包器模块。

将 FileCollection 打包为 ZIP 文件，支持输出为 bytes 或写入磁盘。
ZIP 内部结构以 project_name 为根目录。
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from runtime_tools.exporters.collector import FileCollection


class ZipPacker:
    """
    ZIP 打包器。

    将文件集合打包为标准 ZIP 格式，
    所有文件放在以项目名称命名的根目录下。
    """

    def __init__(self, project_name: str, files: FileCollection) -> None:
        """
        初始化 ZIP 打包器。

        - project_name: 项目名称，作为 ZIP 内部根目录名
        - files: 待打包的文件集合
        """
        self._project_name = project_name
        self._files = files

    def pack_to_bytes(self) -> bytes:
        """
        打包为 ZIP 字节流。

        将所有文件写入内存中的 ZIP，返回完整的 ZIP 文件内容。

        - 返回: ZIP 文件的 bytes 数据
        """
        buf = io.BytesIO()
        self._write_zip(buf)
        return buf.getvalue()

    def pack_to_file(self, output_path: str | Path) -> Path:
        """
        打包为 ZIP 文件并写入磁盘。

        - output_path: 输出文件路径
        - 返回: 写入后的文件路径（Path 对象）
        """
        output = Path(output_path)
        # 确保父目录存在
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "wb") as f:
            self._write_zip(f)

        return output

    def _write_zip(self, target: io.BytesIO | io.BufferedWriter) -> None:
        """
        将文件集合写入 ZIP 到目标流。

        每个文件路径前加上项目名称作为根目录。
        所有内容使用 UTF-8 编码。

        - target: 写入目标（内存缓冲区或文件句柄）
        """
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in self._files:
                # 在 ZIP 内的路径：{project_name}/{export_path}
                archive_path = f"{self._project_name}/{entry.export_path}"
                zf.writestr(archive_path, entry.content.encode("utf-8"))
