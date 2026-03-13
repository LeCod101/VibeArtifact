"""
投影函数包。

导出所有 Agent 专用投影函数和统一返回类型 ProjectionResult。
"""

from ir_core.projections.api_doc_projection import api_doc_projection
from ir_core.projections.architecture_projection import architecture_projection
from ir_core.projections.backend_projection import backend_projection
from ir_core.projections.frontend_projection import frontend_projection
from ir_core.projections.result import ProjectionResult
from ir_core.projections.schema_projection import schema_projection

__all__ = [
    "ProjectionResult",
    "api_doc_projection",
    "architecture_projection",
    "backend_projection",
    "frontend_projection",
    "schema_projection",
]
