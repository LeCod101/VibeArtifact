"""
Agent 定义与批量注册模块。

定义全部 Agent 的配置，并提供 register_all_agents() 函数
将所有 Agent 注册到全局 AgentRegistry 中。

Agent DAG 依赖关系（reviewer 不进 DAG，在 author 的执行步内多轮循环）：
  intent → contraction → planner → schema → backend  ┐
                                          → frontend ├→ export
                                          → doc      │
                                          → diagram  ┘

author↔reviewer 配对（REVIEW_PAIRS）：
  backend  ↔ backend_reviewer
  frontend ↔ frontend_reviewer
  doc      ↔ doc_reviewer
  diagram  ↔ diagram_reviewer
"""

from agents.configs.base import AgentConfig, ModelTier, RoleCategory
from agents.configs.registry import AgentRegistry

# author agent → 配对 reviewer agent 映射
# 命中此表的 agent 在委托运行中走 conversation_graph 多轮循环，
# 未命中的走单轮 AgentRunner
REVIEW_PAIRS: dict[str, str] = {
    "backend": "backend_reviewer",
    "frontend": "frontend_reviewer",
    "doc": "doc_reviewer",
    "diagram": "diagram_reviewer",
}


def register_all_agents() -> AgentRegistry:
    """
    注册全部 Agent（9 个流水线 Agent + 4 个 reviewer）并返回 Registry。

    按照 DAG 依赖关系定义所有 Agent 的配置，
    然后逐个注册到全局 AgentRegistry 单例中。
    返回注册完成的 AgentRegistry 实例。
    """
    registry = AgentRegistry.get_instance()

    # 导入所有 Agent 专用 Schema
    from agents.schemas.backend import BackendInput, BackendOutput
    from agents.schemas.contraction import ContractionInput, ContractionOutput
    from agents.schemas.diagram import DiagramInput, DiagramOutput
    from agents.schemas.doc import DocInput, DocOutput
    from agents.schemas.export import ExportInput, ExportOutput
    from agents.schemas.frontend import FrontendInput, FrontendOutput
    from agents.schemas.intent import IntentInput, IntentOutput
    from agents.schemas.planner import PlannerInput, PlannerOutput
    from agents.schemas.review import ReviewInput, ReviewOutput
    from agents.schemas.schema_agent import SchemaInput, SchemaOutput

    # 流水线 Agent 配置定义
    agents = [
        # === 意图与规划阶段 ===
        AgentConfig(
            agent_id="intent",
            name="Intent Agent",
            description="理解用户产品想法，提取功能范围",
            role_category=RoleCategory.INTENT_PLANNING,
            model_tier=ModelTier.REASONING,
            input_schema=IntentInput,
            output_schema=IntentOutput,
            high_level_key="scope_draft",
            dependencies=[],
        ),
        AgentConfig(
            agent_id="contraction",
            name="Contraction Agent",
            description="将功能范围收缩为最小可行产品",
            role_category=RoleCategory.INTENT_PLANNING,
            model_tier=ModelTier.REASONING,
            input_schema=ContractionInput,
            output_schema=ContractionOutput,
            high_level_key="scope_draft",
            dependencies=["intent"],
        ),
        AgentConfig(
            agent_id="planner",
            name="Planner Agent",
            description="根据收缩后的范围生成任务执行计划",
            role_category=RoleCategory.INTENT_PLANNING,
            model_tier=ModelTier.REASONING,
            input_schema=PlannerInput,
            output_schema=PlannerOutput,
            high_level_key="task_plan",
            dependencies=["contraction"],
        ),
        # === 数据建模阶段 ===
        AgentConfig(
            agent_id="schema",
            name="Schema Agent",
            description="设计数据模型与 API 契约",
            role_category=RoleCategory.SCHEMA,
            model_tier=ModelTier.REASONING,
            input_schema=SchemaInput,
            output_schema=SchemaOutput,
            high_level_key="schema_plan",
            dependencies=["planner"],
        ),
        # === 构建阶段（author，各自配对 reviewer 多轮循环） ===
        AgentConfig(
            agent_id="backend",
            name="Backend Agent",
            description="根据数据模型与 API 契约生成后端代码",
            role_category=RoleCategory.BUILD,
            model_tier=ModelTier.GENERATION,
            input_schema=BackendInput,
            output_schema=BackendOutput,
            high_level_key="backend_plan",
            dependencies=["schema"],
        ),
        AgentConfig(
            agent_id="frontend",
            name="Frontend Agent",
            description="根据数据模型与 API 契约生成前端代码",
            role_category=RoleCategory.BUILD,
            model_tier=ModelTier.GENERATION,
            input_schema=FrontendInput,
            output_schema=FrontendOutput,
            high_level_key="frontend_plan",
            dependencies=["schema"],
        ),
        # === 文档阶段 ===
        AgentConfig(
            agent_id="doc",
            name="Doc Agent",
            description="根据数据模型与 API 契约生成项目文档",
            role_category=RoleCategory.DOCUMENTATION,
            model_tier=ModelTier.GENERATION,
            input_schema=DocInput,
            output_schema=DocOutput,
            high_level_key="doc_plan",
            dependencies=["schema"],
        ),
        AgentConfig(
            agent_id="diagram",
            name="Diagram Agent",
            description="根据数据模型与 API 契约生成 Mermaid 图表",
            role_category=RoleCategory.DOCUMENTATION,
            model_tier=ModelTier.GENERATION,
            input_schema=DiagramInput,
            output_schema=DiagramOutput,
            high_level_key="diagram_plan",
            dependencies=["schema"],
        ),
        # === 交付阶段 ===
        AgentConfig(
            agent_id="export",
            name="Export Agent",
            description="将生成的产物打包导出",
            role_category=RoleCategory.DELIVERY,
            model_tier=ModelTier.GENERATION,
            input_schema=ExportInput,
            output_schema=ExportOutput,
            high_level_key="export_manifest",
            dependencies=["backend", "frontend", "doc", "diagram"],
        ),
    ]

    # === Reviewer Agent（不进 DAG，由 conversation_graph 在配对 author 的
    #     执行步内调用；吸收原独立 qa agent 的质量检查职责） ===
    for author_id, reviewer_id in REVIEW_PAIRS.items():
        agents.append(
            AgentConfig(
                agent_id=reviewer_id,
                name=f"{author_id.capitalize()} Reviewer",
                description=f"评审 {author_id} agent 的产物并给出修改意见",
                role_category=RoleCategory.REVIEW,
                model_tier=ModelTier.REASONING,
                input_schema=ReviewInput,
                output_schema=ReviewOutput,
                high_level_key="review",
                dependencies=[],
            )
        )

    # 逐个注册到全局 Registry
    for agent in agents:
        registry.register(agent)

    return registry
