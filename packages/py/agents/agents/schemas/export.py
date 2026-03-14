"""
Export Agent 的输入输出 Schema 定义。

Export Agent 负责汇总所有产物并生成交付清单，
输出 ExportManifest（包含文件列表、Docker Compose 配置、环境变量模板）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import ExportManifest, QAReport


class ExportInput(AgentInput):
    """
    Export Agent 专用输入。

    在 AgentInput 基础上添加产物摘要和 QA 报告。
    - artifact_paths: 所有待导出的产物文件路径列表（含类型标记）
    - qa_report: QA Agent 的检查报告（可选，QA 可能跳过）
    """

    artifact_paths: list[dict] = []
    qa_report: QAReport | None = None


class ExportOutput(AgentOutput):
    """
    Export Agent 专用输出。

    在 AgentOutput 基础上添加导出清单。
    - export_manifest: 完整的导出清单
    """

    export_manifest: ExportManifest
