"""
IR 校验器统一导出模块。

汇总导出所有校验器函数和校验结果数据结构，
外部可直接 from ir_core.validators import ValidationResult, ... 使用。
"""

from ir_core.validators.edge_validator import validate_edge
from ir_core.validators.node_validator import validate_node_props
from ir_core.validators.result import ValidationResult
from ir_core.validators.snapshot_validator import validate_snapshot

__all__ = [
    "ValidationResult",
    "validate_node_props",
    "validate_edge",
    "validate_snapshot",
]
