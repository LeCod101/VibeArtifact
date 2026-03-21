"""对话上下文构建器模块。

组装精简上下文：summary + decisions + 最近 N 轮消息。
替代全量消息拼接，降低 token 消耗。
"""

from __future__ import annotations

import logging
from uuid import UUID

from platform_data.models.conversation import Conversation, Message
from platform_data.repositories.message_repo import MessageRepository
from platform_data.repositories.snapshot_repo import SnapshotRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ConversationContextBuilder:
    """对话上下文构建器。

    组装精简上下文：summary + decisions + 最近 N 轮消息。
    替代全量消息拼接，降低 token 消耗。
    """

    # 保留最近消息轮数（user+assistant 各一条算一轮）
    RECENT_ROUNDS = 3
    # 最大上下文字符数
    MAX_CONTEXT_CHARS = 4000

    def __init__(self, db: AsyncSession) -> None:
        """初始化上下文构建器。

        参数:
            db: SQLAlchemy 异步数据库会话
        """
        self._db = db

    async def build_context(
        self,
        conversation_id: UUID,
        branch_id: UUID,
    ) -> list[dict[str, str]]:
        """构建对话上下文。

        上下文结构（按顺序）：
        1. [system] 对话摘要（如果有）
        2. [system] 关键决策列表（如果有）
        3. 最近 RECENT_ROUNDS 轮 user/assistant 消息

        参数:
            conversation_id: 会话 ID
            branch_id: 分支 ID

        返回:
            上下文消息列表，格式为 [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        context: list[dict[str, str]] = []

        # 获取摘要
        summary = await self._get_summary(conversation_id)
        if summary:
            context.append({
                "role": "system",
                "content": f"## 对话摘要\n{summary}",
            })

        # 获取决策
        decisions = await self._get_decisions(branch_id)
        if decisions:
            # 逐条拼接决策文本
            lines = "\n".join(f"• {d}" for d in decisions)
            context.append({
                "role": "system",
                "content": f"## 关键决策\n{lines}",
            })

        # 获取最近消息
        recent = await self._get_recent_messages(branch_id)
        context.extend(recent)

        # 执行截断：如果总字符数超过限制，从最前面的消息开始移除
        context = self._truncate(context)

        return context

    async def _get_summary(self, conversation_id: UUID) -> str | None:
        """获取会话摘要。

        从 conversation 记录读取 summary 字段。

        参数:
            conversation_id: 会话 ID

        返回:
            摘要文本或 None
        """
        stmt = select(Conversation.summary).where(
            Conversation.id == conversation_id,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        # row 就是 summary 字段的值（可能为 None 或空字符串）
        if row and row.strip():
            return row.strip()
        return None

    async def _get_decisions(self, branch_id: UUID) -> list[str]:
        """获取分支相关的决策记录。

        通过分支的 head_snapshot_id 加载快照图，
        过滤 node_type="decision" 的节点，提取 title + description。

        参数:
            branch_id: 分支 ID

        返回:
            决策文本列表
        """
        from platform_data.repositories.branch_repo import BranchRepository

        branch_repo = BranchRepository(self._db)
        branch = await branch_repo.get_by_id(branch_id)

        if branch is None or branch.head_snapshot_id is None:
            return []

        snapshot_repo = SnapshotRepository(self._db)
        nodes, _edges = await snapshot_repo.load_snapshot_graph(
            branch.head_snapshot_id,
        )

        decisions: list[str] = []
        for node in nodes:
            if node.node_type != "decision":
                continue
            props = node.props or {}
            title = props.get("title", "")
            description = props.get("description", "")
            # 优先使用 title，如果有 description 则追加
            if title and description and title != description:
                decisions.append(f"{title}: {description}")
            elif title:
                decisions.append(title)
            elif description:
                decisions.append(description)

        return decisions

    async def _get_recent_messages(
        self, branch_id: UUID,
    ) -> list[dict[str, str]]:
        """获取最近 N 轮消息。

        一轮 = 一对 user + assistant 消息。
        从 MessageRepository 按时间降序加载，然后反转为时间正序。

        参数:
            branch_id: 分支 ID

        返回:
            最近消息列表（时间正序）
        """
        msg_repo = MessageRepository(self._db)

        # 加载足够多的消息，然后按轮数截断
        # RECENT_ROUNDS * 2 条消息 + 少量冗余
        raw_messages = await msg_repo.list_by_branch(
            branch_id=branch_id,
            limit=self.RECENT_ROUNDS * 2 + 2,
        )

        # list_by_branch 返回降序，反转为时间正序
        raw_messages = list(reversed(raw_messages))

        # 按轮数截取：从后往前找到第 RECENT_ROUNDS 个 user 消息的位置
        user_count = 0
        split_idx = 0
        for i in range(len(raw_messages) - 1, -1, -1):
            role = self._get_role(raw_messages[i])
            if role == "user":
                user_count += 1
                if user_count >= self.RECENT_ROUNDS:
                    split_idx = i
                    break

        # 截取从 split_idx 开始的消息
        trimmed = raw_messages[split_idx:]

        # 转换为 dict 格式
        result: list[dict[str, str]] = []
        for msg in trimmed:
            role = self._get_role(msg)
            # 只保留 user 和 assistant 消息
            if role in ("user", "assistant"):
                result.append({
                    "role": role,
                    "content": msg.content or "",
                })

        return result

    def _truncate(
        self, context: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """截断上下文，确保总字符数不超过 MAX_CONTEXT_CHARS。

        策略：保留尾部（最新的消息），从头部移除最老的条目。

        参数:
            context: 上下文消息列表

        返回:
            截断后的上下文消息列表
        """
        total_chars = sum(len(m["content"]) for m in context)

        if total_chars <= self.MAX_CONTEXT_CHARS:
            return context

        # 从头部开始移除，直到总字符数不超过限制
        while context and total_chars > self.MAX_CONTEXT_CHARS:
            removed = context.pop(0)
            total_chars -= len(removed["content"])

        return context

    @staticmethod
    def _get_role(message: Message) -> str:
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
        if hasattr(role, "value"):
            return role.value
        return str(role)
