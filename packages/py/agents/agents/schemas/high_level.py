"""
Agent 高层结构体模块。

定义 LLM 输出的高层业务结构，这些结构不是 IROperation，
而是由 Translator 翻译为 IROperation。每种结构体对应一个
Agent 的输出格式，描述其业务语义。

包含以下高层结构体：
- ScopeItem / ScopeDraft：功能范围草案（intent/contraction agent）
- TaskStep / TaskPlan：任务执行计划（planner agent）
- FieldSpec / EntitySpec / EndpointSpec / SchemaPlan：数据模型与 API 契约（schema agent）
- FileSpec / BackendPlan / FrontendPlan / DocPlan：代码文件计划（backend/frontend/doc agent）
- DiagramSpec / DiagramPlan：图表计划（diagram agent）
- FixItem / FixPlan：修复计划（qa agent）
- ExportManifest：导出清单（export agent）
"""

from ir_core.schema.node_types import Priority
from pydantic import BaseModel

# ============================================================
# 功能范围相关（intent / contraction agent）
# ============================================================

class ScopeItem(BaseModel):
    """
    收缩后的单个功能范围。

    表示 MVP 中一个被保留的功能点。
    - name: 功能名称
    - description: 功能描述
    - priority: 优先级（来自 ir_core 的 Priority 枚举）
    - tags: 功能标签列表
    """

    name: str
    description: str
    priority: Priority
    tags: list[str] = []


class ScopeDraft(BaseModel):
    """
    intent/contraction agent 的高层输出 — 功能范围草案。

    描述产品的名称、总体描述、保留的功能范围、
    延后的功能项以及识别到的风险。
    - product_name: 产品名称
    - product_description: 产品总体描述
    - scopes: 保留的功能范围列表
    - deferred_items: 延后到未来版本的功能项
    - risks: 识别到的风险清单
    """

    product_name: str
    product_description: str
    scopes: list[ScopeItem]
    deferred_items: list[str] = []
    risks: list[str] = []


# ============================================================
# 任务计划相关（planner agent）
# ============================================================

class TaskStep(BaseModel):
    """
    任务计划中的单个步骤。

    描述一个执行步骤，包含步骤标识、执行 agent、描述和依赖关系。
    - step_id: 步骤唯一标识
    - agent_id: 由哪个 agent 执行（如 "schema", "backend"）
    - description: 步骤描述
    - depends_on: 依赖的 step_id 列表
    """

    step_id: str
    agent_id: str
    description: str
    depends_on: list[str] = []


class TaskPlan(BaseModel):
    """
    planner agent 的高层输出 — 任务执行计划。

    描述完成项目所需的步骤序列和预估的整体复杂度。
    - steps: 执行步骤列表
    - estimated_complexity: 预估复杂度，取值 "small" / "medium" / "large"
    """

    steps: list[TaskStep]
    estimated_complexity: str


# ============================================================
# 数据模型与 API 契约（schema agent）
# ============================================================

class FieldSpec(BaseModel):
    """
    数据实体字段定义。

    描述实体中的单个字段及其约束。
    - name: 字段名称
    - type: 字段数据类型（如 "str", "int", "UUID"）
    - primary: 是否为主键
    - nullable: 是否允许空值
    - unique: 是否唯一约束
    - default: 默认值表达式
    """

    name: str
    type: str
    primary: bool = False
    nullable: bool = True
    unique: bool = False
    default: str | None = None


class EntitySpec(BaseModel):
    """
    数据实体定义。

    描述一个数据实体，包含字段列表和关联关系。
    - name: 实体名称
    - fields: 字段定义列表
    - relationships: 关联关系描述列表
    """

    name: str
    fields: list[FieldSpec]
    relationships: list[str] = []


class EndpointSpec(BaseModel):
    """
    API 端点定义。

    描述一个 REST API 端点的完整规格。
    - method: HTTP 方法（GET/POST/PUT/DELETE/PATCH）
    - path: 端点路径
    - description: 端点描述
    - request_schema: 请求体 schema 名称
    - response_schema: 响应体 schema 名称
    - auth_required: 是否需要认证
    """

    method: str
    path: str
    description: str
    request_schema: str | None = None
    response_schema: str | None = None
    auth_required: bool = True


class SchemaPlan(BaseModel):
    """
    schema agent 的高层输出 — 数据模型与 API 契约。

    描述系统中的数据实体和 API 端点。
    - entities: 数据实体定义列表
    - endpoints: API 端点定义列表
    """

    entities: list[EntitySpec]
    endpoints: list[EndpointSpec]


# ============================================================
# 代码文件相关（backend / frontend / doc agent）
# ============================================================

class FileSpec(BaseModel):
    """
    代码文件定义。

    描述一个需要生成的代码文件。
    - path: 文件路径（相对于项目根目录）
    - content: 文件内容
    - language: 编程语言标识（如 "python", "typescript"）
    """

    path: str
    content: str
    language: str


class BackendPlan(BaseModel):
    """
    backend agent 的高层输出 — 后端代码计划。

    包含需要生成的所有后端代码文件。
    - files: 代码文件定义列表
    """

    files: list[FileSpec]


class FrontendPlan(BaseModel):
    """
    frontend agent 的高层输出 — 前端代码计划。

    包含需要生成的所有前端代码文件。
    - files: 代码文件定义列表
    """

    files: list[FileSpec]


class DocPlan(BaseModel):
    """
    doc agent 的高层输出 — 文档计划。

    包含需要生成的所有文档文件。
    - files: 文档文件定义列表
    """

    files: list[FileSpec]


# ============================================================
# 图表相关（diagram agent）
# ============================================================

class DiagramSpec(BaseModel):
    """
    Mermaid 图表定义。

    描述一个需要生成的 Mermaid 图表。
    - title: 图表标题
    - diagram_type: 图表类型，取值 "flowchart" / "sequence" / "er" / "classDiagram"
    - mermaid_code: Mermaid 语法代码
    """

    title: str
    diagram_type: str
    mermaid_code: str


class DiagramPlan(BaseModel):
    """
    diagram agent 的高层输出 — 图表计划。

    包含需要生成的所有图表。
    - diagrams: 图表定义列表
    """

    diagrams: list[DiagramSpec]


# ============================================================
# QA 修复相关（qa agent）
# ============================================================

class FixItem(BaseModel):
    """
    QA 修复项。

    描述一个需要修复的问题。
    - file_path: 问题所在的文件路径
    - issue: 问题描述
    - fix_description: 修复方案描述
    - fixed_content: 修复后的文件内容（可选）
    """

    file_path: str
    issue: str
    fix_description: str
    fixed_content: str | None = None


class FixPlan(BaseModel):
    """
    qa agent 的高层输出 — QA 修复计划。

    描述质量检查的结果和需要修复的问题。
    - passed: 是否通过质量检查
    - issues: 需要修复的问题列表
    - summary: 检查结果摘要
    """

    passed: bool
    issues: list[FixItem] = []
    summary: str


# ============================================================
# 导出相关（export agent）
# ============================================================

class ExportManifest(BaseModel):
    """
    export agent 的高层输出 — 导出清单。

    描述最终导出的产物。
    - project_name: 项目名称
    - files: 导出的文件路径列表
    - entry_point: 项目入口文件路径
    - readme_path: README 文件路径
    """

    project_name: str
    files: list[str]
    entry_point: str | None = None
    readme_path: str = "README.md"
