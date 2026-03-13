"""
IR 示例模块。

导出预构建的 IR fixture 和操作列表，用于演示和集成测试。
"""

from ir_core.examples.todo_fixture import build_todo_fixture, build_todo_operations

__all__ = [
    "build_todo_fixture",
    "build_todo_operations",
]
