"""项目相关的请求和响应模型 - 定义创建项目、项目信息等数据结构。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    """创建项目请求。

    字段：
        name: 项目名称
        description: 项目描述，可选
    """

    name: str
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    """更新项目请求。

    字段：
        name: 项目名称，可选
        description: 项目描述，可选
    """

    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    """项目信息响应 - 返回项目基本信息。

    字段：
        id: 项目唯一标识
        user_id: 所属用户 UUID
        name: 项目名称
        description: 项目描述
        status: 项目状态（active / archived）
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
