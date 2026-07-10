"""评审轮次模型 - 定义 author↔reviewer 多轮循环的轮次记录表。

conversation_turns 记录委托运行中每一轮"author 产出 / reviewer 评审"，
供 API 查询轮次历史和前端展示评审过程。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from platform_data.models.base import Base, UUIDPrimaryKeyMixin


class ReviewTurn(UUIDPrimaryKeyMixin, Base):
    """评审轮次表，记录一次 run 中各 author↔reviewer 对的每轮产出与结论。"""

    __tablename__ = "conversation_turns"

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_runs.id"), nullable=False, index=True,
    )
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False, default="", server_default="",
    )
    content_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
