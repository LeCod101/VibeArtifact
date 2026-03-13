"""
IR 操作统一导出模块。

汇总导出快照操作应用和差异计算功能，
外部可直接 from ir_core.operations import apply_operations, ... 使用。
"""

from ir_core.operations.apply import ApplyError, apply_operations
from ir_core.operations.diff import compute_diff

__all__ = [
    "apply_operations",
    "ApplyError",
    "compute_diff",
]
