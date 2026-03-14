"""
QA + Export Translator 测试模块。

测试 QATranslator 和 ExportTranslator 的翻译逻辑，
包括通过/失败场景、Docker Compose 校验和边界情况。
"""

import pytest
from agents.schemas.high_level import (
    ExportManifest,
    FileEntry,
    IssueSpec,
    QAReport,
)
from agents.translators.export_translator import ExportTranslator
from agents.translators.qa_translator import QATranslator
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType


# ============================================================
# 辅助函数
# ============================================================

def _make_qa_passed() -> QAReport:
    """构造通过的 QA 报告。"""
    return QAReport(
        passed=True,
        issues=[
            IssueSpec(
                severity="info",
                category="missing_file",
                description="缺少 .gitignore 文件（非关键）",
                affected_file=".gitignore",
            ),
        ],
        summary="质量检查通过，存在 1 个 info 级别问题",
    )


def _make_qa_failed() -> QAReport:
    """构造失败的 QA 报告，包含 critical 和 warning 问题。"""
    return QAReport(
        passed=False,
        issues=[
            IssueSpec(
                severity="critical",
                category="missing_file",
                description="缺少 backend/main.py 入口文件",
                affected_file="backend/main.py",
            ),
            IssueSpec(
                severity="critical",
                category="schema_mismatch",
                description="User 实体缺少 email 字段",
                affected_file="backend/models/user.py",
            ),
            IssueSpec(
                severity="warning",
                category="import_error",
                description="未使用的 import 语句",
                affected_file="backend/routes/user.py",
            ),
        ],
        summary="质量检查未通过，存在 2 个 critical 和 1 个 warning 问题",
    )


def _make_export_manifest() -> ExportManifest:
    """构造标准的 ExportManifest。"""
    return ExportManifest(
        project_name="TodoApp",
        files=[
            FileEntry(
                source_type="code",
                source_path="backend/main.py",
                export_path="backend/main.py",
            ),
            FileEntry(
                source_type="code",
                source_path="frontend/app/page.tsx",
                export_path="frontend/app/page.tsx",
            ),
            FileEntry(
                source_type="doc",
                source_path="README.md",
                export_path="README.md",
            ),
        ],
        docker_compose_config={
            "services": {
                "backend": {"build": "./backend"},
                "frontend": {"build": "./frontend"},
                "postgres": {"image": "postgres:16"},
                "redis": {"image": "redis:7"},
            },
        },
        env_template={
            "DATABASE_URL": "postgresql://...",
            "REDIS_URL": "redis://...",
            "SECRET_KEY": "change-me",
        },
    )


# ============================================================
# QATranslator 测试
# ============================================================

class TestQATranslator:
    """QATranslator 翻译逻辑测试。"""

    def test_qa_passed(self):
        """passed=true → 只创建一个 decision 节点（qa_passed）。"""
        translator = QATranslator()
        report = _make_qa_passed()
        result = translator.translate(report)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 应该只有 1 个 decision 节点
        assert len(node_ops) == 1
        assert node_ops[0]["node_type"] == NodeType.DECISION
        assert node_ops[0]["label"] == "QA 检查通过"
        assert node_ops[0]["props"]["status"] == "accepted"

    def test_qa_failed(self):
        """passed=false → 每个 critical issue 一个 risk 节点 + 一个 decision 节点。"""
        translator = QATranslator()
        report = _make_qa_failed()
        result = translator.translate(report)

        # 筛选节点操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 2 个 critical issue → 2 个 risk 节点 + 1 个 decision 节点 = 3
        assert len(node_ops) == 3

        # 验证 risk 节点
        risk_ops = [op for op in node_ops if op["node_type"] == NodeType.RISK]
        assert len(risk_ops) == 2

        # 验证 decision 节点
        decision_ops = [
            op for op in node_ops if op["node_type"] == NodeType.DECISION
        ]
        assert len(decision_ops) == 1
        assert decision_ops[0]["label"] == "QA 检查未通过"
        assert decision_ops[0]["props"]["status"] == "pending"

    def test_qa_passed_no_issues(self):
        """无问题时 passed=true → 只有 decision 节点。"""
        translator = QATranslator()
        report = QAReport(
            passed=True,
            issues=[],
            summary="一切正常",
        )
        result = translator.translate(report)

        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1
        assert node_ops[0]["node_type"] == NodeType.DECISION

    def test_qa_passed_with_critical_warning(self):
        """passed=true 但有 critical 问题时产生不一致警告。"""
        translator = QATranslator()
        report = QAReport(
            passed=True,
            issues=[
                IssueSpec(
                    severity="critical",
                    category="missing_file",
                    description="测试不一致",
                    affected_file="test.py",
                ),
            ],
            summary="不一致的报告",
        )
        result = translator.translate(report)

        # 应该产生不一致性警告
        inconsistency_warnings = [
            w for w in result.warnings
            if "passed=true" in w and "critical" in w
        ]
        assert len(inconsistency_warnings) >= 1

    def test_qa_wrong_type(self):
        """传入非 QAReport 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import DocPlan

        translator = QATranslator()
        result = translator.translate(DocPlan(files=[]))

        assert len(result.operations) == 0
        assert "QAReport" in result.warnings[0]

    def test_qa_risk_node_props(self):
        """验证 risk 节点的 props 结构完整。"""
        translator = QATranslator()
        report = _make_qa_failed()
        result = translator.translate(report)

        risk_ops = [
            op for op in result.operations
            if op.get("node_type") == NodeType.RISK
        ]

        for op in risk_ops:
            assert "title" in op["props"]
            assert "description" in op["props"]
            assert "severity" in op["props"]
            assert "status" in op["props"]
            assert op["props"]["severity"] == "high"
            assert op["props"]["status"] == "open"


# ============================================================
# ExportTranslator 测试
# ============================================================

class TestExportTranslator:
    """ExportTranslator 翻译逻辑测试。"""

    def test_export_basic(self):
        """ExportManifest → delivery 节点：正确创建。"""
        translator = ExportTranslator()
        manifest = _make_export_manifest()
        result = translator.translate(manifest)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 应该只有 1 个 delivery 节点
        assert len(node_ops) == 1
        assert node_ops[0]["node_type"] == NodeType.DELIVERY
        assert node_ops[0]["label"] == "TodoApp"

        # 验证 props
        props = node_ops[0]["props"]
        assert props["project_name"] == "TodoApp"
        assert len(props["files"]) == 3
        assert "docker_compose_config" in props
        assert "env_template" in props

    def test_export_docker_compose(self):
        """docker compose 配置校验：缺少服务时产生警告。"""
        translator = ExportTranslator()
        manifest = ExportManifest(
            project_name="IncompleteApp",
            files=[
                FileEntry(
                    source_type="code",
                    source_path="main.py",
                    export_path="main.py",
                ),
            ],
            docker_compose_config={
                "services": {
                    "backend": {"build": "."},
                    # 缺少 frontend、postgres、redis
                },
            },
            env_template={
                "DATABASE_URL": "postgresql://...",
                "REDIS_URL": "redis://...",
                "SECRET_KEY": "secret",
            },
        )
        result = translator.translate(manifest)

        # 应该有缺少服务的警告
        service_warnings = [
            w for w in result.warnings if "缺少必需服务" in w
        ]
        assert len(service_warnings) >= 1

    def test_export_missing_env_keys(self):
        """env_template 缺少必需键时产生警告。"""
        translator = ExportTranslator()
        manifest = ExportManifest(
            project_name="TestApp",
            files=[],
            docker_compose_config={
                "services": {
                    "backend": {},
                    "frontend": {},
                    "postgres": {},
                    "redis": {},
                },
            },
            env_template={
                # 缺少 REDIS_URL 和 SECRET_KEY
                "DATABASE_URL": "postgresql://...",
            },
        )
        result = translator.translate(manifest)

        # 应该有缺少 env 键的警告
        env_warnings = [w for w in result.warnings if "env_template" in w]
        assert len(env_warnings) >= 1

    def test_export_empty_docker_compose(self):
        """docker_compose_config 为空时产生警告。"""
        translator = ExportTranslator()
        manifest = ExportManifest(
            project_name="TestApp",
            files=[],
            docker_compose_config={},
            env_template={
                "DATABASE_URL": "x",
                "REDIS_URL": "x",
                "SECRET_KEY": "x",
            },
        )
        result = translator.translate(manifest)

        # 空 dict 被视为 falsy，应该有警告
        # 注意：空 dict {} 在 Python 中是 falsy
        compose_warnings = [
            w for w in result.warnings
            if "docker_compose_config" in w
        ]
        assert len(compose_warnings) >= 1

    def test_export_wrong_type(self):
        """传入非 ExportManifest 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import QAReport

        translator = ExportTranslator()
        result = translator.translate(
            QAReport(passed=True, summary="test")
        )

        assert len(result.operations) == 0
        assert "ExportManifest" in result.warnings[0]

    def test_export_duplicate_paths_warning(self):
        """重复的 export_path 产生警告。"""
        translator = ExportTranslator()
        manifest = ExportManifest(
            project_name="TestApp",
            files=[
                FileEntry(
                    source_type="code",
                    source_path="a.py",
                    export_path="backend/main.py",
                ),
                FileEntry(
                    source_type="code",
                    source_path="b.py",
                    export_path="backend/main.py",
                ),
            ],
            docker_compose_config={
                "services": {
                    "backend": {},
                    "frontend": {},
                    "postgres": {},
                    "redis": {},
                },
            },
            env_template={
                "DATABASE_URL": "x",
                "REDIS_URL": "x",
                "SECRET_KEY": "x",
            },
        )
        result = translator.translate(manifest)

        # 应该有重复 export_path 的警告
        dup_warnings = [w for w in result.warnings if "重复" in w]
        assert len(dup_warnings) >= 1

    def test_export_invalid_source_type_warning(self):
        """非法 source_type 在 Pydantic Literal 层面被拒绝（验证 FileEntry 的类型约束）。"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FileEntry(
                source_type="invalid",
                source_path="test.txt",
                export_path="test.txt",
            )
