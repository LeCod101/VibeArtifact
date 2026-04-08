"""
产物收集与 ZIP 打包测试。

测试覆盖：
1. ArtifactCollector 产物收集
2. ZipPacker ZIP 打包
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# 产物收集（无外部依赖）
# ──────────────────────────────────────────────


class TestExportCollectsArtifacts:
    """验证 ArtifactCollector 能从 IR 节点收集产物。"""

    def test_collector_extracts_code_nodes(self):
        """code 类型节点被正确收集。"""
        from runtime_tools.exporters.collector import ArtifactCollector

        nodes = [
            {
                "node_type": "code",
                "label": "main.py",
                "props": {
                    "path": "backend/main.py",
                    "content": "print('hello')",
                    "language": "python",
                },
            },
            {
                "node_type": "entity",
                "label": "User",
                "props": {"name": "User"},
            },
        ]

        collector = ArtifactCollector()
        files = collector.collect(nodes)

        assert len(files) == 1
        assert files[0].export_path == "backend/main.py"
        assert files[0].content == "print('hello')"

    def test_collector_extracts_doc_nodes(self):
        """doc 类型节点被正确收集。"""
        from runtime_tools.exporters.collector import ArtifactCollector

        nodes = [
            {
                "node_type": "doc",
                "label": "README",
                "props": {
                    "path": "README.md",
                    "content": "# Hello",
                    "format": "markdown",
                },
            },
        ]

        collector = ArtifactCollector()
        files = collector.collect(nodes)

        assert len(files) == 1
        assert files[0].export_path == "README.md"


# ──────────────────────────────────────────────
# ZIP 打包（无外部依赖）
# ──────────────────────────────────────────────


class TestZipHasFiles:
    """验证 ZIP 包含实际文件内容。"""

    def test_zip_contains_files(self):
        """ZipPacker 生成的 ZIP 包含指定文件。"""
        import io
        import zipfile

        from runtime_tools.exporters.collector import FileEntry
        from runtime_tools.exporters.zip_packer import ZipPacker

        files = [
            FileEntry(
                export_path="src/main.py",
                content="print('hello world')",
            ),
            FileEntry(
                export_path="README.md",
                content="# Test Project",
            ),
        ]

        packer = ZipPacker(project_name="test_project", files=files)
        zip_bytes = packer.pack_to_bytes()

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            assert "test_project/src/main.py" in names
            assert "test_project/README.md" in names

            main_content = zf.read("test_project/src/main.py").decode("utf-8")
            assert main_content == "print('hello world')"

    def test_zip_empty_collection(self):
        """空文件列表生成空 ZIP。"""
        import io
        import zipfile

        from runtime_tools.exporters.zip_packer import ZipPacker

        packer = ZipPacker(project_name="empty", files=[])
        zip_bytes = packer.pack_to_bytes()

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert len(zf.namelist()) == 0
