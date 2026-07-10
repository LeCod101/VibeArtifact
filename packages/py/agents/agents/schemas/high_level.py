"""
Agent 高层结构体模块。

定义 LLM 输出的高层业务结构，每种结构体对应一个 Agent 的输出格式，
描述其业务语义。代码/文档/图表类结构体由 file_extractor 直接提取为
工作区文件写入 workspace_files。

包含以下高层结构体：
- ScopeItem / ScopeDraft：功能范围草案（intent/contraction agent）
- TaskStep / TaskPlan：任务执行计划（planner agent）
- FieldSpec / EntitySpec / EndpointSpec / SchemaPlan：数据模型与 API 契约（schema agent）
- FileSpec / BackendPlan / FrontendPlan / DocPlan：代码文件计划（backend/frontend/doc agent）
- DiagramSpec / DiagramPlan：图表计划（diagram agent）
- IssueSpec / QAReport：质量检查报告（qa agent）
- FileEntry / ExportManifest：导出清单（export agent）
- FixItem / FixPlan：旧版修复计划（已废弃，保留兼容）
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

# ============================================================
# 优先级枚举
# ============================================================

class Priority(StrEnum):
    """功能范围的优先级等级。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# 功能范围相关（intent / contraction agent）
# ============================================================

class ScopeItem(BaseModel):
    """
    收缩后的单个功能范围。

    表示 MVP 中一个被保留的功能点。
    - name: 功能名称
    - description: 功能描述
    - priority: 优先级
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
    estimated_complexity: Literal["small", "medium", "large"]


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

    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
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
    diagram_type: Literal["flowchart", "sequence", "er", "classDiagram"]
    mermaid_code: str


class DiagramPlan(BaseModel):
    """
    diagram agent 的高层输出 — 图表计划。

    包含需要生成的所有图表。
    - diagrams: 图表定义列表
    """

    diagrams: list[DiagramSpec]


# ============================================================
# QA 检查相关（qa agent）
# ============================================================

class IssueSpec(BaseModel):
    """
    QA 检查发现的单个问题。

    描述一个结构性问题的严重度、分类、描述和影响文件。
    - severity: 严重度等级（critical / warning / info）
    - category: 问题分类（missing_file / schema_mismatch / import_error / config_error）
    - description: 问题描述
    - affected_file: 受影响的文件路径
    """

    severity: Literal["critical", "warning", "info"]
    category: Literal[
        "missing_file", "schema_mismatch", "import_error", "config_error"
    ]
    description: str
    affected_file: str


class QAReport(BaseModel):
    """
    qa agent 的高层输出 — 质量检查报告。

    描述结构性检查的结果，包含通过/失败状态、问题列表和摘要。
    - passed: 是否通过质量检查
    - issues: 发现的问题列表
    - summary: 检查结果摘要
    """

    passed: bool
    issues: list[IssueSpec] = []
    summary: str


# 保留旧类型别名以兼容现有引用
class FixItem(BaseModel):
    """
    QA 修复项（已废弃，保留兼容）。

    M5 之前使用的旧格式，已被 IssueSpec 替代。
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
    qa agent 的旧高层输出（已废弃，保留兼容）。

    M5 之前使用的旧格式，已被 QAReport 替代。
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

class FileEntry(BaseModel):
    """
    导出文件条目。

    描述一个待打包导出的文件，包含来源类型、源路径和导出路径。
    - source_type: 文件来源类型（code / doc / diagram）
    - source_path: 源文件在 IR 中的路径
    - export_path: 导出到最终项目中的目标路径
    """

    source_type: Literal["code", "doc", "diagram"]
    source_path: str
    export_path: str


class ExportManifest(BaseModel):
    """
    export agent 的高层输出 — 导出清单。

    描述最终交付项目的完整结构，包含项目名称、文件列表、
    Docker Compose 配置和环境变量模板。
    - project_name: 项目名称
    - files: 导出文件条目列表
    - docker_compose_config: Docker Compose 服务配置字典
    - env_template: .env.example 模板键值对字典
    """

    project_name: str
    files: list[FileEntry]
    docker_compose_config: dict
    env_template: dict
