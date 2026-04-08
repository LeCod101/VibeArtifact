"""辅助工具。

提供联网搜索和向用户追问澄清的能力。
"""

from __future__ import annotations

from agents.tools.base import tool


@tool
async def web_search(query: str) -> dict:
    """搜索互联网获取最新信息。

    Args:
        query: 搜索关键词
    """
    return {
        "action": "web_search",
        "query": query,
    }


@tool
async def ask_clarification(question: str, options: list[str] | None = None) -> dict:
    """向用户提出澄清问题，等待用户回复后继续。

    Args:
        question: 需要用户回答的问题
        options: 可选的预设选项列表
    """
    return {
        "action": "ask_clarification",
        "question": question,
        "options": options or [],
    }
