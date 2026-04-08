"""工具运行时上下文。

提供 DB 会话和项目/用户信息，
供需要读写数据库的工具函数使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ToolContext:
    """工具执行时注入的运行时上下文。

    工具函数通过声明 ``_ctx: ToolContext`` 参数接收此对象，
    该参数对 LLM 不可见（被 @tool 装饰器排除在 JSON Schema 之外）。

    Attributes:
        db: 异步数据库会话，工具通过它读写 artifacts 等表
        project_id: 当前项目 UUID
        user_id: 当前用户 UUID
    """

    db: "AsyncSession"
    project_id: UUID
    user_id: UUID
