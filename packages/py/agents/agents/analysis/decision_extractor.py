"""
决策抽取器模块。

从对话消息中识别用户做出的关键决策，生成 DecisionRecord，
并可将决策写入 IR 的 decision node。

决策类型：技术选型、功能取舍、范围变更、优先级调整。

Phase 1 降级策略：用关键词匹配识别决策（不调 LLM）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DecisionRecord(BaseModel):
    """决策记录。

    字段:
        decision_type: 决策类型（tech_choice/feature_scope/priority/architecture）
        title: 决策标题
        description: 决策描述
        rationale: 决策理由
        affected_nodes: 受影响的 IR 节点 ID 列表
        timestamp: 决策时间
    """

    decision_type: str
    title: str
    description: str
    rationale: str
    affected_nodes: list[str] = []
    timestamp: datetime


class DecisionExtractor:
    """决策抽取器。

    从对话中识别用户做出的关键决策，写回 IR 的 decision node。
    决策类型：技术选型、功能取舍、范围变更、优先级调整。

    Phase 1 降级策略：用关键词匹配识别决策（不调 LLM）。
    """

    # 决策关键词映射
    # 注意：匹配顺序为 feature_scope -> priority -> architecture -> tech_choice
    # 避免宽泛关键词（如 "用"）抢先匹配
    DECISION_KEYWORDS: dict[str, list[str]] = {
        "feature_scope": ["去掉", "删除", "保留", "添加", "新增", "移除", "取消"],
        "priority": ["优先", "先做", "后做", "推迟", "提前", "紧急"],
        "architecture": ["拆分", "合并", "重构", "架构"],
        "tech_choice": ["不用", "选择", "采用", "替换", "迁移到", "改用"],
    }

    # 标题最大字符数
    TITLE_MAX_LENGTH = 50

    async def extract_decisions(self, messages: list) -> list[DecisionRecord]:
        """从消息列表中抽取决策。

        Phase 1 规则：扫描 user 消息，如果包含决策关键词，提取为 DecisionRecord。

        参数:
            messages: 消息列表

        返回:
            抽取到的决策记录列表
        """
        decisions: list[DecisionRecord] = []

        for msg in messages:
            role = self._get_role(msg)
            if role != "user":
                continue

            content = self._get_content(msg)
            if not content:
                continue

            # 获取消息时间戳
            timestamp = getattr(msg, "created_at", None)
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            # 检查每种决策类型的关键词
            for decision_type, keywords in self.DECISION_KEYWORDS.items():
                matched = False
                for keyword in keywords:
                    if keyword in content:
                        matched = True
                        break

                if matched:
                    # 构造 DecisionRecord
                    title = content[:self.TITLE_MAX_LENGTH]
                    if len(content) > self.TITLE_MAX_LENGTH:
                        title = title.rstrip() + "..."

                    record = DecisionRecord(
                        decision_type=decision_type,
                        title=title,
                        description=content,
                        rationale=f"用户消息包含 {decision_type} 类型关键词",
                        affected_nodes=[],
                        timestamp=timestamp,
                    )
                    decisions.append(record)
                    # 一条消息只匹配第一个命中的决策类型，避免重复
                    break

        return decisions

    async def write_to_ir(
        self,
        db,
        project_id: UUID,
        snapshot_id: UUID,
        decisions: list[DecisionRecord],
    ) -> list[dict]:
        """将决策写入 IR 的 decision node。

        对每个决策，创建一个 node_type="decision" 的 IRNode，
        通过 create_node 操作记录。

        参数:
            db: 数据库会话
            project_id: 项目 ID
            snapshot_id: 目标快照 ID
            decisions: 决策记录列表

        返回:
            创建的 IROperation payload 列表
        """
        operations: list[dict] = []

        for decision in decisions:
            # 构造 create_node 操作 payload
            operation_payload = {
                "operation_type": "create_node",
                "node_type": "decision",
                "label": decision.title,
                "props": {
                    "title": decision.title,
                    "description": decision.description,
                    "status": "accepted",
                    "alternatives": [decision.rationale],
                },
            }
            operations.append(operation_payload)

        logger.info(
            "决策写入 IR: project=%s, snapshot=%s, 共 %d 条决策",
            project_id,
            snapshot_id,
            len(operations),
        )

        return operations

    @staticmethod
    def _get_role(message) -> str:
        """获取消息角色字符串。

        兼容 ORM 模型（枚举 .value）和 SimpleNamespace（字符串）。

        参数:
            message: 消息对象

        返回:
            角色字符串
        """
        role = getattr(message, "role", None)
        if role is None:
            return ""
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
