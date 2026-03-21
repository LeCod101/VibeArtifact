"""
10 个 Agent 的角色 Prompt 模板。

每个 prompt 包含角色定义、输入说明、输出说明和约束。
intent、contraction、planner、schema(部分)、backend、frontend、doc、diagram、qa、export agent
已完成精细化 prompt engineering。

支持通过 agent name（小写字符串）索引获取对应的角色 prompt。
"""

from agents.prompts.templates.backend_role import BACKEND_ROLE_PROMPT
from agents.prompts.templates.contraction_role import CONTRACTION_ROLE_PROMPT
from agents.prompts.templates.diagram_role import DIAGRAM_ROLE_PROMPT
from agents.prompts.templates.doc_role import DOC_ROLE_PROMPT
from agents.prompts.templates.export_role import EXPORT_ROLE_PROMPT
from agents.prompts.templates.frontend_role import FRONTEND_ROLE_PROMPT
from agents.prompts.templates.intent_role import INTENT_ROLE_PROMPT
from agents.prompts.templates.planner_role import PLANNER_ROLE_PROMPT
from agents.prompts.templates.qa_role import QA_ROLE_PROMPT
from agents.prompts.templates.schema_role import SCHEMA_ROLE_PROMPT

ROLE_PROMPTS: dict[str, str] = {
    # ================================================================
    # Intent Agent — 意图理解专家（M4 完整 prompt）
    # ================================================================
    "intent": INTENT_ROLE_PROMPT,

    # ================================================================
    # Contraction Agent — MVP 收缩专家（完整 prompt 从 contraction_role.py 导入）
    # ================================================================
    "contraction": CONTRACTION_ROLE_PROMPT,

    # ================================================================
    # Planner Agent — 任务规划专家（M5 完整 prompt）
    # ================================================================
    "planner": PLANNER_ROLE_PROMPT,

    # ================================================================
    # Schema Agent — 数据建模专家
    # ================================================================
    "schema": SCHEMA_ROLE_PROMPT,

    # ================================================================
    # Backend Agent — 后端开发专家（M5 完整 prompt）
    # ================================================================
    "backend": BACKEND_ROLE_PROMPT,

    # ================================================================
    # Frontend Agent — 前端开发专家（M5 完整 prompt）
    # ================================================================
    "frontend": FRONTEND_ROLE_PROMPT,

    # ================================================================
    # Doc Agent — 文档生成专家（M5 完整 prompt）
    # ================================================================
    "doc": DOC_ROLE_PROMPT,

    # ================================================================
    # Diagram Agent — 图表生成专家（M5 完整 prompt）
    # ================================================================
    "diagram": DIAGRAM_ROLE_PROMPT,

    # ================================================================
    # QA Agent — 质量检查官（M5 完整 prompt）
    # ================================================================
    "qa": QA_ROLE_PROMPT,

    # ================================================================
    # Export Agent — 交付清单生成器（M5 完整 prompt）
    # ================================================================
    "export": EXPORT_ROLE_PROMPT,
}


def get_role_prompt(agent_name: str) -> str:
    """
    根据 Agent 名称获取角色 prompt。

    - agent_name: Agent 名称（小写），如 "intent"、"contraction"
    - 返回: 对应的角色 prompt 字符串
    - 抛出: KeyError，当 agent_name 不存在时
    """
    if agent_name not in ROLE_PROMPTS:
        available = ", ".join(sorted(ROLE_PROMPTS.keys()))
        raise KeyError(
            f"未知的 Agent 名称: '{agent_name}'。"
            f"可用的 Agent: {available}"
        )
    return ROLE_PROMPTS[agent_name]
