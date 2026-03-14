"""
Backend + Frontend Translator 测试模块。

测试 BackendTranslator 和 FrontendTranslator 将代码计划翻译为
IROperation 列表的逻辑，包括节点创建、层级间依赖边和边界情况。
"""

import pytest
from agents.schemas.high_level import BackendPlan, FileSpec, FrontendPlan
from agents.translators.backend_translator import BackendTranslator
from agents.translators.frontend_translator import FrontendTranslator
from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType


# ============================================================
# 辅助函数
# ============================================================

def _make_backend_plan() -> BackendPlan:
    """构造测试用 BackendPlan，包含多层级文件。"""
    return BackendPlan(
        files=[
            FileSpec(
                path="backend/config.py",
                content="# 配置文件\nDATABASE_URL = 'postgresql://...'",
                language="python",
            ),
            FileSpec(
                path="backend/database.py",
                content="# 数据库连接\nfrom sqlalchemy import create_engine",
                language="python",
            ),
            FileSpec(
                path="backend/models/user.py",
                content="# 用户模型\nclass User: pass",
                language="python",
            ),
            FileSpec(
                path="backend/schemas/user.py",
                content="# 用户 Schema\nclass UserSchema: pass",
                language="python",
            ),
            FileSpec(
                path="backend/routes/user.py",
                content="# 用户路由\nrouter = APIRouter()",
                language="python",
            ),
            FileSpec(
                path="backend/main.py",
                content="# 入口文件\napp = FastAPI()",
                language="python",
            ),
        ],
    )


def _make_frontend_plan() -> FrontendPlan:
    """构造测试用 FrontendPlan，包含多层级文件。"""
    return FrontendPlan(
        files=[
            FileSpec(
                path="frontend/package.json",
                content='{"name": "frontend", "version": "0.1.0"}',
                language="json",
            ),
            FileSpec(
                path="frontend/lib/api.ts",
                content="// API 客户端\nexport const api = {}",
                language="typescript",
            ),
            FileSpec(
                path="frontend/components/TodoList.tsx",
                content="// 待办列表组件\nexport default function TodoList() {}",
                language="typescript",
            ),
            FileSpec(
                path="frontend/app/page.tsx",
                content="// 首页\nexport default function Home() {}",
                language="typescript",
            ),
        ],
    )


# ============================================================
# BackendTranslator 测试
# ============================================================

class TestBackendTranslator:
    """BackendTranslator 翻译逻辑测试。"""

    def test_backend_basic(self):
        """BackendPlan → code 节点：数量和类型正确。"""
        translator = BackendTranslator()
        plan = _make_backend_plan()
        result = translator.translate(plan)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 6 个文件 → 6 个 code 节点
        assert len(node_ops) == 6

        # 验证节点类型都是 code
        for op in node_ops:
            assert op["node_type"] == NodeType.CODE

        # 验证 props 包含必要字段
        for op in node_ops:
            assert "path" in op["props"]
            assert "content" in op["props"]
            assert "language" in op["props"]

    def test_backend_file_deps(self):
        """文件间依赖边正确创建（层级间 depends_on）。"""
        translator = BackendTranslator()
        plan = _make_backend_plan()
        result = translator.translate(plan)

        # 筛选 depends_on 边
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
            and op["edge_type"] == EdgeType.DEPENDS_ON
        ]

        # 层级链：config(0) → database(1) → models(2) → schemas(3) → routes(5) → main(6)
        # 至少应该有层级间的依赖边
        assert len(edge_ops) >= 4

        # 验证边使用 _ref 引用格式
        for op in edge_ops:
            assert op["source_node_id"].startswith("_ref:")
            assert op["target_node_id"].startswith("_ref:")

    def test_empty_files(self):
        """空文件列表返回空操作 + 警告。"""
        translator = BackendTranslator()
        plan = BackendPlan(files=[])
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert len(result.warnings) >= 1
        assert "files 列表为空" in result.warnings[0]

    def test_wrong_type(self):
        """传入非 BackendPlan 类型返回空操作 + 警告。"""
        translator = BackendTranslator()
        wrong = FrontendPlan(files=[])
        result = translator.translate(wrong)

        assert len(result.operations) == 0
        assert "BackendPlan" in result.warnings[0]

    def test_duplicate_path_warning(self):
        """重复文件路径产生警告。"""
        translator = BackendTranslator()
        plan = BackendPlan(
            files=[
                FileSpec(
                    path="backend/main.py",
                    content="# 第一个 main.py",
                    language="python",
                ),
                FileSpec(
                    path="backend/main.py",
                    content="# 重复的 main.py",
                    language="python",
                ),
            ],
        )
        result = translator.translate(plan)

        # 应该有重复路径警告
        dup_warnings = [w for w in result.warnings if "重复" in w]
        assert len(dup_warnings) >= 1

        # 只应创建 1 个节点（第二个被跳过）
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]
        assert len(node_ops) == 1

    def test_non_backend_prefix_warning(self):
        """文件路径不以 backend/ 开头时产生警告。"""
        translator = BackendTranslator()
        plan = BackendPlan(
            files=[
                FileSpec(
                    path="wrong/main.py",
                    content="# 错误前缀",
                    language="python",
                ),
            ],
        )
        result = translator.translate(plan)

        prefix_warnings = [
            w for w in result.warnings if "不以 'backend/' 开头" in w
        ]
        assert len(prefix_warnings) >= 1


# ============================================================
# FrontendTranslator 测试
# ============================================================

class TestFrontendTranslator:
    """FrontendTranslator 翻译逻辑测试。"""

    def test_frontend_basic(self):
        """FrontendPlan → code 节点：数量和类型正确。"""
        translator = FrontendTranslator()
        plan = _make_frontend_plan()
        result = translator.translate(plan)

        # 筛选 create_node 操作
        node_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_NODE
        ]

        # 4 个文件 → 4 个 code 节点
        assert len(node_ops) == 4

        # 验证节点类型都是 code
        for op in node_ops:
            assert op["node_type"] == NodeType.CODE

    def test_frontend_layer_deps(self):
        """前端文件层级间依赖边正确（config → lib → components → app）。"""
        translator = FrontendTranslator()
        plan = _make_frontend_plan()
        result = translator.translate(plan)

        # 筛选 depends_on 边
        edge_ops = [
            op for op in result.operations
            if op["operation_type"] == OperationType.CREATE_EDGE
            and op["edge_type"] == EdgeType.DEPENDS_ON
        ]

        # 层级链：config → lib → components → app
        # 应该有 3 条层级间依赖边
        assert len(edge_ops) >= 3

    def test_empty_files(self):
        """空文件列表返回空操作 + 警告。"""
        translator = FrontendTranslator()
        plan = FrontendPlan(files=[])
        result = translator.translate(plan)

        assert len(result.operations) == 0
        assert "files 列表为空" in result.warnings[0]

    def test_wrong_type(self):
        """传入非 FrontendPlan 类型返回空操作 + 警告。"""
        translator = FrontendTranslator()
        wrong = BackendPlan(files=[])
        result = translator.translate(wrong)

        assert len(result.operations) == 0
        assert "FrontendPlan" in result.warnings[0]

    def test_non_frontend_prefix_warning(self):
        """文件路径不以 frontend/ 开头时产生警告。"""
        translator = FrontendTranslator()
        plan = FrontendPlan(
            files=[
                FileSpec(
                    path="other/page.tsx",
                    content="// 错误前缀",
                    language="typescript",
                ),
            ],
        )
        result = translator.translate(plan)

        prefix_warnings = [
            w for w in result.warnings if "不以 'frontend/' 开头" in w
        ]
        assert len(prefix_warnings) >= 1
