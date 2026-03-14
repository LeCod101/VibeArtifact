"""
QA Agent 的输入输出 Schema 定义。

QA Agent 负责检查生成的代码文件质量，
发现问题并输出 FixPlan（修复计划）。
"""

from agents.schemas.base import AgentInput, AgentOutput
from agents.schemas.high_level import FixPlan


class QAInput(AgentInput):
    """
    QA Agent 专用输入。

    在 AgentInput 基础上添加待检查的代码文件内容。
    - file_contents: 文件路径到文件内容的映射，key 为文件路径，value 为文件内容
    """

    file_contents: dict[str, str]


class QAOutput(AgentOutput):
    """
    QA Agent 专用输出。

    在 AgentOutput 基础上添加修复计划。
    - fix_plan: 质量检查结果和需要修复的问题列表
    """

    fix_plan: FixPlan
