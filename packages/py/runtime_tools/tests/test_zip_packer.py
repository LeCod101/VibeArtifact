"""
ZIP 打包器测试模块。

测试 ZipPacker、project_layout 路径归一化、
compose_gen 配置生成和 ArtifactCollector 收集逻辑。
"""

import io
import tempfile
import zipfile
from pathlib import Path

import pytest

from runtime_tools.exporters.collector import ArtifactCollector, FileEntry
from runtime_tools.exporters.compose_gen import (
    generate_compose,
    generate_env_example,
)
from runtime_tools.exporters.project_layout import normalize_path, resolve_conflicts
from runtime_tools.exporters.zip_packer import ZipPacker


# ============================================================
# ZipPacker 测试
# ============================================================

class TestZipPacker:
    """ZIP 打包器测试。"""

    def test_pack_to_bytes(self):
        """打包后解压验证文件内容。"""
        files = [
            FileEntry(
                export_path="backend/main.py",
                content="# 入口文件\napp = FastAPI()",
            ),
            FileEntry(
                export_path="frontend/app/page.tsx",
                content="// 首页组件\nexport default function Home() {}",
            ),
            FileEntry(
                export_path="README.md",
                content="# TodoApp\n\n这是一个待办事项应用。",
            ),
        ]

        packer = ZipPacker(project_name="TodoApp", files=files)
        zip_bytes = packer.pack_to_bytes()

        # 验证返回的是非空 bytes
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0

        # 解压验证内容
        buf = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()

            # 验证文件在 {project_name}/ 根目录下
            assert "TodoApp/backend/main.py" in names
            assert "TodoApp/frontend/app/page.tsx" in names
            assert "TodoApp/README.md" in names

            # 验证文件内容
            main_content = zf.read("TodoApp/backend/main.py").decode("utf-8")
            assert "FastAPI" in main_content

            readme_content = zf.read("TodoApp/README.md").decode("utf-8")
            assert "TodoApp" in readme_content

    def test_pack_to_file(self):
        """写入文件后验证。"""
        files = [
            FileEntry(
                export_path="test.py",
                content="print('hello')",
            ),
        ]

        packer = ZipPacker(project_name="test_project", files=files)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.zip"
            result_path = packer.pack_to_file(output_path)

            # 验证文件存在
            assert result_path.exists()

            # 验证是有效的 ZIP 文件
            with zipfile.ZipFile(result_path, "r") as zf:
                names = zf.namelist()
                assert "test_project/test.py" in names

                content = zf.read("test_project/test.py").decode("utf-8")
                assert content == "print('hello')"

    def test_pack_empty_files(self):
        """空文件列表打包应该生成有效的空 ZIP。"""
        packer = ZipPacker(project_name="empty", files=[])
        zip_bytes = packer.pack_to_bytes()

        assert isinstance(zip_bytes, bytes)
        buf = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buf, "r") as zf:
            assert len(zf.namelist()) == 0

    def test_pack_chinese_content(self):
        """中文内容正确编码打包。"""
        files = [
            FileEntry(
                export_path="docs/readme.md",
                content="# 待办事项应用\n\n这是一个用中文编写的文档。",
            ),
        ]

        packer = ZipPacker(project_name="中文项目", files=files)
        zip_bytes = packer.pack_to_bytes()

        buf = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buf, "r") as zf:
            content = zf.read("中文项目/docs/readme.md").decode("utf-8")
            assert "待办事项应用" in content


# ============================================================
# project_layout 路径归一化测试
# ============================================================

class TestProjectLayout:
    """项目目录布局路径归一化测试。"""

    def test_code_backend_path(self):
        """backend/ 前缀的代码文件路径保持不变。"""
        result = normalize_path("code", "backend/main.py")
        assert result == "backend/main.py"

    def test_code_frontend_path(self):
        """frontend/ 前缀的代码文件路径保持不变。"""
        result = normalize_path("code", "frontend/app/page.tsx")
        assert result == "frontend/app/page.tsx"

    def test_doc_path(self):
        """文档文件归一化到 docs/ 目录。"""
        result = normalize_path("doc", "api.md")
        assert result == "docs/api.md"

    def test_diagram_path(self):
        """图表文件归一化到 docs/diagrams/ 目录。"""
        result = normalize_path("diagram", "er_diagram")
        assert result == "docs/diagrams/er_diagram.md"

    def test_diagram_with_md_extension(self):
        """已有 .md 扩展名的图表文件不重复添加。"""
        result = normalize_path("diagram", "er.md")
        assert result == "docs/diagrams/er.md"

    def test_root_files_recognized(self):
        """根目录文件（如 README.md）被正确识别。"""
        result = normalize_path("doc", "README.md")
        assert result == "README.md"

    def test_leading_slash_stripped(self):
        """前导斜杠被去除。"""
        result = normalize_path("code", "/backend/main.py")
        assert result == "backend/main.py"

    def test_resolve_conflicts_no_duplicates(self):
        """无重复路径时原样返回。"""
        paths = ["a.py", "b.py", "c.py"]
        result = resolve_conflicts(paths)
        assert result == paths

    def test_resolve_conflicts_with_duplicates(self):
        """有重复路径时添加序号后缀。"""
        paths = ["main.py", "main.py", "main.py"]
        result = resolve_conflicts(paths)
        assert result[0] == "main.py"
        assert result[1] == "main_1.py"
        assert result[2] == "main_2.py"


# ============================================================
# compose_gen 测试
# ============================================================

class TestComposeGen:
    """Docker Compose 配置生成测试。"""

    def test_compose_gen(self):
        """docker-compose.yml 生成包含四个必需服务。"""
        compose = generate_compose("TodoApp")

        # 验证包含四个服务
        assert "backend:" in compose
        assert "frontend:" in compose
        assert "postgres:" in compose
        assert "redis:" in compose

        # 验证端口映射
        assert "8000" in compose
        assert "3000" in compose
        assert "5432" in compose
        assert "6379" in compose

        # 验证 Docker 安全名称转换
        assert "todoapp" in compose

    def test_compose_gen_special_chars(self):
        """项目名称中的特殊字符被安全处理。"""
        compose = generate_compose("My App-2024")

        # 验证不包含空格和连字符
        assert "my_app_2024" in compose

    def test_env_example_gen(self):
        """生成 .env.example 包含必需环境变量。"""
        env = generate_env_example("TodoApp")

        # 验证必需键
        assert "DATABASE_URL" in env
        assert "REDIS_URL" in env
        assert "SECRET_KEY" in env
        assert "POSTGRES_PASSWORD" in env

    def test_env_example_project_name(self):
        """.env.example 中包含项目名称。"""
        env = generate_env_example("MyProject")

        # 验证项目名出现在注释或值中
        assert "MyProject" in env or "myproject" in env


# ============================================================
# ArtifactCollector 测试
# ============================================================

class TestArtifactCollector:
    """产物收集器测试。"""

    def test_collector(self):
        """ArtifactCollector 正确收集 code/doc/diagram 节点。"""
        nodes = [
            {
                "node_type": "code",
                "props": {
                    "path": "backend/main.py",
                    "content": "app = FastAPI()",
                    "language": "python",
                },
            },
            {
                "node_type": "doc",
                "props": {
                    "path": "README.md",
                    "content": "# TodoApp",
                    "format": "markdown",
                },
            },
            {
                "node_type": "diagram",
                "props": {
                    "name": "ER 图",
                    "diagram_type": "er",
                    "content": "erDiagram\n    User ||--o{ Todo : has",
                    "description": "数据库关系图",
                },
            },
            # 非收集类型，应被忽略
            {
                "node_type": "scope",
                "props": {
                    "name": "功能1",
                    "description": "描述",
                },
            },
        ]

        collector = ArtifactCollector()
        entries = collector.collect(nodes)

        # 应该收集 3 个文件（code + doc + diagram）
        assert len(entries) == 3

        # 验证导出路径
        paths = [e.export_path for e in entries]
        assert "backend/main.py" in paths
        assert "README.md" in paths
        # diagram 应该被归一化到 docs/diagrams/
        diagram_paths = [p for p in paths if "diagrams" in p]
        assert len(diagram_paths) == 1

    def test_collector_empty_content_skipped(self):
        """content 为空的节点被跳过。"""
        nodes = [
            {
                "node_type": "code",
                "props": {
                    "path": "empty.py",
                    "content": "",
                    "language": "python",
                },
            },
        ]

        collector = ArtifactCollector()
        entries = collector.collect(nodes)

        assert len(entries) == 0

    def test_collector_empty_nodes(self):
        """空节点列表返回空集合。"""
        collector = ArtifactCollector()
        entries = collector.collect([])
        assert len(entries) == 0

    def test_collector_no_props_skipped(self):
        """没有 props 的节点被跳过。"""
        nodes = [
            {"node_type": "code"},
            {"node_type": "doc", "props": {}},
        ]

        collector = ArtifactCollector()
        entries = collector.collect(nodes)

        assert len(entries) == 0

    def test_collector_diagram_content_format(self):
        """diagram 节点导出的内容包含 Mermaid 代码块。"""
        nodes = [
            {
                "node_type": "diagram",
                "props": {
                    "name": "测试图",
                    "diagram_type": "flowchart",
                    "content": "graph LR\n    A --> B",
                    "description": "流程图",
                },
            },
        ]

        collector = ArtifactCollector()
        entries = collector.collect(nodes)

        assert len(entries) == 1
        content = entries[0].content
        # 验证 Markdown 格式
        assert "# 测试图" in content
        assert "```mermaid" in content
        assert "graph LR" in content
        assert "```" in content
