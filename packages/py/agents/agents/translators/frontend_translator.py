"""
FrontendTranslator 模块 — 前端代码翻译器。

将 frontend agent 输出的 FrontendPlan 翻译为 IROperation 列表。

翻译规则：
1. 每个 FileSpec → create_node（类型 code）
2. props 包含 path、content、language
3. 文件间根据目录层级创建 depends_on 边
   （lib → components → app/pages → 配置文件）
"""

from ir_core.schema.edge_types import EdgeType
from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import FrontendPlan

from .base import BaseTranslator, TranslatorResult

# 前端文件的依赖优先级层级
# 数字越小表示越底层
_FRONTEND_LAYER_ORDER = {
    "config": 0,
    "lib": 1,
    "components": 2,
    "app": 3,
}

# 合法的前端代码 language 值
VALID_FRONTEND_LANGUAGES = frozenset({
    "typescript", "javascript", "css", "json", "dockerfile",
})


def _classify_frontend_file(path: str) -> str | None:
    """
    根据文件路径判断所属层级。

    - path: 文件路径（如 "frontend/app/todos/page.tsx"）
    - 返回: 层级名称（如 "app"）或 None
    """
    # 去除 "frontend/" 前缀
    cleaned = path.replace("\\", "/")
    if cleaned.startswith("frontend/"):
        cleaned = cleaned[len("frontend/"):]

    # 配置文件匹配
    config_files = {
        "package.json", "tsconfig.json", "tailwind.config.ts",
        "next.config.mjs", "postcss.config.mjs", "Dockerfile",
    }
    basename = cleaned.split("/")[-1]
    if basename in config_files or cleaned in config_files:
        return "config"

    # 目录匹配
    first_dir = cleaned.split("/")[0] if "/" in cleaned else None
    if first_dir in _FRONTEND_LAYER_ORDER:
        return first_dir

    return None


class FrontendTranslator(BaseTranslator):
    """
    前端代码翻译器。

    将 FrontendPlan（前端代码文件列表）翻译为 IR 操作列表。
    产生 code 类型节点，以及文件间的 depends_on 关联边。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 FrontendPlan 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型
        2. 为每个 FileSpec 创建 code 类型节点
        3. 根据文件所属层级创建 depends_on 边

        - high_level_output: FrontendPlan 实例
        - 返回: TranslatorResult，包含创建节点和边的操作列表
        """
        if not isinstance(high_level_output, FrontendPlan):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "FrontendTranslator 期望 FrontendPlan 类型，"
                    f"实际收到 {type(high_level_output).__name__}"
                ],
            )

        plan: FrontendPlan = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # 边界检查：文件列表为空
        if not plan.files:
            return TranslatorResult(
                operations=[],
                warnings=["files 列表为空，至少需要一个文件"],
            )

        # 记录路径到操作索引的映射
        path_to_op_index: dict[str, int] = {}
        # 记录层级到操作索引列表的映射
        layer_to_op_indices: dict[str, list[int]] = {}
        # 检测重复路径
        seen_paths: set[str] = set()

        # ==============================
        # 阶段 1: 创建 code 节点
        # ==============================
        for file_spec in plan.files:
            # 路径校验
            normalized_path = file_spec.path.replace("\\", "/")
            if not normalized_path.startswith("frontend/"):
                warnings.append(
                    f"文件路径 '{file_spec.path}' 不以 'frontend/' 开头"
                )

            # 重复路径检测
            if normalized_path in seen_paths:
                warnings.append(
                    f"检测到重复文件路径: '{normalized_path}'"
                )
                continue
            seen_paths.add(normalized_path)

            # 内容校验
            if not file_spec.content or not file_spec.content.strip():
                warnings.append(
                    f"文件 '{normalized_path}' 的 content 为空"
                )

            # language 校验
            if file_spec.language not in VALID_FRONTEND_LANGUAGES:
                warnings.append(
                    f"文件 '{normalized_path}' 使用了非标准 language "
                    f"'{file_spec.language}'，"
                    f"建议使用：{', '.join(sorted(VALID_FRONTEND_LANGUAGES))}"
                )

            # 从路径中提取文件名作为标签
            label = normalized_path.split("/")[-1]

            op = {
                "operation_type": OperationType.CREATE_NODE,
                "node_type": NodeType.CODE,
                "label": label,
                "props": {
                    "path": normalized_path,
                    "content": file_spec.content,
                    "language": file_spec.language,
                },
            }

            op_index = len(operations)
            path_to_op_index[normalized_path] = op_index
            operations.append(op)

            # 归类到层级
            layer = _classify_frontend_file(normalized_path)
            if layer is not None:
                layer_to_op_indices.setdefault(layer, []).append(op_index)

        # ==============================
        # 阶段 2: 创建层级间 depends_on 边
        # ==============================
        # 依赖链: config → lib → components → app
        # 高层级的文件依赖低层级的文件
        sorted_layers = sorted(
            layer_to_op_indices.keys(),
            key=lambda x: _FRONTEND_LAYER_ORDER.get(x, 99),
        )

        for i in range(1, len(sorted_layers)):
            current_layer = sorted_layers[i]
            prev_layer = sorted_layers[i - 1]
            current_indices = layer_to_op_indices[current_layer]
            prev_indices = layer_to_op_indices[prev_layer]

            # 当前层的每个文件都依赖上一层的第一个文件（代表性依赖）
            if prev_indices:
                representative_prev = prev_indices[0]
                for cur_idx in current_indices:
                    edge_op = {
                        "operation_type": OperationType.CREATE_EDGE,
                        "edge_type": EdgeType.DEPENDS_ON,
                        "source_node_id": f"_ref:{cur_idx}",
                        "target_node_id": f"_ref:{representative_prev}",
                    }
                    operations.append(edge_op)

        return TranslatorResult(operations=operations, warnings=warnings)
