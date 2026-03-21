"""模板相关的请求和响应模型 - 定义模板列表、详情、从模板创建项目等数据结构。"""

from datetime import datetime

from pydantic import BaseModel


class TemplateResponse(BaseModel):
    """模板信息响应 - 列表接口使用，不包含 snapshot_data。

    字段：
        id: 模板唯一标识
        name: 模板名称
        description: 模板描述
        category: 模板类别
        icon: 图标（emoji 或图标名称）
        is_public: 是否公开
        created_at: 创建时间
    """

    id: str
    name: str
    description: str
    category: str
    icon: str | None
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateDetailResponse(TemplateResponse):
    """模板详情响应 - 包含完整的 snapshot_data。

    字段：
        snapshot_data: IR 快照数据 {"nodes": [...], "edges": [...]}
    """

    snapshot_data: dict


class CreateFromTemplateRequest(BaseModel):
    """从模板创建项目请求。

    字段：
        template_id: 模板 UUID
        project_name: 新项目名称
    """

    template_id: str
    project_name: str


class CreateFromTemplateResponse(BaseModel):
    """从模板创建项目响应。

    字段：
        project_id: 新创建的项目 UUID
        snapshot_id: 初始快照 UUID
        message: 操作结果消息
    """

    project_id: str
    snapshot_id: str
    message: str
