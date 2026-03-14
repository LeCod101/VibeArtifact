"""
产物存储模块。

Phase 1 简单实现：将 ZIP 文件保存到本地文件系统。
存储路径为 data/exports/{run_id}.zip。
"""

from __future__ import annotations

from pathlib import Path

# 默认导出目录
EXPORT_DIR = Path("data/exports")


def _ensure_dir(directory: Path) -> None:
    """
    确保目录存在，不存在则自动创建。

    - directory: 需要确保存在的目录路径
    """
    directory.mkdir(parents=True, exist_ok=True)


def save_zip(run_id: str, zip_bytes: bytes) -> Path:
    """
    保存 ZIP 文件到本地存储。

    将 ZIP 字节数据写入 data/exports/{run_id}.zip。

    - run_id: 运行 ID，用作文件名
    - zip_bytes: ZIP 文件的字节数据
    - 返回: 保存后的文件路径
    """
    _ensure_dir(EXPORT_DIR)
    file_path = EXPORT_DIR / f"{run_id}.zip"
    file_path.write_bytes(zip_bytes)
    return file_path


def get_zip_path(run_id: str) -> Path | None:
    """
    获取 ZIP 文件路径。

    检查指定 run_id 的 ZIP 文件是否存在，存在则返回路径。

    - run_id: 运行 ID
    - 返回: 文件路径（存在时）或 None（不存在时）
    """
    file_path = EXPORT_DIR / f"{run_id}.zip"
    if file_path.exists():
        return file_path
    return None


def delete_zip(run_id: str) -> bool:
    """
    删除 ZIP 文件。

    - run_id: 运行 ID
    - 返回: 删除成功返回 True，文件不存在返回 False
    """
    file_path = EXPORT_DIR / f"{run_id}.zip"
    if file_path.exists():
        file_path.unlink()
        return True
    return False
