"""
IR 节点类型定义模块。

定义所有合法的节点类型枚举，以及每种节点类型对应的属性（props）Pydantic model。
提供 NODE_PROPS_MAP 映射表，方便 validator 根据 node_type 查找对应的 props model。
"""

from enum import StrEnum

from pydantic import BaseModel

# ============================================================
# 节点类型枚举
# ============================================================

class NodeType(StrEnum):
    """
    IR 图中所有合法的节点类型。

    使用 StrEnum 以便 JSON 序列化时直接输出字符串值。
    """

    # 范围/功能模块
    SCOPE = "scope"
    # 数据实体
    ENTITY = "entity"
    # API 端点
    ENDPOINT = "endpoint"
    # 页面
    PAGE = "page"
    # UI 组件
    COMPONENT = "component"
    # 架构决策记录
    DECISION = "decision"
    # 风险条目
    RISK = "risk"
    # 任务步骤（planner agent 生成的执行步骤）
    TASK = "task"
    # 文档文件（doc agent 生成的技术文档）
    DOC = "doc"
    # 图表（diagram agent 生成的 Mermaid 图表）
    DIAGRAM = "diagram"
    # 代码文件（backend/frontend agent 生成的源码文件）
    CODE = "code"
    # 交付清单（export agent 生成的最终导出清单）
    DELIVERY = "delivery"


# ============================================================
# 通用子结构
# ============================================================

class FieldDef(BaseModel):
    """
    实体字段定义。

    用于 EntityProps.fields 列表中的每一项，描述数据实体的单个字段。
    - name: 字段名称
    - type: 字段数据类型（如 "UUID", "str", "int"）
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


class PropDef(BaseModel):
    """
    组件属性定义。

    用于 ComponentProps.props 列表中的每一项，描述 UI 组件的单个属性。
    - name: 属性名称
    - type: 属性数据类型
    - required: 是否必填
    - default: 默认值
    """

    name: str
    type: str
    required: bool = True
    default: str | None = None


# ============================================================
# 优先级枚举
# ============================================================

class Priority(StrEnum):
    """范围（scope）节点的优先级等级。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# HTTP 方法枚举
# ============================================================

class HttpMethod(StrEnum):
    """API 端点支持的 HTTP 方法。"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# ============================================================
# 决策状态枚举
# ============================================================

class DecisionStatus(StrEnum):
    """架构决策的审批状态。"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ============================================================
# 风险严重度枚举
# ============================================================

class RiskSeverity(StrEnum):
    """风险条目的严重程度。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================
# 风险状态枚举
# ============================================================

class RiskStatus(StrEnum):
    """风险条目的处理状态。"""

    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"


# ============================================================
# 各节点类型的 Props Model
# ============================================================

class ScopeProps(BaseModel):
    """
    scope 节点的属性。

    表示功能范围/模块，包含名称、描述、优先级和标签。
    """

    name: str
    description: str
    priority: Priority
    tags: list[str]


class EntityProps(BaseModel):
    """
    entity 节点的属性。

    表示数据实体，包含名称、字段定义列表和关联关系。
    """

    name: str
    fields: list[FieldDef]
    relationships: list[str] = []


class EndpointProps(BaseModel):
    """
    endpoint 节点的属性。

    表示 API 端点，包含 HTTP 方法、路径、描述、请求/响应 schema 等。
    """

    method: HttpMethod
    path: str
    description: str
    request_schema: str | None = None
    response_schema: str | None = None
    auth_required: bool = True


class PageProps(BaseModel):
    """
    page 节点的属性。

    表示前端页面，包含路由路径、标题、描述和布局。
    """

    route: str
    title: str
    description: str | None = None
    layout: str | None = None


class ComponentProps(BaseModel):
    """
    component 节点的属性。

    表示 UI 组件，包含名称、描述、属性定义列表和事件列表。
    """

    name: str
    description: str | None = None
    props: list[PropDef] | None = None
    events: list[str] | None = None


class DecisionProps(BaseModel):
    """
    decision 节点的属性。

    表示架构决策记录，包含标题、描述、状态和备选方案。
    """

    title: str
    description: str
    status: DecisionStatus
    alternatives: list[str] | None = None


class RiskProps(BaseModel):
    """
    risk 节点的属性。

    表示风险条目，包含标题、描述、严重度、缓解措施和处理状态。
    """

    title: str
    description: str
    severity: RiskSeverity
    mitigation: str | None = None
    status: RiskStatus


class TaskProps(BaseModel):
    """
    task 节点的属性。

    表示 planner agent 生成的任务步骤，包含步骤 ID、执行 agent、描述和依赖关系。
    - step_id: 步骤唯一标识
    - agent_id: 执行该步骤的 agent 标识（如 "schema", "backend"）
    - description: 步骤描述
    - depends_on: 依赖的 step_id 列表
    """

    step_id: str
    agent_id: str
    description: str
    depends_on: list[str] = []


class DocProps(BaseModel):
    """
    doc 节点的属性。

    表示 doc agent 生成的文档文件，包含路径、内容和格式。
    - path: 文档文件路径（相对于项目根目录）
    - content: 文档内容（Markdown 格式）
    - format: 文档格式标识，固定为 "markdown"
    """

    path: str
    content: str
    format: str = "markdown"


class DiagramProps(BaseModel):
    """
    diagram 节点的属性。

    表示 diagram agent 生成的 Mermaid 图表，包含名称、类型、内容和描述。
    - name: 图表名称
    - diagram_type: 图表类型（er / architecture / sequence / flowchart / classDiagram）
    - content: Mermaid 语法代码
    - description: 图表用途描述
    """

    name: str
    diagram_type: str
    content: str
    description: str = ""


class CodeProps(BaseModel):
    """
    code 节点的属性。

    表示 backend/frontend agent 生成的源码文件，包含文件路径、内容和编程语言。
    - path: 文件路径（相对于项目根目录，如 "backend/main.py"）
    - content: 文件源码内容
    - language: 编程语言标识（如 "python", "typescript", "json", "toml"）
    """

    path: str
    content: str
    language: str


class FileEntryDef(BaseModel):
    """
    导出文件条目定义。

    用于 DeliveryProps.files 列表中的每一项，描述一个待导出文件。
    - source_type: 文件来源类型（code / doc / diagram）
    - source_path: 源文件路径
    - export_path: 导出目标路径
    """

    source_type: str
    source_path: str
    export_path: str


class DeliveryProps(BaseModel):
    """
    delivery 节点的属性。

    表示 export agent 生成的交付清单，包含项目名称、文件列表、
    Docker Compose 配置和环境变量模板。
    - project_name: 项目名称
    - files: 导出文件条目列表
    - docker_compose_config: Docker Compose 服务配置
    - env_template: .env.example 模板键值对
    """

    project_name: str
    files: list[FileEntryDef]
    docker_compose_config: dict
    env_template: dict


# ============================================================
# 节点类型 → Props Model 映射表
# ============================================================

# validator 可通过此映射表根据 node_type 查找对应的 props model，
# 用于动态校验节点属性的合法性。
NODE_PROPS_MAP: dict[NodeType, type[BaseModel]] = {
    NodeType.SCOPE: ScopeProps,
    NodeType.ENTITY: EntityProps,
    NodeType.ENDPOINT: EndpointProps,
    NodeType.PAGE: PageProps,
    NodeType.COMPONENT: ComponentProps,
    NodeType.DECISION: DecisionProps,
    NodeType.RISK: RiskProps,
    NodeType.TASK: TaskProps,
    NodeType.DOC: DocProps,
    NodeType.DIAGRAM: DiagramProps,
    NodeType.CODE: CodeProps,
    NodeType.DELIVERY: DeliveryProps,
}
