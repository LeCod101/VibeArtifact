"""产物相关的响应模型 - 定义产物列表的数据结构。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    """产物信息响应。

    字段：
        id: 产物唯一标识
        kind: 产物类型（如 code、document、diagram 等）
        name: 产物名称
        snapshot_id: 关联的快照 ID
        created_at: 创建时间
    """

    id: UUID
    kind: str
    name: str
    snapshot_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
