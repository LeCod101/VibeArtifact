"""
Schema 类型序列化/反序列化测试模块。

测试所有 Agent 的 Input/Output 类型以及高层结构体的
model_validate / model_dump 往返正确性。
"""

from uuid import uuid4

from agents.schemas.backend import BackendInput, BackendOutput
from agents.schemas.base import AgentInput, AgentOutput, AgentRunMeta, MessageSlice
from agents.schemas.contraction import (
    ContractionDecision,
    ContractionInput,
    ContractionOutput,
    DeferredFeature,
)
from agents.schemas.diagram import DiagramOutput
from agents.schemas.doc import DocOutput
from agents.schemas.export import ExportInput, ExportOutput
from agents.schemas.frontend import FrontendOutput
from agents.schemas.high_level import (
    ExportManifest,
    FixPlan,
    SchemaPlan,
    ScopeDraft,
    ScopeItem,
    TaskPlan,
)
from agents.schemas.intent import IntentInput, IntentOutput
from agents.schemas.planner import PlannerInput, PlannerOutput
from agents.schemas.qa import QAInput, QAOutput
from agents.schemas.schema_agent import SchemaInput, SchemaOutput

# ============================================================
# 辅助函数
# ============================================================

def _base_input_data():
    """构造 AgentInput 的基础字段数据。"""
    return {
        "project_id": str(uuid4()),
        "snapshot_id": str(uuid4()),
        "ir_nodes": [],
        "ir_edges": [],
        "task_description": "测试任务",
    }


def _sample_scope_draft():
    """构造一个 ScopeDraft 的字典数据。"""
    return {
        "product_name": "TestApp",
        "product_description": "测试应用",
        "scopes": [
            {
                "name": "核心功能",
                "description": "核心功能描述",
                "priority": "high",
                "tags": ["core"],
            }
        ],
        "deferred_items": ["高级功能"],
        "risks": ["技术风险"],
    }


def _sample_schema_plan():
    """构造一个 SchemaPlan 的字典数据。"""
    return {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "UUID", "primary": True, "nullable": False},
                    {"name": "email", "type": "str"},
                ],
                "relationships": [],
            }
        ],
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/users",
                "description": "获取用户列表",
            }
        ],
    }


def _sample_task_plan():
    """构造一个 TaskPlan 的字典数据。"""
    return {
        "steps": [
            {
                "step_id": "s1",
                "agent_id": "schema",
                "description": "设计数据模型",
                "depends_on": [],
            }
        ],
        "estimated_complexity": "medium",
    }


# ============================================================
# 基础类型测试
# ============================================================

class TestBaseSchemas:
    """基础 Schema 类型的序列化/反序列化测试。"""

    def test_agent_input_roundtrip(self):
        """AgentInput 可以 model_validate / model_dump 往返。"""
        data = _base_input_data()
        obj = AgentInput.model_validate(data)
        dumped = obj.model_dump()
        restored = AgentInput.model_validate(dumped)
        assert str(restored.project_id) == data["project_id"]
        assert restored.task_description == data["task_description"]

    def test_agent_output_roundtrip(self):
        """AgentOutput 可以 model_validate / model_dump 往返。"""
        data = {
            "reasoning": "测试推理",
            "confidence": 0.9,
            "warnings": ["注意事项"],
        }
        obj = AgentOutput.model_validate(data)
        dumped = obj.model_dump()
        restored = AgentOutput.model_validate(dumped)
        assert restored.reasoning == "测试推理"
        assert restored.confidence == 0.9
        assert restored.warnings == ["注意事项"]

    def test_message_slice_roundtrip(self):
        """MessageSlice 可以 model_validate / model_dump 往返。"""
        data = {"role": "user", "content": "你好"}
        obj = MessageSlice.model_validate(data)
        dumped = obj.model_dump()
        restored = MessageSlice.model_validate(dumped)
        assert restored.role == "user"
        assert restored.content == "你好"

    def test_agent_run_meta_roundtrip(self):
        """AgentRunMeta 可以 model_validate / model_dump 往返。"""
        data = {
            "model": "test-model",
            "provider": "mock",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_cost": 0.01,
            "latency_ms": 500.0,
        }
        obj = AgentRunMeta.model_validate(data)
        dumped = obj.model_dump()
        restored = AgentRunMeta.model_validate(dumped)
        assert restored.model == "test-model"
        assert restored.prompt_tokens == 100


# ============================================================
# 高层结构体测试
# ============================================================

class TestHighLevelSchemas:
    """高层结构体的序列化/反序列化测试。"""

    def test_scope_draft_fields(self):
        """ScopeDraft 包含 scopes、deferred_items、risks 字段。"""
        data = _sample_scope_draft()
        obj = ScopeDraft.model_validate(data)
        assert len(obj.scopes) == 1
        assert obj.deferred_items == ["高级功能"]
        assert obj.risks == ["技术风险"]

    def test_scope_draft_roundtrip(self):
        """ScopeDraft 可以 model_validate / model_dump 往返。"""
        data = _sample_scope_draft()
        obj = ScopeDraft.model_validate(data)
        dumped = obj.model_dump()
        restored = ScopeDraft.model_validate(dumped)
        assert restored.product_name == obj.product_name
        assert len(restored.scopes) == len(obj.scopes)

    def test_scope_item_roundtrip(self):
        """ScopeItem 可以 model_validate / model_dump 往返。"""
        data = {
            "name": "功能A",
            "description": "功能A描述",
            "priority": "high",
            "tags": ["tag1"],
        }
        obj = ScopeItem.model_validate(data)
        dumped = obj.model_dump()
        restored = ScopeItem.model_validate(dumped)
        assert restored.name == "功能A"
        assert restored.priority == "high"

    def test_schema_plan_fields(self):
        """SchemaPlan 包含 entities 和 endpoints 字段。"""
        data = _sample_schema_plan()
        obj = SchemaPlan.model_validate(data)
        assert len(obj.entities) == 1
        assert len(obj.endpoints) == 1
        assert obj.entities[0].name == "User"

    def test_task_plan_roundtrip(self):
        """TaskPlan 可以 model_validate / model_dump 往返。"""
        data = _sample_task_plan()
        obj = TaskPlan.model_validate(data)
        dumped = obj.model_dump()
        restored = TaskPlan.model_validate(dumped)
        assert len(restored.steps) == 1
        assert restored.estimated_complexity == "medium"

    def test_fix_plan_roundtrip(self):
        """FixPlan 可以 model_validate / model_dump 往返。"""
        data = {
            "passed": False,
            "issues": [
                {
                    "file_path": "main.py",
                    "issue": "缺少错误处理",
                    "fix_description": "添加 try-except",
                }
            ],
            "summary": "发现 1 个问题",
        }
        obj = FixPlan.model_validate(data)
        dumped = obj.model_dump()
        restored = FixPlan.model_validate(dumped)
        assert not restored.passed
        assert len(restored.issues) == 1

    def test_export_manifest_roundtrip(self):
        """ExportManifest 可以 model_validate / model_dump 往返。"""
        data = {
            "project_name": "TestProject",
            "files": ["main.py", "README.md"],
            "entry_point": "main.py",
        }
        obj = ExportManifest.model_validate(data)
        dumped = obj.model_dump()
        restored = ExportManifest.model_validate(dumped)
        assert restored.project_name == "TestProject"
        assert len(restored.files) == 2


# ============================================================
# Agent 专用 Input/Output 测试
# ============================================================

class TestAgentSpecificSchemas:
    """10 个 Agent 的 Input/Output 序列化/反序列化测试。"""

    def test_intent_input_output_roundtrip(self):
        """IntentInput/IntentOutput 可以 model_validate / model_dump 往返。"""
        # IntentInput
        input_data = {**_base_input_data(), "user_idea": "做一个 Todo 应用"}
        inp = IntentInput.model_validate(input_data)
        assert inp.user_idea == "做一个 Todo 应用"

        # IntentOutput
        output_data = {
            "reasoning": "理解用户意图",
            "confidence": 0.9,
            "warnings": [],
            "scope_draft": _sample_scope_draft(),
        }
        out = IntentOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = IntentOutput.model_validate(dumped)
        assert restored.scope_draft.product_name == "TestApp"

    def test_contraction_input_output_roundtrip(self):
        """ContractionInput/ContractionOutput 往返测试。"""
        # 构造容量报告数据
        capacity_report_data = {
            "dimensions": [
                {"dimension": "pages", "count": 1, "points": 3},
                {"dimension": "api_endpoints", "count": 2, "points": 4},
                {"dimension": "db_tables", "count": 1, "points": 3},
                {"dimension": "auth_flows", "count": 0, "points": 0},
                {"dimension": "integrations", "count": 0, "points": 0},
                {"dimension": "file_upload", "count": 0, "points": 0},
                {"dimension": "realtime", "count": 0, "points": 0},
                {"dimension": "payment", "count": 0, "points": 0},
            ],
            "total_points": 10,
            "tier": "small",
            "budget": 30,
            "over_budget": False,
            "needs_contraction": False,
            "must_contract": False,
        }
        input_data = {
            **_base_input_data(),
            "scope_draft": _sample_scope_draft(),
            "capacity_report": capacity_report_data,
        }
        inp = ContractionInput.model_validate(input_data)
        assert inp.scope_draft.product_name == "TestApp"
        assert inp.capacity_report.total_points == 10

        # 构造收缩决策数据
        decision_data = {
            "retained_features": ["核心功能"],
            "deferred_features": [
                {"name": "高级功能", "reason": "实现复杂度过高，优先延后"}
            ],
            "risks": ["收缩后功能较少"],
            "rationale": "保留核心功能作为 MVP 最小集合",
        }
        output_data = {
            "reasoning": "收缩功能",
            "confidence": 0.8,
            "warnings": [],
            "scope_draft": _sample_scope_draft(),
            "decision": decision_data,
        }
        out = ContractionOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = ContractionOutput.model_validate(dumped)
        assert len(restored.scope_draft.scopes) == 1
        assert restored.decision.rationale == "保留核心功能作为 MVP 最小集合"
        assert len(restored.decision.deferred_features) == 1
        assert restored.decision.deferred_features[0].name == "高级功能"

    def test_planner_input_output_roundtrip(self):
        """PlannerInput/PlannerOutput 往返测试。"""
        input_data = {
            **_base_input_data(),
            "scope_draft": _sample_scope_draft(),
        }
        inp = PlannerInput.model_validate(input_data)
        assert inp.scope_draft is not None

        output_data = {
            "reasoning": "规划任务",
            "confidence": 0.85,
            "warnings": [],
            "task_plan": _sample_task_plan(),
        }
        out = PlannerOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = PlannerOutput.model_validate(dumped)
        assert len(restored.task_plan.steps) == 1

    def test_schema_input_output_roundtrip(self):
        """SchemaInput/SchemaOutput 往返测试。"""
        input_data = {
            **_base_input_data(),
            "scope_draft": _sample_scope_draft(),
        }
        SchemaInput.model_validate(input_data)

        output_data = {
            "reasoning": "设计数据模型",
            "confidence": 0.9,
            "warnings": [],
            "schema_plan": _sample_schema_plan(),
        }
        out = SchemaOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = SchemaOutput.model_validate(dumped)
        assert len(restored.schema_plan.entities) == 1

    def test_backend_input_output_roundtrip(self):
        """BackendInput/BackendOutput 往返测试。"""
        input_data = {
            **_base_input_data(),
            "schema_plan": _sample_schema_plan(),
        }
        inp = BackendInput.model_validate(input_data)
        assert inp.schema_plan is not None

        output_data = {
            "reasoning": "生成后端代码",
            "confidence": 0.9,
            "warnings": [],
            "backend_plan": {
                "files": [
                    {"path": "main.py", "content": "print('hello')", "language": "python"}
                ]
            },
        }
        out = BackendOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = BackendOutput.model_validate(dumped)
        assert len(restored.backend_plan.files) == 1

    def test_frontend_input_output_roundtrip(self):
        """FrontendInput/FrontendOutput 往返测试。"""
        output_data = {
            "reasoning": "生成前端代码",
            "confidence": 0.9,
            "warnings": [],
            "frontend_plan": {
                "files": [
                    {"path": "App.tsx", "content": "<div/>", "language": "typescript"}
                ]
            },
        }
        out = FrontendOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = FrontendOutput.model_validate(dumped)
        assert len(restored.frontend_plan.files) == 1

    def test_doc_input_output_roundtrip(self):
        """DocInput/DocOutput 往返测试。"""
        output_data = {
            "reasoning": "生成文档",
            "confidence": 0.9,
            "warnings": [],
            "doc_plan": {
                "files": [
                    {"path": "README.md", "content": "# Hello", "language": "markdown"}
                ]
            },
        }
        out = DocOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = DocOutput.model_validate(dumped)
        assert restored.doc_plan.files[0].path == "README.md"

    def test_diagram_input_output_roundtrip(self):
        """DiagramInput/DiagramOutput 往返测试。"""
        output_data = {
            "reasoning": "生成图表",
            "confidence": 0.9,
            "warnings": [],
            "diagram_plan": {
                "diagrams": [
                    {
                        "title": "ER 图",
                        "diagram_type": "er",
                        "mermaid_code": "erDiagram",
                    }
                ]
            },
        }
        out = DiagramOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = DiagramOutput.model_validate(dumped)
        assert len(restored.diagram_plan.diagrams) == 1

    def test_qa_input_output_roundtrip(self):
        """QAInput/QAOutput 往返测试。"""
        input_data = {
            **_base_input_data(),
            "file_contents": {"main.py": "print('hello')"},
        }
        inp = QAInput.model_validate(input_data)
        assert "main.py" in inp.file_contents

        output_data = {
            "reasoning": "审查代码",
            "confidence": 0.9,
            "warnings": [],
            "fix_plan": {
                "passed": True,
                "issues": [],
                "summary": "通过检查",
            },
        }
        out = QAOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = QAOutput.model_validate(dumped)
        assert restored.fix_plan.passed

    def test_export_input_output_roundtrip(self):
        """ExportInput/ExportOutput 往返测试。"""
        input_data = {
            **_base_input_data(),
            "artifact_paths": ["main.py", "README.md"],
        }
        inp = ExportInput.model_validate(input_data)
        assert len(inp.artifact_paths) == 2

        output_data = {
            "reasoning": "打包导出",
            "confidence": 0.95,
            "warnings": [],
            "export_manifest": {
                "project_name": "MyProject",
                "files": ["main.py"],
                "entry_point": "main.py",
            },
        }
        out = ExportOutput.model_validate(output_data)
        dumped = out.model_dump()
        restored = ExportOutput.model_validate(dumped)
        assert restored.export_manifest.project_name == "MyProject"
