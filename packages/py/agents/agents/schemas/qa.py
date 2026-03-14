"""
QA Agent 的输入输出 Schema 定义。

QA Agent 负责对所有前置 agent 的产物进行结构性完整性检查，
输出 QAReport（质量检查报告）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import QAReport


class QAInput(AgentInput):
    """
    QA Agent 专用输入。

    在 AgentInput 基础上添加产物摘要信息。
    - file_list: 所有已生成文件的路径列表
    - endpoint_list: SchemaPlan 中定义的端点摘要列表
    - entity_list: SchemaPlan 中定义的实体摘要列表
    - page_list: 前端页面路由列表
    """

    file_list: list[str] = []
    endpoint_list: list[dict] = []
    entity_list: list[dict] = []
    page_list: list[str] = []


class QAOutput(AgentOutput):
    """
    QA Agent 专用输出。

    在 AgentOutput 基础上添加质量检查报告。
    - qa_report: 质量检查结果，包含 passed/issues/summary
    """

    qa_report: QAReport
