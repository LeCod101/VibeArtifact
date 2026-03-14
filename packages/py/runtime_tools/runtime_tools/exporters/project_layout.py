"""
项目标准目录布局规则模块。

定义生成项目的标准目录结构，提供路径归一化方法，
确保所有产物文件按照 backend/ frontend/ docs/ 三级目录组织。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ============================================================
# 默认目录布局配置
# ============================================================

# 后端文件扩展名 → 默认存放目录
_BACKEND_EXTENSIONS: set[str] = {".py", ".toml", ".cfg", ".ini"}

# 前端文件扩展名 → 默认存放目录
_FRONTEND_EXTENSIONS: set[str] = {
    ".ts", ".tsx", ".js", ".jsx", ".css", ".scss",
    ".json", ".html", ".svg", ".vue",
}

# 路径前缀 → 目标目录映射
# 优先匹配前缀（区分大小写）
_PREFIX_MAP: list[tuple[str, str]] = [
    ("backend/", "backend/"),
    ("frontend/", "frontend/"),
    ("docs/", "docs/"),
    ("docker-compose", ""),
    (".env", ""),
    ("README", ""),
    ("Dockerfile", ""),
]


@dataclass
class LayoutConfig:
    """
    目录布局配置。

    描述产物文件如何映射到标准导出目录结构。
    - backend_dir: 后端代码存放目录
    - frontend_dir: 前端代码存放目录
    - docs_dir: 文档存放目录
    - diagrams_dir: 图表存放子目录
    - root_files: 放在项目根目录的文件名集合
    """

    backend_dir: str = "backend"
    frontend_dir: str = "frontend"
    docs_dir: str = "docs"
    diagrams_dir: str = "docs/diagrams"
    root_files: set[str] = field(default_factory=lambda: {
        "docker-compose.yml",
        ".env.example",
        "README.md",
    })


# 全局默认布局
DEFAULT_LAYOUT = LayoutConfig()


def normalize_path(
    source_type: str,
    original_path: str,
    layout: LayoutConfig | None = None,
) -> str:
    """
    根据来源类型和原始路径，归一化为标准导出路径。

    - source_type: 来源类型，可选 "code" / "doc" / "diagram"
    - original_path: 原始文件路径（如 "backend/main.py"）
    - layout: 目录布局配置，为 None 时使用默认布局
    - 返回: 归一化后的导出路径
    """
    if layout is None:
        layout = DEFAULT_LAYOUT

    # 去除前导斜杠
    path = original_path.lstrip("/")

    # 防御路径遍历攻击：移除所有 ".." 路径段
    # 避免 LLM 输出类似 "../../etc/passwd" 的恶意路径写入 ZIP
    parts = path.replace("\\", "/").split("/")
    parts = [p for p in parts if p != ".."]
    path = "/".join(parts)

    # 图表类型：始终放入 docs/diagrams/ 目录
    if source_type == "diagram":
        # 提取文件名部分
        name = path.rsplit("/", maxsplit=1)[-1]
        if not name.endswith(".md"):
            name = f"{name}.md"
        return f"{layout.diagrams_dir}/{name}"

    # 已有正确前缀的路径直接返回
    for prefix, target in _PREFIX_MAP:
        if path.startswith(prefix):
            return path

    # 根目录文件
    file_name = path.rsplit("/", maxsplit=1)[-1]
    if file_name in layout.root_files:
        return file_name

    # 根据来源类型分配目录
    if source_type == "doc":
        return f"{layout.docs_dir}/{path}"

    if source_type == "code":
        return _assign_code_directory(path, layout)

    # 兜底：保持原路径
    return path


def _assign_code_directory(path: str, layout: LayoutConfig) -> str:
    """
    为代码文件分配目录。

    根据文件扩展名判断属于后端还是前端，
    如果无法判断则保持原路径。

    - path: 文件路径（不含前缀）
    - layout: 目录布局配置
    - 返回: 加上目录前缀后的路径
    """
    # 提取扩展名
    dot_pos = path.rfind(".")
    if dot_pos == -1:
        return path

    ext = path[dot_pos:].lower()

    if ext in _BACKEND_EXTENSIONS:
        return f"{layout.backend_dir}/{path}"
    if ext in _FRONTEND_EXTENSIONS:
        return f"{layout.frontend_dir}/{path}"

    # 无法判断，保持原路径
    return path


def resolve_conflicts(paths: list[str]) -> list[str]:
    """
    解决路径冲突和重复。

    检查路径列表中的重复项，对重复路径添加数字后缀。

    - paths: 待检查的路径列表
    - 返回: 去重后的路径列表（与输入顺序对应）
    """
    seen: dict[str, int] = {}
    result: list[str] = []

    for path in paths:
        if path not in seen:
            seen[path] = 1
            result.append(path)
        else:
            count = seen[path]
            seen[path] = count + 1
            # 在扩展名前插入序号
            dot_pos = path.rfind(".")
            if dot_pos == -1:
                new_path = f"{path}_{count}"
            else:
                new_path = f"{path[:dot_pos]}_{count}{path[dot_pos:]}"
            result.append(new_path)

    return result
