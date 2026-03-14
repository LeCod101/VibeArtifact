"""
ExportTranslator 模块 — 导出翻译器。

将 export agent 输出的 ExportManifest 翻译为 IROperation 列表。

翻译规则：
1. 创建一个 delivery 节点，props 包含 ExportManifest 的全部内容
2. 节点 label 为项目名称
3. 校验必需的 Docker Compose 服务和环境变量键
"""

from ir_core.schema.node_types import NodeType
from ir_core.schema.operation_types import OperationType
from pydantic import BaseModel

from agents.schemas.high_level import ExportManifest

from .base import BaseTranslator, TranslatorResult

# Docker Compose 必需的四个服务
REQUIRED_SERVICES = frozenset({
    "backend", "frontend", "postgres", "redis",
})

# .env.example 必需的键
REQUIRED_ENV_KEYS = frozenset({
    "DATABASE_URL", "REDIS_URL", "SECRET_KEY",
})

# 合法的文件来源类型
VALID_SOURCE_TYPES = frozenset({"code", "doc", "diagram"})


class ExportTranslator(BaseTranslator):
    """
    导出翻译器。

    将 ExportManifest（导出清单）翻译为 IR 操作列表。
    产生一个 delivery 类型的 IR 节点，包含完整的导出清单信息。
    """

    def translate(self, high_level_output: BaseModel) -> TranslatorResult:
        """
        将 ExportManifest 翻译为 IROperation 列表。

        翻译逻辑：
        1. 校验输入类型
        2. 校验 files 列表的合法性
        3. 校验 docker_compose_config 必需服务
        4. 校验 env_template 必需键
        5. 创建 delivery 节点

        - high_level_output: ExportManifest 实例
        - 返回: TranslatorResult，包含创建节点的操作列表
        """
        if not isinstance(high_level_output, ExportManifest):
            return TranslatorResult(
                operations=[],
                warnings=[
                    "ExportTranslator 期望 ExportManifest 类型，实际收到 "
                    f"{type(high_level_output).__name__}"
                ],
            )

        manifest: ExportManifest = high_level_output
        operations: list[dict] = []
        warnings: list[str] = []

        # ==============================
        # 校验阶段
        # ==============================

        # 检查 files 列表是否为空
        if not manifest.files:
            warnings.append(
                "files 列表为空，导出清单至少需要包含一个文件条目"
            )

        # 校验文件来源类型和路径
        export_paths_seen: set[str] = set()
        for idx, entry in enumerate(manifest.files):
            if entry.source_type not in VALID_SOURCE_TYPES:
                warnings.append(
                    f"第 {idx + 1} 个文件条目的 source_type "
                    f"'{entry.source_type}' 不在合法取值范围内，"
                    f"合法值：{', '.join(sorted(VALID_SOURCE_TYPES))}"
                )
            if not entry.source_path or not entry.source_path.strip():
                warnings.append(
                    f"第 {idx + 1} 个文件条目的 source_path 为空"
                )
            if not entry.export_path or not entry.export_path.strip():
                warnings.append(
                    f"第 {idx + 1} 个文件条目的 export_path 为空"
                )
            elif entry.export_path in export_paths_seen:
                warnings.append(
                    f"export_path '{entry.export_path}' 重复出现，"
                    "导出路径不可重复"
                )
            else:
                export_paths_seen.add(entry.export_path)

        # 校验 Docker Compose 必需服务
        if manifest.docker_compose_config:
            services = manifest.docker_compose_config.get("services", {})
            if isinstance(services, dict):
                existing_services = set(services.keys())
                missing_services = REQUIRED_SERVICES - existing_services
                if missing_services:
                    missing_str = "、".join(sorted(missing_services))
                    warnings.append(
                        f"docker_compose_config 缺少必需服务：{missing_str}，"
                        "必须包含 backend / frontend / postgres / redis"
                    )
            else:
                warnings.append(
                    "docker_compose_config.services 格式不正确，应为字典类型"
                )
        else:
            warnings.append(
                "docker_compose_config 为空，"
                "必须包含 backend / frontend / postgres / redis 四个服务配置"
            )

        # 校验 .env 必需键
        if manifest.env_template:
            existing_keys = set(manifest.env_template.keys())
            missing_keys = REQUIRED_ENV_KEYS - existing_keys
            if missing_keys:
                missing_str = "、".join(sorted(missing_keys))
                warnings.append(
                    f"env_template 缺少必需键：{missing_str}"
                )
        else:
            warnings.append(
                "env_template 为空，"
                "至少需要包含 DATABASE_URL / REDIS_URL / SECRET_KEY"
            )

        # ==============================
        # 创建 delivery 节点
        # ==============================
        # 将 FileEntry 列表序列化为 dict 列表
        files_data = [entry.model_dump() for entry in manifest.files]

        delivery_op = {
            "operation_type": OperationType.CREATE_NODE,
            "node_type": NodeType.DELIVERY,
            "label": manifest.project_name,
            "props": {
                "project_name": manifest.project_name,
                "files": files_data,
                "docker_compose_config": manifest.docker_compose_config,
                "env_template": manifest.env_template,
            },
        }
        operations.append(delivery_op)

        return TranslatorResult(operations=operations, warnings=warnings)
