"""ConversationContextBuilder 单元测试。

使用 mock 模拟数据库依赖，验证上下文构建逻辑。
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api_app.application.services.context_builder import ConversationContextBuilder


def _make_message(role: str, content: str) -> SimpleNamespace:
    """创建模拟消息对象。

    参数:
        role: 消息角色
        content: 消息内容

    返回:
        模拟的消息 SimpleNamespace 对象
    """
    return SimpleNamespace(role=role, content=content)


def _make_orm_message(role_value: str, content: str) -> SimpleNamespace:
    """创建模拟 ORM 消息对象（role 是枚举类型）。

    参数:
        role_value: 角色枚举值
        content: 消息内容

    返回:
        模拟的 ORM 消息对象
    """
    role_enum = SimpleNamespace(value=role_value)
    return SimpleNamespace(role=role_enum, content=content)


# ============================================================
# 辅助 fixtures
# ============================================================


@pytest.fixture()
def mock_db():
    """提供一个 mock 的 AsyncSession。"""
    return AsyncMock()


@pytest.fixture()
def builder(mock_db):
    """提供 ConversationContextBuilder 实例。"""
    return ConversationContextBuilder(mock_db)


@pytest.fixture()
def conv_id():
    """提供固定的 conversation_id。"""
    return uuid.uuid4()


@pytest.fixture()
def branch_id():
    """提供固定的 branch_id。"""
    return uuid.uuid4()


# ============================================================
# 测试用例
# ============================================================


@pytest.mark.asyncio
async def test_build_context_empty(builder, conv_id, branch_id, mock_db):
    """无消息、无摘要、无决策时返回空列表。"""
    # mock _get_summary 返回 None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=[]),
        patch.object(builder, "_get_recent_messages", return_value=[]),
    ):
        result = await builder.build_context(conv_id, branch_id)

    assert result == []


@pytest.mark.asyncio
async def test_build_context_with_recent_messages(
    builder, conv_id, branch_id, mock_db,
):
    """只有近期消息时，上下文仅包含 user/assistant 消息。"""
    recent = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮助你？"},
    ]

    # mock _get_summary 返回 None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=[]),
        patch.object(builder, "_get_recent_messages", return_value=recent),
    ):
        result = await builder.build_context(conv_id, branch_id)

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_build_context_with_summary(
    builder, conv_id, branch_id, mock_db,
):
    """有摘要时，上下文第一条应为 system 消息包含摘要。"""
    # mock _get_summary 返回摘要文本
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "这是一段对话摘要"
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=[]),
        patch.object(builder, "_get_recent_messages", return_value=[]),
    ):
        result = await builder.build_context(conv_id, branch_id)

    assert len(result) == 1
    assert result[0]["role"] == "system"
    assert "对话摘要" in result[0]["content"]
    assert "这是一段对话摘要" in result[0]["content"]


@pytest.mark.asyncio
async def test_build_context_with_decisions(
    builder, conv_id, branch_id, mock_db,
):
    """有决策时，上下文包含 system 消息列出决策。"""
    decisions = ["使用 PostgreSQL 作为数据库", "前端采用 Next.js"]

    # mock _get_summary 返回 None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=decisions),
        patch.object(builder, "_get_recent_messages", return_value=[]),
    ):
        result = await builder.build_context(conv_id, branch_id)

    assert len(result) == 1
    assert result[0]["role"] == "system"
    assert "关键决策" in result[0]["content"]
    assert "PostgreSQL" in result[0]["content"]
    assert "Next.js" in result[0]["content"]


@pytest.mark.asyncio
async def test_build_context_full(
    builder, conv_id, branch_id, mock_db,
):
    """summary + decisions + messages 完整上下文。"""
    decisions = ["选择 FastAPI"]
    recent = [
        {"role": "user", "content": "开始开发"},
        {"role": "assistant", "content": "好的，开始吧"},
    ]

    # mock _get_summary 返回摘要
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "项目初始化完成"
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=decisions),
        patch.object(builder, "_get_recent_messages", return_value=recent),
    ):
        result = await builder.build_context(conv_id, branch_id)

    # 应为：摘要 system + 决策 system + 2 条消息 = 4 条
    assert len(result) == 4
    assert result[0]["role"] == "system"
    assert "对话摘要" in result[0]["content"]
    assert result[1]["role"] == "system"
    assert "关键决策" in result[1]["content"]
    assert result[2]["role"] == "user"
    assert result[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_build_context_truncation(
    builder, conv_id, branch_id, mock_db,
):
    """超长上下文应截断，总字符数不超过 MAX_CONTEXT_CHARS。"""
    # 设置一个较小的限制便于测试
    builder.MAX_CONTEXT_CHARS = 100

    # 构造超长消息
    long_messages = [
        {"role": "user", "content": "A" * 60},
        {"role": "assistant", "content": "B" * 60},
        {"role": "user", "content": "C" * 30},
    ]

    # mock _get_summary 返回 None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with (
        patch.object(builder, "_get_decisions", return_value=[]),
        patch.object(builder, "_get_recent_messages", return_value=long_messages),
    ):
        result = await builder.build_context(conv_id, branch_id)

    total_chars = sum(len(m["content"]) for m in result)
    assert total_chars <= 100
    # 至少保留了一些消息（不是全部被截断）
    assert len(result) > 0


@pytest.mark.asyncio
async def test_recent_messages_time_order(builder):
    """_get_recent_messages 返回消息应按时间正序排列。"""
    # 模拟 MessageRepository.list_by_branch 返回降序消息
    # （最新的在前）
    messages_desc = [
        _make_orm_message("assistant", "回复3"),
        _make_orm_message("user", "问题3"),
        _make_orm_message("assistant", "回复2"),
        _make_orm_message("user", "问题2"),
        _make_orm_message("assistant", "回复1"),
        _make_orm_message("user", "问题1"),
    ]

    branch_id = uuid.uuid4()

    with patch(
        "api_app.application.services.context_builder.MessageRepository"
    ) as MockMsgRepo:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list_by_branch.return_value = messages_desc
        MockMsgRepo.return_value = mock_repo_instance

        result = await builder._get_recent_messages(branch_id)

    # 验证第一条是最早的消息
    assert result[0]["content"] == "问题1"
    # 验证最后一条是最新的消息
    assert result[-1]["content"] == "回复3"


@pytest.mark.asyncio
async def test_recent_messages_limit(builder):
    """_get_recent_messages 只保留最近 RECENT_ROUNDS 轮。"""
    builder.RECENT_ROUNDS = 2

    # 模拟 5 轮消息（降序排列）
    messages_desc = []
    for i in range(5, 0, -1):
        messages_desc.append(_make_orm_message("assistant", f"回复{i}"))
        messages_desc.append(_make_orm_message("user", f"问题{i}"))

    branch_id = uuid.uuid4()

    with patch(
        "api_app.application.services.context_builder.MessageRepository"
    ) as MockMsgRepo:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list_by_branch.return_value = messages_desc
        MockMsgRepo.return_value = mock_repo_instance

        result = await builder._get_recent_messages(branch_id)

    # RECENT_ROUNDS=2，应保留最近 2 轮 = 4 条消息
    # 注意：list_by_branch 有 limit，实际返回的消息数可能更多
    # 但 _get_recent_messages 内部会截取
    user_msgs = [m for m in result if m["role"] == "user"]
    assert len(user_msgs) <= 2
