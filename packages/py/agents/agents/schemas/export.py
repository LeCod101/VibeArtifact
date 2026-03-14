"""
Export Agent 的输入输出 Schema 定义。

Export Agent 负责将生成的产物打包导出，
输出 ExportManifest（导出清单）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ExportManifest


class ExportInput(AgentInput):
    """
    Export Agent 专用输入。

    在 AgentInput 基础上添加待导出的产物路径列表。
    - artifact_paths: 所有待导出的产物文件路径列表
    """

    artifact_paths: list[str]


class ExportOutput(AgentOutput):
    """
    Export Agent 专用输出。

    在 AgentOutput 基础上添加导出清单。
    - export_manifest: 导出的产物清单
    """

    export_manifest: ExportManifest
