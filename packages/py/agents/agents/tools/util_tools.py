"""辅助工具。

提供联网搜索和向用户追问澄清的能力。
"""

from __future__ import annotations

import logging
import os

from agents.tools.base import tool

logger = logging.getLogger(__name__)


@tool
async def web_search(query: str) -> dict:
    """搜索互联网获取最新技术信息。

    Args:
        query: 搜索关键词，如 "Spring Boot 3 配置文件格式"
    """
    api_key = os.environ.get("SERPAPI_API_KEY", "")
    if not api_key:
        return {
            "action": "web_search",
            "query": query,
            "results": [],
            "error": "未配置 SERPAPI_API_KEY，无法联网搜索",
        }

    try:
        import httpx

        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": 5,
            "hl": "zh-cn",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()

        organic = data.get("organic_results", [])
        results = [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            }
            for item in organic[:5]
        ]

        return {
            "action": "web_search",
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as exc:
        logger.warning("web_search 失败: %s", exc)
        return {
            "action": "web_search",
            "query": query,
            "results": [],
            "error": f"搜索失败: {exc}",
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
