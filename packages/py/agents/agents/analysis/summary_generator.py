"""
对话摘要生成器模块。

当分支消息数超过阈值时，将旧消息压缩为一段 summary 文本，
保留关键上下文，减少后续 LLM 调用时的 token 消耗。

Phase 1 降级策略：不调用 LLM，直接用规则拼接摘要。
"""

from __future__ import annotations

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """对话摘要生成器。

    当分支消息数超过阈值（默认 10 轮）时，
    将旧消息压缩为一段 summary 文本，保留关键上下文。
    """

    # 触发压缩的消息轮数
    COMPRESSION_THRESHOLD = 10
    # 保留最近 N 轮不压缩
    KEEP_RECENT = 3
    # 摘要最大字符数
    MAX_SUMMARY_LENGTH = 2000

    async def should_compress(self, messages: list) -> bool:
        """判断是否需要压缩。

        一轮 = 一条 user 消息，计算 user 消息数来确定轮数。

        参数:
            messages: 消息列表（需要有 role 属性）

        返回:
            是否需要压缩
        """
        rounds = sum(
            1 for m in messages
            if self._get_role(m) == "user"
        )
        return rounds > self.COMPRESSION_THRESHOLD

    async def generate_summary(
        self,
        messages: list,
        existing_summary: str | None = None,
    ) -> str:
        """生成摘要文本。

        Phase 1 降级策略：不调用 LLM，直接拼接规则摘要。
        提取每轮 assistant 消息的第一行（通常是变更摘要），加上旧 summary。

        参数:
            messages: 要压缩的消息列表（不含最近 KEEP_RECENT 轮）
            existing_summary: 已有的摘要文本（增量压缩时传入）

        返回:
            压缩后的摘要文本
        """
        parts: list[str] = []

        # 如果有旧 summary，以它开头
        if existing_summary:
            parts.append(existing_summary.strip())

        # 提取每轮 assistant 消息的第一行
        for m in messages:
            if self._get_role(m) != "assistant":
                continue
            content = self._get_content(m)
            if not content:
                continue
            # 取第一行（第一个 \n 前的内容）
            first_line = content.split("\n", 1)[0].strip()
            if first_line:
                parts.append(f"* {first_line}")

        summary = "\n".join(parts)

        # 限制总长度不超过 MAX_SUMMARY_LENGTH
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[: self.MAX_SUMMARY_LENGTH - 3] + "..."

        return summary

    async def compress_branch(
        self,
        db,
        branch_id: UUID,
        conversation_id: UUID,
    ) -> str | None:
        """对指定分支执行压缩。

        1. 加载分支所有消息
        2. 判断是否需要压缩
        3. 如需要，生成 summary 并存入 conversation.summary
        4. 返回生成的 summary 或 None

        参数:
            db: 数据库会话（AsyncSession）
            branch_id: 分支 ID
            conversation_id: 会话 ID

        返回:
            生成的摘要文本，如果不需要压缩则返回 None
        """
        from platform_data.models.conversation import Conversation
        from platform_data.repositories.message_repo import MessageRepository

        msg_repo = MessageRepository(db)

        # 加载全部消息（按时间降序）
        all_messages = await msg_repo.list_by_branch(
            branch_id=branch_id,
            limit=200,
        )

        # 反转为时间正序，便于处理
        all_messages = list(reversed(all_messages))

        # 判断是否需要压缩
        if not await self.should_compress(all_messages):
            return None

        # 获取现有 conversation summary
        from sqlalchemy import select

        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        existing_summary = conversation.summary if conversation else None

        # 计算需要保留的最近 KEEP_RECENT 轮消息的索引
        # 从后往前找到第 KEEP_RECENT 个 user 消息的位置
        user_count = 0
        split_idx = len(all_messages)
        for i in range(len(all_messages) - 1, -1, -1):
            if self._get_role(all_messages[i]) == "user":
                user_count += 1
                if user_count >= self.KEEP_RECENT:
                    split_idx = i
                    break

        # 需要压缩的消息（旧的部分）
        messages_to_compress = all_messages[:split_idx]

        if not messages_to_compress:
            return None

        # 生成摘要
        summary = await self.generate_summary(
            messages_to_compress,
            existing_summary=existing_summary,
        )

        # 写入 conversation.summary
        if conversation:
            conversation.summary = summary
            await db.flush()

        logger.info(
            "分支 %s 压缩完成: 压缩 %d 条消息, 摘要长度 %d",
            branch_id,
            len(messages_to_compress),
            len(summary),
        )

        return summary

    @staticmethod
    def _get_role(message) -> str:
        """获取消息角色字符串。

        兼容 ORM 模型（枚举 .value）和 SimpleNamespace（字符串）。

        参数:
            message: 消息对象

        返回:
            角色字符串（"user" / "assistant" / "system"）
        """
        role = getattr(message, "role", None)
        if role is None:
            return ""
        # ORM 模型的 role 是枚举类型，需要取 .value
        if hasattr(role, "value"):
            return role.value
        return str(role)

    @staticmethod
    def _get_content(message) -> str:
        """获取消息内容文本。

        参数:
            message: 消息对象

        返回:
            消息内容字符串
        """
        return getattr(message, "content", "") or ""
