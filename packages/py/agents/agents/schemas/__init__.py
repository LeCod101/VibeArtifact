"""
Agent Schema 统一导出模块。

集中导出所有 Agent 相关的 Pydantic Schema 类型，
方便外部一次性 import 所需的类型。
"""

# 基础类型
# Agent 专用 Schema — Backend
from agents.schemas.backend import BackendInput, BackendOutput
from agents.schemas.base import (
    AgentInput,
    AgentOutput,
    AgentRunMeta,
    MessageSlice,
)

# Agent 专用 Schema — Contraction
from agents.schemas.contraction import ContractionInput, ContractionOutput

# Agent 专用 Schema — Diagram
from agents.schemas.diagram import DiagramInput, DiagramOutput

# Agent 专用 Schema — Doc
from agents.schemas.doc import DocInput, DocOutput

# Agent 专用 Schema — Export
from agents.schemas.export import ExportInput, ExportOutput

# Agent 专用 Schema — Frontend
from agents.schemas.frontend import FrontendInput, FrontendOutput

# 高层结构体
from agents.schemas.high_level import (
    BackendPlan,
    DiagramPlan,
    DiagramSpec,
    DocPlan,
    EndpointSpec,
    EntitySpec,
    ExportManifest,
    FieldSpec,
    FileSpec,
    FixItem,
    FixPlan,
    FrontendPlan,
    SchemaPlan,
    ScopeDraft,
    ScopeItem,
    TaskPlan,
    TaskStep,
)

# Agent 专用 Schema — Intent
from agents.schemas.intent import IntentInput, IntentOutput

# Agent 专用 Schema — Planner
from agents.schemas.planner import PlannerInput, PlannerOutput

# Agent 专用 Schema — QA
from agents.schemas.qa import QAInput, QAOutput

# Agent 专用 Schema — Schema
from agents.schemas.schema_agent import SchemaInput, SchemaOutput

__all__ = [
    # 基础类型
    "MessageSlice",
    "AgentRunMeta",
    "AgentInput",
    "AgentOutput",
    # 高层结构体
    "ScopeItem",
    "ScopeDraft",
    "TaskStep",
    "TaskPlan",
    "FieldSpec",
    "EntitySpec",
    "EndpointSpec",
    "SchemaPlan",
    "FileSpec",
    "BackendPlan",
    "FrontendPlan",
    "DocPlan",
    "DiagramSpec",
    "DiagramPlan",
    "FixItem",
    "FixPlan",
    "ExportManifest",
    # Agent 专用 Schema
    "IntentInput",
    "IntentOutput",
    "ContractionInput",
    "ContractionOutput",
    "PlannerInput",
    "PlannerOutput",
    "SchemaInput",
    "SchemaOutput",
    "BackendInput",
    "BackendOutput",
    "FrontendInput",
    "FrontendOutput",
    "DocInput",
    "DocOutput",
    "DiagramInput",
    "DiagramOutput",
    "QAInput",
    "QAOutput",
    "ExportInput",
    "ExportOutput",
]
