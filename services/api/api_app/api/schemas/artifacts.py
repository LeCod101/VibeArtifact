"""产物相关的请求和响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    """产物信息响应。"""

    id: UUID
    project_id: UUID
    artifact_type: str
    title: str
    content: str
    file_path: str | None = None
    language: str | None = None
    version_num: int
    parent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactListItem(BaseModel):
    """产物列表项（不含完整 content，减少传输量）。"""

    id: UUID
    project_id: UUID
    artifact_type: str
    title: str
    file_path: str | None = None
    language: str | None = None
    version_num: int
    parent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactUpdateRequest(BaseModel):
    """产物编辑请求。"""

    title: str | None = None
    content: str | None = None
    file_path: str | None = None
    language: str | None = None


class ArtifactVersionResponse(BaseModel):
    """产物版本历史项。"""

    id: UUID
    version_num: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExportRequest(BaseModel):
    """导出请求。"""

    export_type: str = "zip"


class ExportResponse(BaseModel):
    """导出响应。"""

    id: UUID
    project_id: UUID
    export_type: str
    file_url: str | None = None
    file_size_bytes: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
