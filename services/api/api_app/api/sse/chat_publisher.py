"""
对话模式 SSE 事件发布器。

频道格式: sse:chat:{conversation_id}

与 publisher.py 的区别：
- publisher.py 面向全权委托模式（run_id 为频道标识）
- chat_publisher.py 面向一问一答模式（conversation_id 为频道标识）
- redis 参数可选，为 None 时静默跳过（不抛异常）
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _chat_channel(conversation_id: str) -> str:
    """
    生成对话模式 SSE 频道名称。

    频道命名规则：sse:chat:{conversation_id}

    参数:
        conversation_id: 会话 ID

    返回:
        Redis 频道名称
    """
    return f"sse:chat:{conversation_id}"


async def publish_chat_event(
    conversation_id: str,
    event: str,
    data: dict,
    redis=None,
) -> None:
    """
    发布对话模式 SSE 事件。

    将事件序列化为 JSON 并通过 Redis pub/sub 发布到频道
    sse:chat:{conversation_id}。如果 redis 为 None 则静默跳过。

    参数:
        conversation_id: 会话 ID
        event: 事件类型
        data: 事件载荷数据
        redis: Redis 连接（可选，为空则跳过）
    """
    if redis is None:
        return

    channel = _chat_channel(conversation_id)
    payload = {
        "event": event,
        "data": {
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    message = json.dumps(payload, ensure_ascii=False)
    await redis.publish(channel, message)


# ──────────────────────────────────────────────
# 便捷发布函数
# ──────────────────────────────────────────────


async def publish_chat_analysis_start(
    conversation_id: str,
    redis=None,
) -> None:
    """
    发布影响分析开始事件。

    参数:
        conversation_id: 会话 ID
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="analysis_start",
        data={"message": "正在分析您的需求..."},
        redis=redis,
    )


async def publish_chat_analysis_done(
    conversation_id: str,
    impact_report: dict,
    redis=None,
) -> None:
    """
    发布影响分析完成事件。

    参数:
        conversation_id: 会话 ID
        impact_report: 影响分析报告字典
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="analysis_done",
        data={
            "impact_report": impact_report,
            "message": "影响分析完成",
        },
        redis=redis,
    )


async def publish_chat_agent_start(
    conversation_id: str,
    agent_id: str,
    redis=None,
) -> None:
    """
    发布某个 Agent 开始执行事件。

    参数:
        conversation_id: 会话 ID
        agent_id: 正在执行的 Agent 标识
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="agent_start",
        data={
            "agent_id": agent_id,
            "message": f"正在执行 {agent_id} ...",
        },
        redis=redis,
    )


async def publish_chat_agent_done(
    conversation_id: str,
    agent_id: str,
    duration_ms: int,
    redis=None,
) -> None:
    """
    发布某个 Agent 执行完成事件。

    参数:
        conversation_id: 会话 ID
        agent_id: 已完成的 Agent 标识
        duration_ms: 执行耗时（毫秒）
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="agent_done",
        data={
            "agent_id": agent_id,
            "duration_ms": duration_ms,
        },
        redis=redis,
    )


async def publish_chat_apply_done(
    conversation_id: str,
    new_snapshot_id: str,
    operations_count: int,
    redis=None,
) -> None:
    """
    发布快照写入完成事件。

    参数:
        conversation_id: 会话 ID
        new_snapshot_id: 新快照 ID
        operations_count: 操作总数
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="apply_done",
        data={
            "new_snapshot_id": new_snapshot_id,
            "operations_count": operations_count,
            "message": "变更已应用",
        },
        redis=redis,
    )


async def publish_chat_complete(
    conversation_id: str,
    change_summary: dict,
    redis=None,
) -> None:
    """
    发布编排全部完成事件。

    参数:
        conversation_id: 会话 ID
        change_summary: 变更摘要字典
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="complete",
        data={
            "change_summary": change_summary,
            "message": "处理完成",
        },
        redis=redis,
    )


async def publish_chat_failed(
    conversation_id: str,
    error: str,
    redis=None,
) -> None:
    """
    发布执行失败事件。

    参数:
        conversation_id: 会话 ID
        error: 错误信息
        redis: Redis 连接（可选）
    """
    await publish_chat_event(
        conversation_id=conversation_id,
        event="failed",
        data={
            "error": error,
            "message": "处理失败",
        },
        redis=redis,
    )
