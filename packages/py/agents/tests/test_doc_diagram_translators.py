"""
Doc + Diagram Translator 测试模块。

测试 DocTranslator 和 DiagramTranslator 的翻译逻辑，
包括基础翻译、缺少必要文件/图表的处理和边界情况。
"""

from agents.schemas.high_level import (
    DiagramPlan,
    DiagramSpec,
    DocPlan,
    FileSpec,
)
from agents.translators.diagram_translator import DiagramTranslator
from agents.translators.doc_translator import DocTranslator
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType

# ============================================================
# 辅助函数
# ============================================================

def _make_doc_plan() -> DocPlan:
    """构造标准的 DocPlan，包含 README.md 和 docs/api.md。"""
    return DocPlan(
        files=[
            FileSpec(
                path="README.md",
                content="# TodoApp\n\n这是一个待办事项应用。",
                language="markdown",
            ),
            FileSpec(
                path="docs/api.md",
                content="# API 文档\n\n## GET /api/todos\n\n获取所有待办事项。",
                language="markdown",
            ),
            FileSpec(
                path="docs/setup.md",
                content="# 部署指南\n\n## Docker Compose 启动",
                language="markdown",
            ),
        ],
    )


def _make_diagram_plan() -> DiagramPlan:
    """构造标准的 DiagramPlan，包含 ER 图和架构图。"""
    return DiagramPlan(
        diagrams=[
            DiagramSpec(
                title="数据库 ER 图",
                diagram_type="er",
                mermaid_code="erDiagram\n    User ||--o{ Todo : has",
            ),
            DiagramSpec(
                title="系统架构图",
                diagram_type="flowchart",
                mermaid_code="graph LR\n    A[前端] --> B[后端]\n    B --> C[数据库]",
            ),
        ],
    )


# ============================================================
# DocTranslator 测试
# ============================================================

class TestDocTranslator:
    """DocTranslator 翻译逻辑测试。"""

    def test_doc_basic(self):
        """DocPlan → doc 节点：数量和类型正确。"""
        translator = DocTranslator()
        plan = _make_doc_plan()
        result = translator.translate(plan)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 3 个文件 → 3 个 doc 节点
        assert len(node_ops) == 3

        # 验证节点类型都是 doc
        for op in node_ops:
            assert op["node_type"] == NodeType.DOC

        # 验证 props 包含 path, content, format
        for op in node_ops:
            assert "path" in op["props"]
            assert "content" in op["props"]
            assert op["props"]["format"] == "markdown"

    def test_doc_requires_readme(self):
        """缺少 README.md 时产生警告。"""
        translator = DocTranslator()
        plan = DocPlan(
            files=[
                FileSpec(
                    path="docs/api.md",
                    content="# API 文档",
                    language="markdown",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有缺少 README.md 的警告
        readme_warnings = [
            w for w in result.warnings if "README.md" in w
        ]
        assert len(readme_warnings) >= 1

    def test_doc_requires_api_md(self):
        """缺少 docs/api.md 时产生警告。"""
        translator = DocTranslator()
        plan = DocPlan(
            files=[
                FileSpec(
                    path="README.md",
                    content="# TodoApp",
                    language="markdown",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有缺少 docs/api.md 的警告
        api_warnings = [
            w for w in result.warnings if "docs/api.md" in w
        ]
        assert len(api_warnings) >= 1

    def test_doc_empty_files(self):
        """空 files 列表返回空操作 + 警告。"""
        translator = DocTranslator()
        plan = DocPlan(files=[])
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert "files 列表为空" in result.warnings[0]

    def test_doc_empty_content_skipped(self):
        """content 为空的文件被跳过并产生警告。"""
        translator = DocTranslator()
        plan = DocPlan(
            files=[
                FileSpec(
                    path="README.md",
                    content="",
                    language="markdown",
                ),
                FileSpec(
                    path="docs/api.md",
                    content="# API 文档",
                    language="markdown",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该只创建 1 个节点（README.md 被跳过）
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1

        # 应该有 content 为空的警告
        empty_warnings = [w for w in result.warnings if "content 为空" in w]
        assert len(empty_warnings) >= 1

    def test_doc_wrong_type(self):
        """传入非 DocPlan 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import BackendPlan

        translator = DocTranslator()
        result = translator.translate(BackendPlan(files=[]))

        assert len(result.operations) == 0
        assert "DocPlan" in result.warnings[0]


# ============================================================
# DiagramTranslator 测试
# ============================================================

class TestDiagramTranslator:
    """DiagramTranslator 翻译逻辑测试。"""

    def test_diagram_basic(self):
        """DiagramPlan → diagram 节点：数量和类型正确。"""
        translator = DiagramTranslator()
        plan = _make_diagram_plan()
        result = translator.translate(plan)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 2 个图表 → 2 个 diagram 节点
        assert len(node_ops) == 2

        # 验证节点类型都是 diagram
        for op in node_ops:
            assert op["node_type"] == NodeType.DIAGRAM

        # 验证 props 包含必要字段
        for op in node_ops:
            assert "name" in op["props"]
            assert "diagram_type" in op["props"]
            assert "content" in op["props"]

    def test_diagram_min_two(self):
        """图表数量不足 2 个时产生警告。"""
        translator = DiagramTranslator()
        plan = DiagramPlan(
            diagrams=[
                DiagramSpec(
                    title="仅一个图表",
                    diagram_type="er",
                    mermaid_code="erDiagram\n    User {}",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有数量不足的警告
        count_warnings = [
            w for w in result.warnings if "至少需要 2 个" in w
        ]
        assert len(count_warnings) >= 1

        # 但仍然应该创建节点
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1

    def test_diagram_empty(self):
        """空 diagrams 列表返回空操作 + 警告。"""
        translator = DiagramTranslator()
        plan = DiagramPlan(diagrams=[])
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert "diagrams 列表为空" in result.warnings[0]

    def test_diagram_missing_required_types(self):
        """缺少必须的图表类型（er/flowchart）产生警告。"""
        translator = DiagramTranslator()
        plan = DiagramPlan(
            diagrams=[
                DiagramSpec(
                    title="序列图",
                    diagram_type="sequence",
                    mermaid_code="sequenceDiagram\n    A->>B: 请求",
                ),
                DiagramSpec(
                    title="类图",
                    diagram_type="classDiagram",
                    mermaid_code="classDiagram\n    class User",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有缺少必须类型的警告
        type_warnings = [
            w for w in result.warnings if "缺少必须的图表类型" in w
        ]
        assert len(type_warnings) >= 1

    def test_diagram_empty_mermaid_skipped(self):
        """mermaid_code 为空的图表被跳过。"""
        translator = DiagramTranslator()
        plan = DiagramPlan(
            diagrams=[
                DiagramSpec(
                    title="空图表",
                    diagram_type="er",
                    mermaid_code="",
                ),
                DiagramSpec(
                    title="正常图表",
                    diagram_type="flowchart",
                    mermaid_code="graph LR\n    A --> B",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该只创建 1 个节点
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1

        # 应该有 mermaid_code 为空的警告
        empty_warnings = [
            w for w in result.warnings if "mermaid_code 为空" in w
        ]
        assert len(empty_warnings) >= 1

    def test_diagram_wrong_type(self):
        """传入非 DiagramPlan 类型返回空操作 + 警告。"""
        from agents.schemas.high_level import DocPlan

        translator = DiagramTranslator()
        result = translator.translate(DocPlan(files=[]))

        assert len(result.operations) == 0
        assert "DiagramPlan" in result.warnings[0]

    def test_diagram_mermaid_prefix_mismatch(self):
        """Mermaid 代码起始关键字与图表类型不匹配时产生警告。"""
        translator = DiagramTranslator()
        plan = DiagramPlan(
            diagrams=[
                DiagramSpec(
                    title="ER 图",
                    diagram_type="er",
                    # er 类型应该以 erDiagram 开头，但用了 graph
                    mermaid_code="graph LR\n    A --> B",
                ),
                DiagramSpec(
                    title="架构图",
                    diagram_type="flowchart",
                    mermaid_code="graph LR\n    A --> B",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有 prefix 不匹配的警告（ER 图）
        prefix_warnings = [
            w for w in result.warnings
            if "未以" in w and "erDiagram" in w
        ]
        assert len(prefix_warnings) >= 1
