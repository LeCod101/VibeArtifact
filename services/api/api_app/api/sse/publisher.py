"""
SSE 事件发布器模块。

Worker 端通过 Redis pub/sub 发布进度事件到频道 sse:{run_id}，
API 端通过订阅同一频道将事件转为 SSE 流推送给前端客户端。

本模块可独立使用 Redis 连接，不依赖 FastAPI app。
Worker 端和 API 端均可导入使用。
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import redis.asyncio as aioredis

# ──────────────────────────────────────────────
# Redis 连接管理
# ──────────────────────────────────────────────

_redis_client: aioredis.Redis | None = None


def _get_redis_url() -> str:
    """
    获取 Redis 连接 URL。

    优先从环境变量 REDIS_URL 读取，否则使用默认本地地址。
    """
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def get_redis() -> aioredis.Redis:
    """
    获取异步 Redis 客户端（单例）。

    懒加载，首次调用时创建连接。
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            _get_redis_url(),
            decode_responses=True,
        )
    return _redis_client


def _channel_name(run_id: str) -> str:
    """
    生成 SSE 频道名称。

    频道命名规则：sse:{run_id}

    - run_id: 运行 ID
    - 返回: Redis 频道名称
    """
    return f"sse:{run_id}"


# ──────────────────────────────────────────────
# 事件发布（Worker 端调用）
# ──────────────────────────────────────────────

async def publish_step_event(
    run_id: str,
    event_type: str,
    data: dict,
) -> None:
    """
    发布进度事件到 Redis pub/sub。

    将事件序列化为 JSON 并发布到频道 sse:{run_id}。
    Worker 端的 orchestrate.py 和 agent_task.py 调用此函数
    通知前端某个步骤的状态变更。

    - run_id: 运行 ID
    - event_type: 事件类型（step_start / step_complete / step_failed /
                  run_complete / run_failed）
    - data: 事件载荷数据
    """
    r = await get_redis()
    message = json.dumps(
        {
            "event": event_type,
            "data": data,
        },
        ensure_ascii=False,
    )
    await r.publish(_channel_name(run_id), message)


# ──────────────────────────────────────────────
# 便捷发布函数
# ──────────────────────────────────────────────

async def publish_step_start(run_id: str, agent_id: str) -> None:
    """
    发布步骤开始事件。

    - run_id: 运行 ID
    - agent_id: 开始执行的 agent 标识
    """
    await publish_step_event(
        run_id=run_id,
        event_type="step_start",
        data={
            "step": agent_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def publish_step_complete(
    run_id: str,
    agent_id: str,
    duration_ms: int,
) -> None:
    """
    发布步骤完成事件。

    - run_id: 运行 ID
    - agent_id: 完成执行的 agent 标识
    - duration_ms: 执行耗时（毫秒）
    """
    await publish_step_event(
        run_id=run_id,
        event_type="step_complete",
        data={
            "step": agent_id,
            "agent_id": agent_id,
            "duration_ms": duration_ms,
        },
    )


async def publish_step_failed(
    run_id: str,
    agent_id: str,
    error: str,
) -> None:
    """
    发布步骤失败事件。

    - run_id: 运行 ID
    - agent_id: 失败的 agent 标识
    - error: 错误信息
    """
    await publish_step_event(
        run_id=run_id,
        event_type="step_failed",
        data={
            "step": agent_id,
            "agent_id": agent_id,
            "error": error,
        },
    )


async def publish_run_complete(run_id: str, zip_url: str) -> None:
    """
    发布运行完成事件。

    - run_id: 运行 ID
    - zip_url: 产物 ZIP 下载地址
    """
    await publish_step_event(
        run_id=run_id,
        event_type="run_complete",
        data={
            "run_id": run_id,
            "zip_url": zip_url,
        },
    )


async def publish_run_failed(
    run_id: str,
    error: str,
    failed_step: str = "",
) -> None:
    """
    发布运行失败事件。

    - run_id: 运行 ID
    - error: 失败原因
    - failed_step: 导致失败的 agent 标识（可选）
    """
    await publish_step_event(
        run_id=run_id,
        event_type="run_failed",
        data={
            "run_id": run_id,
            "error": error,
            "failed_step": failed_step,
        },
    )


async def publish_approval_required(
    run_id: str,
    approval_items: dict,
) -> None:
    """
    发布审批请求事件。

    委托运行进入 waiting_approval 状态时发布此事件，
    前端收到后展示审批面板，包含风险项和待决策项。

    - run_id: 运行 ID
    - approval_items: 审批项汇总字典，包含 high_risks / pending_decisions 等
    """
    await publish_step_event(
        run_id=run_id,
        event_type="approval_required",
        data={
            "run_id": run_id,
            "approval_items": approval_items,
            "message": "运行需要审批，请查看风险项和待决策项",
        },
    )


async def publish_approval_complete(
    run_id: str,
    action: str,
) -> None:
    """
    发布审批完成事件。

    用户完成审批操作（approve / reject / adjust）后发布此事件，
    前端收到后更新运行状态和面板显示。

    - run_id: 运行 ID
    - action: 审批动作（approve / reject / adjust）
    """
    await publish_step_event(
        run_id=run_id,
        event_type="approval_complete",
        data={
            "run_id": run_id,
            "action": action,
            "message": f"审批操作完成: {action}",
        },
    )


async def publish_needs_attention(
    run_id: str,
    gate_result: dict,
) -> None:
    """
    发布 needs_attention 事件。

    Gate 检查失败且自动修复无效时发布此事件，
    前端收到后展示人工介入提示和失败详情。

    - run_id: 运行 ID
    - gate_result: Gate 汇总结果字典，包含失败门禁和问题列表
    """
    await publish_step_event(
        run_id=run_id,
        event_type="needs_attention",
        data={
            "run_id": run_id,
            "gate_result": gate_result,
            "message": "Gate 检查失败，需要人工介入",
        },
    )
