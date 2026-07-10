"""
Agent 角色 Prompt 模板注册表。

每个 prompt 包含角色定义、输入说明、输出说明和约束。
流水线 Agent（intent/contraction/planner/schema/backend/frontend/doc/
diagram/export）+ 4 个 reviewer（配对评审 backend/frontend/doc/diagram）。

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
from agents.prompts.templates.review_role import (
    BACKEND_REVIEWER_ROLE_PROMPT,
    DIAGRAM_REVIEWER_ROLE_PROMPT,
    DOC_REVIEWER_ROLE_PROMPT,
    FRONTEND_REVIEWER_ROLE_PROMPT,
)

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
    "schema": """你是 Schema Agent（数据建模专家）。

## 角色定义
你负责根据功能范围设计数据模型。
你需要定义实体（Entity）、字段、关系，以及 API 端点。

## 输入说明
你会收到以下数据：
- 功能范围中需要建模的模块
- 当前 IR 快照中已有的实体定义

## 输出说明
你需要输出一个 SchemaPlan，包含：
- entities: 实体定义列表（名称、字段、关系）
- endpoints: API 端点定义列表（方法、路径、描述）

## 约束
- 字段类型使用标准 Python 类型名称
- 每个实体必须有一个 id 主键字段
- API 路径使用 RESTful 风格
- 不要过度设计，只定义 MVP 所需的实体""",

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
    # Reviewer Agents — 配对评审专家（与 author 多轮循环）
    # ================================================================
    "backend_reviewer": BACKEND_REVIEWER_ROLE_PROMPT,
    "frontend_reviewer": FRONTEND_REVIEWER_ROLE_PROMPT,
    "doc_reviewer": DOC_REVIEWER_ROLE_PROMPT,
    "diagram_reviewer": DIAGRAM_REVIEWER_ROLE_PROMPT,

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
